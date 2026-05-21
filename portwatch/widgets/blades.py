"""Blade/rack renderer for portwatch."""

from __future__ import annotations

import getpass
import ipaddress
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from rich.text import Text

from portwatch.snapshot import PortRecord

_LISTEN_SYMBOL = "●"
_ESTABLISHED_SYMBOL = "◉"
_CLOSING_SYMBOL = "◯"

_ESTABLISHED_STATES = {"ESTABLISHED", "SYN_SENT", "SYN_RECV"}
_CLOSING_STATES = {"CLOSING", "CLOSE", "CLOSE_WAIT", "FIN_WAIT1", "FIN_WAIT2", "LAST_ACK", "TIME_WAIT"}
_PRIVATE_IP_RANGES = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
)


def _safe_getuser() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return "unknown"


def _copy_grouped_records(records_by_process: Mapping[str, Sequence[PortRecord]]) -> Dict[str, List[PortRecord]]:
    grouped: Dict[str, List[PortRecord]] = {}
    for name, records in records_by_process.items():
        grouped[name] = list(records)
    return grouped


def _record_rank(record: PortRecord) -> Tuple[int, int, int, str, str, str, int]:
    state_rank = 0 if record.socket.state == "LISTEN" else 1 if record.socket.state in _ESTABLISHED_STATES else 2
    process_rank = 0 if record.process is not None else 1
    remote_rank = 0 if record.socket.remote_port else 1
    return (
        state_rank,
        process_rank,
        remote_rank,
        record.socket.protocol,
        record.socket.local_ip,
        record.socket.remote_ip,
        record.socket.remote_port,
    )


def _bar_segment(count: int, total: int, width: int) -> int:
    if total <= 0 or width <= 0:
        return 0
    return max(0, min(width, round((count / total) * width)))


def _compose_text(lines: Sequence[str], spans: Sequence[Tuple[int, int, int, str]]) -> Text:
    plain = "\n".join(lines)
    text = Text(plain)
    offsets: List[int] = []
    offset = 0
    for line in lines:
        offsets.append(offset)
        offset += len(line) + 1
    for row, col, length, style in spans:
        if row >= len(offsets) or length <= 0:
            continue
        start = offsets[row] + col
        end = min(len(plain), start + length)
        if start < end:
            text.stylize(style, start, end)
    return text


def _port_color(port: int) -> str:
    if port <= 1023:
        return "bright_white"
    if port <= 49151:
        return "yellow"
    return "bright_cyan"


def _remote_color(ip: str) -> str:
    try:
        parsed = ipaddress.ip_address(ip)
    except ValueError:
        return "cyan"
    if parsed.is_private:
        return "magenta"
    return "cyan"


def _status_color(status: str) -> str:
    return {
        "RUN": "green",
        "BUSY": "yellow",
        "WARN": "red",
        "DEAD": "bright_black",
    }.get(status, "bright_black")


def _is_public_ip(ip: str) -> bool:
    try:
        parsed = ipaddress.ip_address(ip)
    except ValueError:
        return True
    return not parsed.is_private


def _truncate_remote_ip(ip: str) -> str:
    parts = ip.split(".")
    if len(parts) <= 3:
        return ip
    return ".".join(parts[:3])


def _state_symbol(record: PortRecord) -> str:
    if record.socket.state == "LISTEN":
        return _LISTEN_SYMBOL
    if record.socket.state in _ESTABLISHED_STATES:
        return _ESTABLISHED_SYMBOL
    return _CLOSING_SYMBOL


def _row_records(records: Sequence[PortRecord], per_row: int) -> List[List[PortRecord]]:
    if per_row <= 0:
        return []
    rows: List[List[PortRecord]] = []
    for index in range(0, len(records), per_row):
        rows.append(list(records[index : index + per_row]))
    return rows


def _established_remote_text(record: PortRecord, cell_width: int) -> str:
    remote_ip = record.socket.remote_ip
    remote_port = f":{record.socket.remote_port}" if record.socket.remote_port else ""
    candidate = f"{remote_ip}{remote_port}"
    max_remote_width = max(4, cell_width - 10)
    if len(candidate) <= max_remote_width:
        return candidate
    truncated_ip = _truncate_remote_ip(remote_ip)
    candidate = f"{truncated_ip}{remote_port}"
    if len(candidate) <= max_remote_width:
        return candidate
    return f"{truncated_ip[:max(1, max_remote_width - len(remote_port) - 1)]}…{remote_port}"[:max_remote_width]


