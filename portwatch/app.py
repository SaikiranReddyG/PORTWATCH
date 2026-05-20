"""Textual TUI application for portwatch."""

from __future__ import annotations

import asyncio
import getpass
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional, Sequence

from rich.console import RenderableType
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Input, Static

from . import __version__
from .diff import diff_snapshots
from .loop import SessionStats, _format_summary, _format_change
from .snapshot import PortRecord, take_snapshot


class FilterMode(str, Enum):
    ALL = "ALL"
    LISTEN = "LISTEN"
    ESTABLISHED = "ESTABLISHED"
    SUSPICIOUS = "SUSPICIOUS"

    def next(self) -> "FilterMode":
        order = [FilterMode.ALL, FilterMode.LISTEN, FilterMode.ESTABLISHED, FilterMode.SUSPICIOUS]
        return order[(order.index(self) + 1) % len(order)]


def _record_port(record: PortRecord) -> int:
    return record.socket.local_port


def _record_name(record: PortRecord) -> str:
    if record.process is None:
        return "???"
    return record.process.name or "???"


def _record_matches_filter(record: PortRecord, mode: FilterMode) -> bool:
    if mode is FilterMode.ALL or mode is FilterMode.SUSPICIOUS:
        return True
    if mode is FilterMode.LISTEN:
        return record.socket.state == "LISTEN"
    if mode is FilterMode.ESTABLISHED:
        return record.socket.state == "ESTABLISHED"
    return True


def _record_matches_search(record: PortRecord, query: str) -> bool:
    if not query:
        return True
    query = query.strip().lower()
    if not query:
        return True
    if query in str(record.socket.local_port).lower():
        return True
    if query in _record_name(record).lower():
        return True
    return False


def filter_records(records: Sequence[PortRecord], mode: FilterMode, query: str = "") -> List[PortRecord]:
    return [record for record in records if _record_matches_filter(record, mode) and _record_matches_search(record, query)]


@dataclass
class SlotManager:
    slot_map: Dict[int, int] = field(default_factory=dict)
    slot_expiry: Dict[int, float] = field(default_factory=dict)
    slot_history: Dict[int, int] = field(default_factory=dict)

    def update(self, records: Sequence[PortRecord], slot_count: int, now: Optional[float] = None) -> List[Optional[PortRecord]]:
        now = time.time() if now is None else now
        active_ports = {record.socket.local_port for record in records}

        # Expire stale reservations first.
        for port, expiry in list(self.slot_expiry.items()):
            if expiry <= now:
                self.slot_expiry.pop(port, None)
                self.slot_history.pop(port, None)

        # Record disappearing ports and free their slots for reuse immediately.
        for port, slot in list(self.slot_map.items()):
            if port not in active_ports and port not in self.slot_expiry:
                self.slot_expiry[port] = now + 30.0
                self.slot_history[port] = slot
                self.slot_map.pop(port, None)

        occupied_slots = set(self.slot_map.values())

        # Keep existing active ports in their slots.
        active_by_port = {record.socket.local_port: record for record in records}

        # Assign new ports to the first available slot.
        for port in sorted(active_ports):
            if port in self.slot_map:
                continue
            for slot in range(slot_count):
                if slot not in occupied_slots:
                    self.slot_map[port] = slot
                    occupied_slots.add(slot)
                    break

        slots: List[Optional[PortRecord]] = [None] * slot_count
        for port, slot in self.slot_map.items():
            record = active_by_port.get(port)
            if record is not None and 0 <= slot < slot_count:
                slots[slot] = record
        return slots


def _format_status_line(
    version: str,
    count: int,
    ts: str,
    diff_text: str = "",
    filter_text: str = "",
    message: str = "",
) -> str:
    parts = [f"portwatch v{version}", f"{count} sockets"]
    if diff_text:
        parts.append(diff_text)
    parts.append(f"last update {ts}")
    if filter_text:
        parts.append(filter_text)
    if message:
        parts.append(message)
    parts.append("q to quit")
    return " · ".join(parts)


