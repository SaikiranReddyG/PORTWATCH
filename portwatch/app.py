import time
from typing import List

from .snapshot import take_snapshot
from .widgets.chip import ChipWidget


def _format_status_line(version: str, count: int, timestr: str) -> str:
    return f"portwatch v{version} · {count} sockets · snapshot taken at {timestr} · q to quit"


def run_tui():
    try:
        from textual.app import App
        from textual.widgets import Static
        from textual.reactive import Reactive
        from textual import events
    except Exception as e:
        raise RuntimeError("Textual is required for the TUI. Install with 'pip install textual'.") from e

    class PortwatchApp(App):
        async def on_mount(self) -> None:
            # show loading then snapshot
            snapshot = take_snapshot()
            chip = ChipWidget(snapshot)
            self.body = Static(chip.render())
            await self.view.dock(self.body, edge="top")
            # status
            ts = time.strftime("%H:%M:%S")
            status = _format_status_line("0.0.1", len(snapshot), ts)
            self.footer = Static(status)
            await self.view.dock(self.footer, edge="bottom", size=1)

        async def on_key(self, event: events.Key) -> None:
            if event.key == "q" or (event.key == "c" and event.ctrl):
                await self.action_quit()

    # Create and run an instance. Some Textual versions expose `run` as an
    # instance method rather than a classmethod — instantiate to be safe.
    app = PortwatchApp()
    app.run()