def _render_cell(record: PortRecord, cell_width: int, established: bool) -> Tuple[str, List[Tuple[int, int, int, str]]]:
    symbol = _state_symbol(record)
    port_text = f"{record.socket.local_port:>5}"
    if established:
        remote = _established_remote_text(record, cell_width)
        text = f"{symbol} {port_text} → {remote}"
        remote_start = 10
        spans = [
            (2, 5, _port_color(record.socket.local_port)),
            (8, 1, "bright_black"),
            (remote_start, len(remote), _remote_color(record.socket.remote_ip)),
        ]
    else:
        text = f"{symbol} {port_text}"
        spans = [(2, 5, _port_color(record.socket.local_port))]
    return text[:cell_width].ljust(cell_width), spans


def _wrap_fixed_cells(records: Sequence[PortRecord], per_row: int, cell_width: int, established: bool) -> List[Tuple[str, List[Tuple[int, int, int, str]]]]:
    if per_row <= 0:
        return []
    rows: List[Tuple[str, List[Tuple[int, int, int, str]]]] = []
    for row_records in _row_records(records, per_row):
        cell_texts: List[str] = []
        spans: List[Tuple[int, int, int, str]] = []
        cursor = 0
        for index, record in enumerate(row_records):
            cell_text, cell_spans = _render_cell(record, cell_width, established)
            cell_texts.append(cell_text)
            for col, length, style in cell_spans:
                spans.append((cursor + col, length, style))
            cursor += len(cell_text)
            if index != len(row_records) - 1:
                cursor += 1
        rows.append((" ".join(cell_texts), spans))
    return rows


def _fit_between(left: str, right: str, width: int, fill: str = " ") -> str:
    if width <= 0:
        return ""
    left = left[:width]
    right = right[:width]
    remaining = width - len(left) - len(right)
    if remaining < 1:
        merged = (left + " " + right).strip()
        return merged[:width].ljust(width, fill)
    return f"{left}{fill * remaining}{right}"


def _header_line(width: int, count: int) -> str:
    if width <= 0:
        return ""
    middle = f" {count} sockets "
    body = _fit_between(" portwatch ", middle, max(0, width - 2), fill="─")
    return f"┌{body}┐"[:width].ljust(width)


def _title_line(name: str, status: str, width: int) -> str:
    if width <= 0:
        return ""
    tag = f"[{status}]"
    name = name.upper().strip() or "???"
    prefix = f"┌── {name} "
    suffix = f" {tag} ──┐"
    if len(prefix) + len(suffix) >= width:
        available = max(1, width - len(suffix) - len("┌──  "))
        name = name[:available]
        prefix = f"┌── {name} "
    fill = max(2, width - len(prefix) - len(suffix))
    return (f"{prefix}{'─' * fill}{suffix}")[:width].ljust(width)


def _bottom_line(width: int) -> str:
    if width <= 0:
        return ""
    return f"└{'─' * max(0, width - 2)}┘"[:width].ljust(width)


def _group_status(name: str, records: Sequence[PortRecord]) -> str:
    if not records:
        return "DEAD"
    if name.startswith("???") or all(record.process is None for record in records):
        return "WARN"
    states = {record.socket.state for record in records}
    if states and states <= _CLOSING_STATES:
        return "DEAD"
    if "LISTEN" in states:
        return "RUN"
    if states & _ESTABLISHED_STATES:
        return "BUSY"
    return "WARN"


def _group_sort_key(item: Tuple[str, Sequence[PortRecord]]) -> Tuple[int, str]:
    name, records = item
    status = _group_status(name, records)
    rank = {"RUN": 0, "BUSY": 1, "WARN": 2, "DEAD": 3}.get(status, 4)
    return rank, name.lower()


def _dedupe_port_records(records: Sequence[PortRecord]) -> List[PortRecord]:
    best_by_port: Dict[int, PortRecord] = {}
    for record in records:
        port = record.socket.local_port
        current = best_by_port.get(port)
        if current is None or _record_rank(record) < _record_rank(current):
            best_by_port[port] = record
    return sorted(best_by_port.values(), key=lambda record: (record.socket.local_port, _record_rank(record)))


