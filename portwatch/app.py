"""Textual TUI application for portwatch."""

from __future__ import annotations

import time

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Static

from .snapshot import take_snapshot, PortRecord
from .widgets.chip import ChipWidget
from . import __version__


class ChipDisplay(Static):
    """A static widget that renders the chip diagram."""

    def __init__(self, records: list[PortRecord], **kwargs) -> None:
        super().__init__(**kwargs)
        self._records = records

    def on_mount(self) -> None:
        size = self.app.size
        chip = ChipWidget(self._records)
        content = chip.render(width=size.width, height=size.height - 1)
        self.update(content)

    def on_resize(self) -> None:
        size = self.app.size
        chip = ChipWidget(self._records)
        content = chip.render(width=size.width, height=size.height - 1)
        self.update(content)


class PortwatchApp(App):
    """portwatch TUI — microcontroller chip view."""

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
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
    ]

def _format_status_line(version, count, ts):
    return f"portwatch v{version} · {count} sockets · snapshot taken at {ts} · q to quit"

    def compose(self) -> ComposeResult:
        snapshot = take_snapshot()
        self._snapshot = snapshot
        yield ChipDisplay(snapshot, id="chip")
        ts = time.strftime("%H:%M:%S")
        status = _format_status_line(__version__, len(snapshot), ts)
        yield Static(status, id="status")


def run_tui() -> None:
    """Entry point called by the CLI."""
    app = PortwatchApp()
    app.run()