def _timestr(ts: Optional[float] = None) -> str:
    return time.strftime("%H:%M:%S", time.localtime(time.time() if ts is None else ts))


def _summary_text(stats: SessionStats) -> str:
    return _format_summary(stats)


class ChipDisplay(Static):
    """A static widget that renders the chip diagram."""

    def __init__(self, records: Optional[Sequence[PortRecord]] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._records: List[PortRecord] = list(records or [])
        self._slot_manager = SlotManager()
        self._slots: List[Optional[PortRecord]] = []
        self._render_size = (100, 40)
        self._focus_port: Optional[int] = None
        self._filter_mode = FilterMode.ALL
        self._search_query = ""
        self._detail_port: Optional[int] = None
        self._active_message = ""

    def on_mount(self) -> None:
        self._render_size = (self.app.size.width, self.app.size.height)
        self._refresh()

    def on_resize(self) -> None:
        self._render_size = (self.app.size.width, self.app.size.height)
        self._refresh()

    def set_context(
        self,
        *,
        filter_mode: Optional[FilterMode] = None,
        search_query: Optional[str] = None,
        focus_port: Optional[int] = None,
        detail_port: Optional[int] = None,
        message: str = "",
    ) -> None:
        if filter_mode is not None:
            self._filter_mode = filter_mode
        if search_query is not None:
            self._search_query = search_query
        if focus_port is not None:
            self._focus_port = focus_port
        if detail_port is not None:
            self._detail_port = detail_port
        self._active_message = message
        self._refresh()

    def update_records(self, records: Sequence[PortRecord]) -> None:
        self._records = list(records)
        self._refresh()

    def _refresh(self) -> None:
        width, height = self._render_size
        if width <= 0 or height <= 0:
            return
        visible = filter_records(self._records, self._filter_mode, self._search_query)
        slot_count = max(0, height - 8)
        self._slots = self._slot_manager.update(visible, slot_count, now=time.time())
        if self._focus_port is not None and not any(r is not None and r.socket.local_port == self._focus_port for r in self._slots):
            self._focus_port = self._first_visible_port()
        content = self._render_chip(width, height, visible)
        try:
            self.update(content)
        except Exception:
            # Textual widgets can be exercised in tests without a mounted app.
            self._render_cache = content

    def _first_visible_port(self) -> Optional[int]:
        for record in self._slots:
            if record is not None:
                return record.socket.local_port
        return None

    def _current_focus_index(self) -> int:
        if self._focus_port is None:
            return 0
        for index, record in enumerate(self._slots):
            if record is not None and record.socket.local_port == self._focus_port:
                return index
        return 0

    def move_focus(self, delta: int) -> None:
        occupied = [record.socket.local_port for record in self._slots if record is not None]
        if not occupied:
            self._focus_port = None
            return
        if self._focus_port not in occupied:
            self._focus_port = occupied[0]
            return
        index = occupied.index(self._focus_port)
        self._focus_port = occupied[(index + delta) % len(occupied)]
        self._refresh()

    def jump_column(self, direction: int) -> None:
        # direction: -1 = left, +1 = right
        occupied = [record.socket.local_port for record in self._slots if record is not None]
        if not occupied:
            return
        current = self._current_focus_index()
        half = max(1, len(self._slots) // 2)
        target = current + (half * direction)
        target = max(0, min(len(self._slots) - 1, target))
        if self._slots[target] is not None:
            self._focus_port = self._slots[target].socket.local_port
        else:
            # fall back to nearest occupied slot in the requested column
            if direction > 0:
                for idx in range(target, len(self._slots)):
                    if self._slots[idx] is not None:
                        self._focus_port = self._slots[idx].socket.local_port
                        break
            else:
                for idx in range(target, -1, -1):
                    if self._slots[idx] is not None:
                        self._focus_port = self._slots[idx].socket.local_port
                        break
        self._refresh()

    def current_record(self) -> Optional[PortRecord]:
        if self._focus_port is None:
            return None
        for record in self._slots:
            if record is not None and record.socket.local_port == self._focus_port:
                return record
        return None

    def _render_chip(self, width: int, height: int, visible: Sequence[PortRecord]) -> Text:
        # Keep the body independent from pin drawing, but the render logic lives here
        # because chip.py is locked for this phase.
        total_pin_rows = max(0, height - 8)
        left_rows = (total_pin_rows + 1) // 2
        right_rows = total_pin_rows // 2

        body_width = max(34, min(42, width - 20))
        body_left = max(0, (width - body_width) // 2)
        body_right = body_left + body_width
        body_top = max(0, (height - 10) // 2)

        rows = [" " * width for _ in range(height)]

        listens = sum(1 for record in visible if record.socket.state == "LISTEN")
        established = sum(1 for record in visible if record.socket.state == "ESTABLISHED")
        total = len(visible)
        other = total - listens - established
        user = getpass.getuser()

        bar_width = body_width - 4
        listen_width = _portion(listens, total, bar_width)
        est_width = _portion(established, total, bar_width)
        other_width = max(0, bar_width - listen_width - est_width)
        bar = ("▓" * listen_width) + ("▒" * est_width) + ("░" * other_width)
        bar = bar.ljust(bar_width, "░")

        body_plain_lines = [
            "╔" + "═" * (body_width - 2) + "╗",
            "║" + "portwatch".center(body_width - 2) + "║",
            "║" + " " * (body_width - 2) + "║",
            "║" + f"{listens} LISTEN · {established} ESTABLISHED".center(body_width - 2) + "║",
            "║" + f"{other} other · {total} total".center(body_width - 2) + "║",
            "║" + " " * (body_width - 2) + "║",
            "║" + bar.center(body_width - 2) + "║",
            "║" + " " * (body_width - 2) + "║",
            "║" + f"running as: {user}".ljust(body_width - 2) + "║",
            "╚" + "═" * (body_width - 2) + "╝",
        ]
        for offset, line in enumerate(body_plain_lines):
            row_index = body_top + offset
            if 0 <= row_index < height:
                rows[row_index] = _overlay(rows[row_index], body_left, line)

        slot_count = len(self._slots)
        overflow_count = max(0, len(visible) - slot_count)
        left_visible = min(left_rows, len([record for record in self._slots[:left_rows] if record is not None]))
        right_visible = min(right_rows, len([record for record in self._slots[left_rows:] if record is not None]))
        left_trace_len = max(0, body_left - 10)
        right_trace_len = max(0, width - (body_left + body_width) - 10)
        left_trace = "[bright_black]" + "─" * left_trace_len + "┤[/bright_black]"
        right_trace = "[bright_black]├" + "─" * right_trace_len + "[/bright_black]"

        occupied_slots = [record for record in self._slots if record is not None]
        left_ports = occupied_slots[:left_rows]
        right_ports = occupied_slots[left_rows:left_rows + right_rows]

        for i in range(left_rows):
            row_index = body_top + 1 + i
            if not (0 <= row_index < height):
                continue
            if i < len(left_ports):
                record = left_ports[i]
                is_focus = record.socket.local_port == self._focus_port
                symbol, color = _pin_style(record)
                port = _port_label(record, is_focus)
                pin_plain = f"{port} {symbol}{left_trace_len * '─'}┤"
            elif i == left_rows - 1 and overflow_count > 0:
                pin_plain = f"... +{overflow_count} more"
            else:
                pin_plain = "····"
            rows[row_index] = _overlay_right(rows[row_index], body_left, pin_plain)

        for i in range(right_rows):
            row_index = body_top + 1 + i
            if not (0 <= row_index < height):
                continue
            if i < len(right_ports):
                record = right_ports[i]
                is_focus = record.socket.local_port == self._focus_port
                symbol, color = _pin_style(record)
                port = _port_label(record, is_focus)
                pin_plain = f"├{right_trace_len * '─'} {symbol} {port}"
            elif i == right_rows - 1 and overflow_count > 0:
                pin_plain = f"... +{overflow_count} more"
            else:
                pin_plain = "····"
            rows[row_index] = _overlay(rows[row_index], body_right, pin_plain)

        return Text("\n".join(rows))


def _pin_style(record: PortRecord) -> tuple[str, str]:
    if record.socket.state == "LISTEN":
        return "●", "green" if record.process is not None else "yellow"
    if record.socket.state == "ESTABLISHED":
        return "◐", "cyan"
    return "◯", "bright_black"


def _port_label(record: PortRecord, focused: bool) -> str:
    port = f"{record.socket.local_port:>5}"
    return port


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


class PortwatchApp(App):
    """portwatch TUI — real-time chip view."""

    CSS = """
    Screen {
        background: $surface;
    }

    #chip {
        width: 1fr;
        height: 1fr;
    }

    #status {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
    }

    #detail {
        dock: right;
        width: 42;
        display: none;
        background: $surface;
        color: $text;
        border: solid $accent;
    }

    #search {
        dock: bottom;
        display: none;
        height: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
        Binding("up", "move_up", "Up"),
        Binding("down", "move_down", "Down"),
        Binding("left", "move_left", "Left"),
        Binding("right", "move_right", "Right"),
        Binding("enter", "toggle_detail", "Inspect"),
        Binding("escape", "cancel_or_close", "Close"),
        Binding("/", "search", "Search"),
        Binding("f", "cycle_filter", "Filter"),
        Binding("d", "dismiss", "Dismiss"),
    ]

    def __init__(self, poll_interval: float = 2.0, **kwargs) -> None:
        super().__init__(**kwargs)
        self.poll_interval = poll_interval
        self._stats = SessionStats(start_time=time.time())
        self._previous_snapshot: List[PortRecord] = []
        self._current_snapshot: List[PortRecord] = []
        self._last_diff_text = ""
        self._last_diff_at = 0.0
        self._status_message = ""
        self._search_open = False
        self._search_query = ""
        self._filter_mode = FilterMode.ALL
        self._detail_open = False
        self._poll_in_flight = False

    def compose(self) -> ComposeResult:
        yield ChipDisplay([], id="chip")
        yield Static("", id="detail")
        yield Input(placeholder="Search by port or process", id="search")
        yield Static("", id="status")

    def on_mount(self) -> None:
        search = self.query_one("#search", Input)
        search.display = False
        search.disabled = True
        self.query_one("#detail", Static).display = False
        self._schedule_poll()
        self.set_interval(self.poll_interval, self._schedule_poll)

    def _schedule_poll(self) -> None:
        if self._poll_in_flight:
            return
        self._poll_in_flight = True
        asyncio.create_task(self._poll())

    async def _poll(self) -> None:
        try:
            snapshot = await asyncio.to_thread(take_snapshot)
        except Exception:
            self._stats.parse_error_count += 1
            self._status_message = "poll error"
            self._poll_in_flight = False
            self._refresh_widgets()
            return

        self._current_snapshot = snapshot
        self._stats.snapshot_count += 1
        self._stats.peak_port_count = max(self._stats.peak_port_count, len(snapshot))

        diff = diff_snapshots(self._previous_snapshot, snapshot)
        diff_count = len(diff.added) + len(diff.removed) + len(diff.changed)
        if diff_count:
            self._stats.changes_detected += diff_count
            self._last_diff_text = f"+{len(diff.added)} -{len(diff.removed)} ~{len(diff.changed)}"
            self._last_diff_at = time.time()
        else:
            if time.time() - self._last_diff_at > self.poll_interval:
                self._last_diff_text = ""
        self._previous_snapshot = snapshot
        self._refresh_widgets()
        self._poll_in_flight = False

    def _refresh_widgets(self) -> None:
        chip = self.query_one("#chip", ChipDisplay)
        chip.set_context(
            filter_mode=self._filter_mode,
            search_query=self._search_query,
            focus_port=self._focused_port(),
            detail_port=self._detail_port(),
            message=self._status_message,
        )
        chip.update_records(self._current_snapshot)
        detail = self.query_one("#detail", Static)
        detail.display = self._detail_open
        detail.update(self._detail_renderable())
        status = self.query_one("#status", Static)
        status.update(self._status_text())
        search = self.query_one("#search", Input)
        search.display = self._search_open
        if self._search_open:
            search.disabled = False
            search.focus()
        else:
            search.disabled = True

    def _focused_port(self) -> Optional[int]:
        chip = self.query_one("#chip", ChipDisplay)
        if isinstance(chip.current_record(), PortRecord):
            return chip.current_record().socket.local_port
        return None

    def _detail_port(self) -> Optional[int]:
        if self._detail_open:
            return self._focused_port()
        return None

    def _status_text(self) -> str:
        diff_text = self._last_diff_text if self._last_diff_text and (time.time() - self._last_diff_at) < max(0.1, self.poll_interval * 2) else ""
        filter_text = f"[filter: {self._filter_mode.value}]" if self._filter_mode is not FilterMode.ALL else ""
        message = self._status_message
        return _format_status_line(__version__, len(self._current_snapshot), _timestr(), diff_text, filter_text, message)

    def _detail_renderable(self) -> RenderableType:
        record = self._current_focused_record()
        if record is None:
            return Text("No pin selected")
        s = record.socket
        lines = [
            f"Port {s.local_port} · {s.protocol} · {s.local_ip}",
            f"State: {s.state}",
        ]
        if record.process is None:
            lines.append("Process: ???")
        else:
            p = record.process
            lines.extend([
                f"Process: {p.name} (pid={p.pid})",
                f"Binary: {p.exe}",
                f"Cmdline: {p.cmdline or '—'}",
                f"UID: {p.uid} ({p.username})",
            ])
        remote = f"{s.remote_ip}:{s.remote_port}" if s.remote_port else "—"
        lines.append(f"Remote: {remote}")
        return Text("\n".join(lines))

    def _current_focused_record(self) -> Optional[PortRecord]:
        chip = self.query_one("#chip", ChipDisplay)
        return chip.current_record()

    # Actions
    def action_move_up(self) -> None:
        self.query_one("#chip", ChipDisplay).move_focus(-1)
        self._refresh_widgets()

    def action_move_down(self) -> None:
        self.query_one("#chip", ChipDisplay).move_focus(1)
        self._refresh_widgets()

    def action_move_left(self) -> None:
        self.query_one("#chip", ChipDisplay).jump_column(-1)
        self._refresh_widgets()

    def action_move_right(self) -> None:
        self.query_one("#chip", ChipDisplay).jump_column(1)
        self._refresh_widgets()

    def action_toggle_detail(self) -> None:
        self._detail_open = not self._detail_open
        self._refresh_widgets()

    def action_cycle_filter(self) -> None:
        self._filter_mode = self._filter_mode.next()
        self._status_message = f"[filter: {self._filter_mode.value}]" if self._filter_mode is not FilterMode.ALL else ""
        self._refresh_widgets()

    def action_search(self) -> None:
        self._search_open = True
        self._search_query = ""
        self._refresh_widgets()

    def action_dismiss(self) -> None:
        self._status_message = "no suspicious flags to dismiss"
        self._refresh_widgets()

    def action_cancel_or_close(self) -> None:
        if self._search_open:
            self._search_open = False
            self._search_query = ""
            self._refresh_widgets()
            return
        if self._detail_open:
            self._detail_open = False
            self._refresh_widgets()

    def action_quit(self) -> None:
        self.exit()

    # Input handling
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search":
            self._search_query = event.value
            self._search_open = False
            event.input.disabled = True
            self._refresh_widgets()


def run_tui(poll_interval: float = 2.0) -> None:
    """Entry point called by the CLI."""
    app = PortwatchApp(poll_interval=poll_interval)
    try:
        app.run()
    except KeyboardInterrupt:
        pass
    print(_summary_text(app._stats), flush=True)