class BladesWidget:
    """Build a Rich Text renderable for the blade/rack layout."""

    def __init__(self, records_by_process: Optional[Mapping[str, Sequence[PortRecord]]] = None) -> None:
        self.records_by_process = _copy_grouped_records(records_by_process or {})

    def update_records(self, records_by_process: Mapping[str, Sequence[PortRecord]]) -> None:
        self.records_by_process = _copy_grouped_records(records_by_process)

    def render(self, width: int = 100, height: int = 40) -> Text:
        if width < 60 or height < 18:
            msg = "portwatch needs at least 60×18"
            return Text(msg.center(max(1, width)))

        grouped_items = sorted(self.records_by_process.items(), key=_group_sort_key)
        flat_records = [record for _, records in grouped_items for record in records]
        if not flat_records:
            return self._loading_screen(width, height)

        inner_width = max(0, width - 2)
        card_width = max(0, inner_width - 2)
        cell_width = 26

        listens = [record for record in flat_records if record.socket.state == "LISTEN"]
        closings = [record for record in flat_records if record.socket.state in _CLOSING_STATES]
        established = [record for record in flat_records if record.socket.state in _ESTABLISHED_STATES]
        n_listen = len(listens) + len(closings)
        n_established = len(established)
        n_other = len(flat_records) - n_listen - n_established

        bar_width = max(8, min(card_width - 14, inner_width - 22))
        listen_width = _bar_segment(n_listen, len(flat_records), bar_width)
        est_width = _bar_segment(n_established, len(flat_records), bar_width)
        other_width = max(0, bar_width - listen_width - est_width)
        bar = "█" * listen_width + "▒" * est_width + "░" * other_width
        summary_line = "│" + _fit_between(bar.ljust(bar_width, "░"), f"{n_listen} LISTEN  {n_established} EST  {n_other} OTHER", inner_width - 2) + "│"

        lines: List[str] = [_header_line(width, len(flat_records)), summary_line[:width].ljust(width), "├" + "─" * inner_width + "┤"]
        spans: List[Tuple[int, int, int, str]] = []
        if listen_width:
            spans.append((1, 1, listen_width, "green"))
        if est_width:
            spans.append((1, 1 + listen_width, est_width, "cyan"))
        if other_width:
            spans.append((1, 1 + listen_width + est_width, other_width, "bright_black"))

        unused_rows = max(0, height - len(lines) - 1)
        for index, (name, records) in enumerate(grouped_items):
            if unused_rows <= 0:
                break
            blade_lines, blade_spans = self._render_blade(name, records, card_width, cell_width)
            base_row = len(lines)
            for blade_line in blade_lines:
                if unused_rows <= 0:
                    break
                lines.append(blade_line[:width].ljust(width))
                unused_rows -= 1
            for row_offset, col, length, style in blade_spans:
                spans.append((base_row + row_offset, col, length, style))
            if unused_rows > 0 and index != len(grouped_items) - 1:
                lines.append(self._dot_line(width))
                spans.append((len(lines) - 1, 0, width, "bright_black"))
                unused_rows -= 1

        while unused_rows > 0:
            lines.append(self._dot_line(width))
            spans.append((len(lines) - 1, 0, width, "bright_black"))
            unused_rows -= 1

        lines.append("└" + "─" * inner_width + "┘")
        return _compose_text(lines[:height], spans)

    def _render_blade(self, name: str, records: Sequence[PortRecord], width: int, cell_width: int) -> Tuple[List[str], List[Tuple[int, int, int, str]]]:
        status = _group_status(name, records)
        sorted_records = _dedupe_port_records(records)
        listen_records = [record for record in sorted_records if record.socket.state == "LISTEN" or record.socket.state in _CLOSING_STATES]
        established_records = [record for record in sorted_records if record.socket.state in _ESTABLISHED_STATES]

        listen_rows = _wrap_fixed_cells(listen_records, 5, cell_width, established=False)
        established_rows = _wrap_fixed_cells(established_records, 3, cell_width, established=True)

        lines: List[str] = [_title_line(name, status, width)]
        spans: List[Tuple[int, int, int, str]] = []
        tag_start = lines[0].find(f"[{status}]")
        if tag_start >= 0:
            spans.append((0, tag_start, len(f"[{status}]"), _status_color(status)))
        for row, row_spans in listen_rows:
            rendered_row = self._render_grid_row(row, width)
            row_index = len(lines)
            lines.append(rendered_row)
            for col, length, style in row_spans:
                spans.append((row_index, 2 + col, length, style))
        for row, row_spans in established_rows:
            rendered_row = self._render_grid_row(row, width)
            row_index = len(lines)
            lines.append(rendered_row)
            for col, length, style in row_spans:
                spans.append((row_index, 2 + col, length, style))

        summary = f"{len(listen_records)} listening · active conns: {len(established_records)}"
        lines.append(self._summary_line(summary, width))
        lines.append(_bottom_line(width))
        return lines, spans

    def _render_grid_row(self, row: str, width: int) -> str:
        return f"│ {row[: max(0, width - 4)].ljust(max(0, width - 4))} │"[:width].ljust(width)

    def _summary_line(self, summary: str, width: int) -> str:
        return f"│ {summary[: max(0, width - 4)].ljust(max(0, width - 4))} │"[:width].ljust(width)

    def _dot_line(self, width: int) -> str:
        return "·" * width

    def _loading_screen(self, width: int, height: int) -> Text:
        lines: List[str] = []
        for row in range(height):
            if row == height // 2:
                lines.append("LOADING".center(width))
            elif row == height // 2 + 1:
                lines.append("····".center(width))
            else:
                lines.append(self._dot_line(width))
        return Text("\n".join(lines), style="bright_black")