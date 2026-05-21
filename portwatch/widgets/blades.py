"""Blade/rack renderer for portwatch."""

from __future__ import annotations

import getpass
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from rich.text import Text

from portwatch.snapshot import PortRecord

_LISTEN_SYMBOL = "●"
_ACTIVE_SYMBOL = "◐"
_IDLE_SYMBOL = "◯"

_ACTIVE_STATES = {"ESTABLISHED", "SYN_SENT", "SYN_RECV"}
_DEAD_STATES = {"CLOSE", "CLOSING", "CLOSE_WAIT", "FIN_WAIT1", "FIN_WAIT2", "LAST_ACK", "TIME_WAIT"}


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


def _record_symbol(record: PortRecord) -> str:
    if record.socket.state == "LISTEN":
        return _LISTEN_SYMBOL
    if record.socket.state in _ACTIVE_STATES:
        return _ACTIVE_SYMBOL
    return _IDLE_SYMBOL


def _record_token(record: PortRecord) -> str:
    port = str(record.socket.local_port)
    symbol = _record_symbol(record)
    if record.socket.state in _ACTIVE_STATES and record.socket.remote_ip not in {"0.0.0.0", "::", ""}:
        remote = record.socket.remote_ip
        if record.socket.remote_port:
            remote = f"{remote}:{record.socket.remote_port}"
        return f"{symbol} {port} → {remote}"
    return f"{symbol} {port}"


def _wrap_tokens(tokens: Sequence[str], width: int) -> List[str]:
    if width <= 0:
        return [""]
    lines: List[str] = []
    current = ""
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        if len(token) > width:
            token = token[: max(0, width - 1)] + "…"
        candidate = token if not current else f"{current}  {token}"
        if len(candidate) <= width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = token
    if current:
        lines.append(current)
    return lines or [""]


def _limit_lines(tokens: Sequence[str], width: int, max_lines: int) -> List[str]:
    wrapped = _wrap_tokens(tokens, width)
    if max_lines <= 0:
        return []
    if len(wrapped) <= max_lines:
        return wrapped
    kept = wrapped[:max_lines]
    overflow = len(wrapped) - max_lines
    kept[-1] = f"{kept[-1]}  … +{overflow} more"[:width]
    return kept


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
    if states and states <= _DEAD_STATES:
        return "DEAD"
    if "LISTEN" in states:
        return "RUN"
    if states & _ACTIVE_STATES:
        return "BUSY"
    return "WARN"


def _group_sort_key(item: Tuple[str, Sequence[PortRecord]]) -> Tuple[int, str]:
    name, records = item
    status = _group_status(name, records)
    rank = {"RUN": 0, "BUSY": 1, "WARN": 2, "DEAD": 3}.get(status, 4)
    return rank, name.lower()


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
        content_width = max(0, inner_width - 2)

        n_listen = sum(1 for record in flat_records if record.socket.state == "LISTEN")
        n_est = sum(1 for record in flat_records if record.socket.state in _ACTIVE_STATES)
        n_other = len(flat_records) - n_listen - n_est
        user = _safe_getuser()

        bar_width = max(8, min(content_width - 14, inner_width - 22))
        listen_width = _bar_segment(n_listen, len(flat_records), bar_width)
        est_width = _bar_segment(n_est, len(flat_records), bar_width)
        other_width = max(0, bar_width - listen_width - est_width)
        bar = "█" * listen_width + "▒" * est_width + "░" * other_width
        summary_line = "│" + _fit_between(bar.ljust(bar_width, "░"), f"{n_listen} LISTEN  {n_est} EST  {n_other} OTHER", inner_width - 2) + "│"

        title = f"┌─ portwatch ──────────────────────────────────── {len(flat_records)} sockets ┐"
        title = title[:width].ljust(width)
        lines: List[str] = [title, summary_line[:width].ljust(width), "├" + "─" * inner_width + "┤"]
        spans: List[Tuple[int, int, int, str]] = []
        if listen_width:
            spans.append((1, 1, listen_width, "green"))
        if est_width:
            spans.append((1, 1 + listen_width, est_width, "cyan"))
        if other_width:
            spans.append((1, 1 + listen_width + est_width, other_width, "bright_black"))

        remaining_lines = max(0, height - len(lines) - 1)
        for index, (name, records) in enumerate(grouped_items):
            if remaining_lines <= 0:
                break
            groups_left = len(grouped_items) - index
            max_content_lines = max(1, min(4, remaining_lines - (groups_left - 1) * 2 - 2))
            card = self._render_card(name, records, width, max_content_lines)
            if len(card) > remaining_lines:
                card = card[:remaining_lines]
            lines.extend(card)
            remaining_lines -= len(card)
            if remaining_lines > 0 and index != len(grouped_items) - 1:
                lines.append(" " * width)
                remaining_lines -= 1

        while remaining_lines > 0:
            lines.append(" " * width)
            remaining_lines -= 1

        lines.append("└" + "─" * inner_width + "┘")
        return _compose_text(lines[:height], spans)

    def _render_card(self, name: str, records: Sequence[PortRecord], width: int, max_content_lines: int) -> List[str]:
        status = _group_status(name, records)
        sorted_records = sorted(records, key=lambda record: (record.socket.local_port, record.socket.state, record.socket.remote_ip, record.socket.remote_port))
        listen_count = sum(1 for record in sorted_records if record.socket.state == "LISTEN")
        active_count = sum(1 for record in sorted_records if record.socket.state in _ACTIVE_STATES)

        tokens = [_record_token(record) for record in sorted_records]
        if listen_count:
            tokens.append(f"{listen_count} listening")
        if active_count:
            tokens.append(f"active conns: {active_count}")
        if all(record.process is None for record in sorted_records):
            tokens.append("unresolved")

        content_lines = _limit_lines(tokens, width - 4 if width >= 4 else width, max_content_lines)
        while len(content_lines) < max_content_lines:
            content_lines.append("")

        lines = [_title_line(name, status, width)]
        for line in content_lines[:max_content_lines]:
            line = line[: max(0, width - 4)]
            lines.append(f"│ {line.ljust(max(0, width - 4))} │"[:width].ljust(width))
        lines.append(_bottom_line(width))
        return lines

    def _loading_screen(self, width: int, height: int) -> Text:
        lines: List[str] = []
        for row in range(height):
            if row == height // 2:
                lines.append("LOADING".center(width))
            elif row == height // 2 + 1:
                lines.append("····".center(width))
            else:
                lines.append(" " * width)
        return Text("\n".join(lines), style="bright_black")