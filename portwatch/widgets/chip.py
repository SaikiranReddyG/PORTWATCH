from typing import List
from rich.text import Text
from rich.console import RenderableType
from portwatch.snapshot import PortRecord


class ChipWidget:
    """A simple, renderable chip-like widget using Rich.

    This class is intentionally *not* a Textual widget so tests can call
    `render()` without needing Textual installed. The Textual app will use
    this class as a renderable for display.
    """

    def __init__(self, records: List[PortRecord]):
        self.records = records or []

    def render(self, width: int = 80, height: int = 24) -> RenderableType:
        # Minimum layout: show loading when no records
        if not self.records:
            t = Text()
            t.append("LOADING\n", style="bold")
            t.append("\n" * (height - 2))
            return t

        # Build simple textual chip: left and right pins and center box
        ports = sorted({r.local_port: r for r in self.records}.items(), key=lambda x: x[0])
        ports = [p for _, p in ports]
        half = (len(ports) + 1) // 2
        left = ports[:half]
        right = ports[half:]

        lines = []
        # compute chip width
        chip_w = min(40, max(20, width - 20))
        top = " " * 14 + "┌" + "─" * chip_w + "┐"
        bottom = " " * 14 + "└" + "─" * chip_w + "┘"
        lines.append(top)

        # body lines: show title and counts
        listens = sum(1 for r in self.records if r.state == "LISTEN")
        est = sum(1 for r in self.records if r.state == "ESTABLISHED")
        other = len(self.records) - listens - est
        total = len(self.records)

        body = []
        body.append("")
        body.append(f"  ╔{"═" * ((chip_w - 2)//1)}╗")
        body.append(f"  ║{'portwatch'.center(chip_w - 2)}║")
        body.append(f"  ║{' '.center(chip_w - 2)}║")
        counts = f"{listens} LISTEN · {est} ESTABLISHED · {other} other · {total} total"
        body.append(f"  ║{counts.center(chip_w - 2)}║")
        body.append(f"  ║{' '.center(chip_w - 2)}║")
        body.append(f"  ╚{"═" * ((chip_w - 2)//1)}╝")

        # assemble lines with pins
        max_lines = max(len(left), len(right), len(body))
        for i in range(max_lines):
            left_part = ""
            if i < len(left):
                r = left[i]
                symbol = _symbol_for(r)
                left_part = f"{str(r.local_port).rjust(5)} {symbol} ──────┤"
            else:
                left_part = "".ljust(14)

            body_part = body[i] if i < len(body) else "  ║" + " " * (chip_w - 2) + "║"

            right_part = ""
            if i < len(right):
                r = right[i]
                symbol = _symbol_for(r)
                right_part = f"├────── {symbol} {str(r.local_port).ljust(5)}"

            lines.append(left_part + body_part + right_part)

        lines.append(bottom)

        t = Text()
        for ln in lines:
            t.append(ln + "\n")
        return t


def _symbol_for(record: PortRecord) -> str:
    st = record.state
    if st == "LISTEN":
        if record.process is None or record.process.name == "???":
            return "●"  # yellow in real app
        return "●"
    if st == "ESTABLISHED":
        return "◐"
    return "◯"
