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


def _bar_segment(count: int, total: int, width: int) -> int:
    if total <= 0 or width <= 0:
        return 0
    return max(0, min(width, round((count / total) * width)))


def _copy_grouped_records(records_by_process: Mapping[str, Sequence[PortRecord]]) -> Dict[str, List[PortRecord]]:
    grouped: Dict[str, List[PortRecord]] = {}
    for name, records in records_by_process.items():
        grouped[name] = list(records)
    return grouped


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
        return f"{symbol} {port}→{remote}"
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


def _frame_line(content: str, width: int) -> str:
    if width <= 0:
        return ""
    return f"│{content.ljust(width)}│"


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
    line = f"{prefix}{'─' * fill}{suffix}"
    return line[:width].ljust(width)


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
    if "LISTEN" in states:
        return "RUN"
    if states & _ACTIVE_STATES:
        return "BUSY"
    if states and states <= _DEAD_STATES:
        return "DEAD"
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
        content_width = max(0, inner_width - 4)

        n_listen = sum(1 for record in flat_records if record.socket.state == "LISTEN")
        n_est = sum(1 for record in flat_records if record.socket.state in _ACTIVE_STATES)
        n_other = len(flat_records) - n_listen - n_est
        user = _safe_getuser()

        bar_width = max(8, content_width - 18)
        listen_width = _bar_segment(n_listen, len(flat_records), bar_width)
        est_width = _bar_segment(n_est, len(flat_records), bar_width)
        other_width = max(0, bar_width - listen_width - est_width)
        bar = "█" * listen_width + "▒" * est_width + "░" * other_width
        summary_line = _fit_between(
            bar.ljust(bar_width, "░"),
            f"{n_listen} LISTEN  {n_est} EST  {n_other} OTHER",
            inner_width,
        )

        body: List[str] = []
        body.append(_fit_between(" portwatch ", f"{len(flat_records)} sockets ", inner_width, fill="─"))
        body.append(summary_line)
        body.append("─" * inner_width)

        remaining_groups = len(grouped_items)
        for index, (name, records) in enumerate(grouped_items):
            if remaining_groups <= 0:
                break
            remaining_groups -= 1
            card = self._render_card(name, records, inner_width)
            needed = len(card) + (1 if body else 0)
            if len(body) + needed > max(0, height - 2):
                if len(body) < max(0, height - 3):
                    body.append(_frame_line(f"… +{remaining_groups + 1} groups more".ljust(content_width), inner_width))
                break
            if body and body[-1].strip():
                body.append(" " * inner_width)
            body.extend(card)

        if len(body) < max(0, height - 2):
            body.append(_frame_line(f" running as: {user}".ljust(content_width), inner_width))

        while len(body) < max(0, height - 2):
            body.append(" " * inner_width)

        body = body[: max(0, height - 2)]
        lines = ["┌" + "─" * inner_width + "┐"]
        lines.extend(_frame_line(line, inner_width) if line.strip() else _frame_line("".ljust(inner_width), inner_width) for line in body)
        lines.append("└" + "─" * inner_width + "┘")
        return Text("\n".join(lines))

    def _render_card(self, name: str, records: Sequence[PortRecord], width: int) -> List[str]:
        status = _group_status(name, records)
        sorted_records = sorted(records, key=lambda record: (record.socket.local_port, record.socket.state))
        listen_count = sum(1 for record in sorted_records if record.socket.state == "LISTEN")
        active_count = sum(1 for record in sorted_records if record.socket.state in _ACTIVE_STATES)

        tokens = [_record_token(record) for record in sorted_records]
        if listen_count:
            tokens.append(f"{listen_count} listening")
        if active_count:
            tokens.append(f"active conns: {active_count}")
        if all(record.process is None for record in sorted_records):
            tokens.append("unresolved")

        text_width = max(0, width - 4)
        content_lines = _wrap_tokens(tokens, text_width)
        if len(content_lines) > 2:
            overflow = len(content_lines) - 2
            content_lines = content_lines[:2]
            content_lines[-1] = f"{content_lines[-1]}  … +{overflow} more"[:text_width]

        lines = [_title_line(name, status, width)]
        for line in content_lines:
            lines.append(f"│ {line.ljust(text_width)} │"[:width].ljust(width))
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