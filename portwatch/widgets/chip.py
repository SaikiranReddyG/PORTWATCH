from __future__ import annotations

import getpass
from typing import List, Tuple

from rich.console import RenderableType
from rich.text import Text

from portwatch.snapshot import PortRecord


class ChipWidget:
    """Render the portwatch chip as a fixed-width set of terminal rows."""

    def __init__(self, records: List[PortRecord]):
        self.records = records or []

    def render(self, width: int = 80, height: int = 24) -> RenderableType:
        if not self.records:
            return Text.from_markup("\n".join(["LOADING"] + [""] * max(0, height - 1)))

        body_inner_height = 9
        body_total_height = body_inner_height + 2

        available_pin_rows = max(0, height - 6)
        pin_rows = min(body_inner_height, available_pin_rows)
        left_rows = pin_rows // 2 + (pin_rows % 2)
        right_rows = pin_rows // 2

        sorted_records = sorted(self.records, key=lambda record: record.socket.local_port)
        
        max_slots = left_rows + right_rows
        if len(sorted_records) > max_slots:
            display_total = max_slots - 1
        else:
            display_total = len(sorted_records)
            
        visible = sorted_records[:display_total]
        left_ports = visible[:left_rows]
        right_ports = visible[left_rows:]
        overflow_count = len(sorted_records) - display_total

        body_width = 36 if width >= 36 else max(20, width - 4)
        body_left = max(0, (width - body_width) // 2)
        body_right = body_left + body_width
        body_top = max(0, (height - body_total_height) // 2)

        rows = [" " * width for _ in range(height)]

        listens = sum(1 for record in self.records if record.socket.state == "LISTEN")
        established = sum(1 for record in self.records if record.socket.state == "ESTABLISHED")
        other = len(self.records) - listens - established
        total = len(self.records)
        user = getpass.getuser()

        bar_width = body_width - 4
        listen_width = _portion(listens, total, bar_width)
        est_width = _portion(established, total, bar_width)
        other_width = max(0, bar_width - listen_width - est_width)
        bar = ("▓" * listen_width) + ("▒" * est_width) + ("░" * other_width)
        bar = bar.ljust(bar_width, "░")

        body_lines = [
            "╔" + "═" * (body_width - 2) + "╗",
            "║" + "portwatch".center(body_width - 2) + "║",
            "║" + "".center(body_width - 2) + "║",
            "║" + f"{listens} LISTEN · {established} EST".center(body_width - 2) + "║",
            "║" + f"{other} other · {total} total".center(body_width - 2) + "║",
            "║" + "".center(body_width - 2) + "║",
            "║" + bar.center(body_width - 2) + "║",
            "║" + "".center(body_width - 2) + "║",
            "║" + "".center(body_width - 2) + "║",
            "║" + f"running as: {user}".ljust(body_width - 2) + "║",
            "╚" + "═" * (body_width - 2) + "╝",
        ]

        for offset, line in enumerate(body_lines):
            row_index = body_top + offset
            if 0 <= row_index < height:
                rows[row_index] = _overlay(rows[row_index], body_left, line)

        left_trace_width = max(0, body_left - 8 - 1)
        left_trace = "─" * left_trace_width
        right_trace_width = max(0, width - body_right - 8 - 1)
        right_trace = "─" * right_trace_width

        for i in range(min(left_rows, body_inner_height)):
            row_index = body_top + 1 + i
            if not (0 <= row_index < height):
                continue
            if i < len(left_ports):
                record = left_ports[i]
                plain, styled = _left_pin(record, left_trace)
                row = _overlay_right(rows[row_index], body_left, plain)
                rows[row_index] = row.replace(plain, styled, 1)

        for i in range(min(right_rows, body_inner_height)):
            row_index = body_top + 1 + i
            if not (0 <= row_index < height):
                continue
            if overflow_count > 0 and i == right_rows - 1:
                overflow_text = f"+{overflow_count} more"
                rows[row_index] = _overlay(rows[row_index], body_right, overflow_text)
                continue
            if i < len(right_ports):
                record = right_ports[i]
                plain, styled = _right_pin(record, right_trace)
                row = _overlay(rows[row_index], body_right, plain)
                rows[row_index] = row.replace(plain, styled, 1)

        return Text.from_markup("\n".join(rows))


def _portion(count: int, total: int, width: int) -> int:
    if total <= 0 or width <= 0:
        return 0
    return min(width, round((count / total) * width))


def _overlay(row: str, start: int, text: str) -> str:
    if start >= len(row):
        return row
    end = min(len(row), start + len(text))
    return row[:start] + text[: end - start] + row[end:]


def _overlay_right(row: str, end: int, text: str) -> str:
    start = max(0, end - len(text))
    return _overlay(row, start, text)


def _symbol_for(record: PortRecord) -> Tuple[str, str]:
    state = record.socket.state
    if state == "LISTEN":
        return "●", "green" if record.process is not None else "yellow"
    if state == "ESTABLISHED":
        return "◐", "cyan"
    return "◯", "grey39"


def _left_pin(record: PortRecord, trace: str) -> Tuple[str, str]:
    symbol, color = _symbol_for(record)
    port = f"{record.socket.local_port:>5}"
    plain = f"{port} {symbol}{trace}┤"
    styled = f"{port} [{color}]{symbol}[/]{trace}┤"
    return plain, styled


def _right_pin(record: PortRecord, trace: str) -> Tuple[str, str]:
    symbol, color = _symbol_for(record)
    port = f"{record.socket.local_port:>5}"
    plain = f"├{trace}{symbol} {port}"
    styled = f"├{trace}[{color}]{symbol}[/] {port}"
    return plain, styled
