"""Microcontroller-style chip widget for portwatch.

Renders a DIP (Dual Inline Package) diagram where each pin represents
an active port.  The layout is computed with exact character positions
so traces align perfectly regardless of terminal width.
"""

from __future__ import annotations

import getpass
from typing import List, Optional, Tuple

from rich.text import Text

from portwatch.snapshot import PortRecord

# ── symbol table (load-bearing: meaning is clear without color) ──────
_SYMBOLS = {
    "LISTEN":      "●",
    "ESTABLISHED": "◐",
    "SYN_SENT":    "◐",
    "SYN_RECV":    "◐",
    "TIME_WAIT":   "◯",
    "CLOSE_WAIT":  "◯",
    "FIN_WAIT1":   "◯",
    "FIN_WAIT2":   "◯",
    "CLOSE":       "◯",
    "LAST_ACK":    "◯",
    "CLOSING":     "◯",
}
_DEFAULT_SYMBOL = "◯"

# ── color palette (matches pulse-platform) ───────────────────────────
_COLORS = {
    "listen_known":   "green",
    "listen_unknown": "yellow",
    "established":    "cyan",
    "closing":        "bright_black",
    "trace":          "bright_black",
    "chip_border":    "white",
    "outer_frame":    "bright_black",
    "body_text":      "white",
    "body_dim":       "bright_black",
    "port_label":     "bright_white",
    "status":         "bright_black",
    "bar_listen":     "green",
    "bar_est":        "cyan",
    "bar_other":      "bright_black",
}


def _sym(record: PortRecord) -> str:
    return _SYMBOLS.get(record.state, _DEFAULT_SYMBOL)


def _color(record: PortRecord) -> str:
    st = record.state
    if st == "LISTEN":
        return _COLORS["listen_known"] if record.process else _COLORS["listen_unknown"]
    if st in ("ESTABLISHED", "SYN_SENT", "SYN_RECV"):
        return _COLORS["established"]
    return _COLORS["closing"]


class ChipWidget:
    """Build a Rich Text renderable of the chip diagram."""

    def __init__(self, records: List[PortRecord]) -> None:
        self.records = records or []

    # ── public API ───────────────────────────────────────────────────
    def render(self, width: int = 100, height: int = 40) -> Text:
        if width < 80 or height < 24:
            msg = "portwatch needs at least 80×24"
            return Text(msg.center(width))

        if not self.records:
            return self._loading_screen(width, height)

        # ── data prep ────────────────────────────────────────────────
        # Dedup by port number — on a chip, each pin is one port.
        # When multiple sockets share a port (e.g. 0.0.0.0:53 and
        # 127.0.0.1:53), keep the most "interesting" one: prefer
        # LISTEN, then ESTABLISHED, then other; prefer resolved process.
        def _rank(r: PortRecord) -> tuple:
            state_rank = 0 if r.state == "LISTEN" else (1 if r.state == "ESTABLISHED" else 2)
            proc_rank = 0 if r.process else 1
            return (state_rank, proc_rank)

        by_port: dict[int, PortRecord] = {}
        for r in self.records:
            port = r.local_port
            if port not in by_port or _rank(r) < _rank(by_port[port]):
                by_port[port] = r
        unique = sorted(by_port.values(), key=lambda r: r.local_port)

        # ── geometry ─────────────────────────────────────────────────
        body_w = 38                         # inner width including ║…║
        body_content_w = body_w - 2         # chars between the ║ walls
        body_min_content = 8                # min content rows (title, stats, bar, user)

        # Available pin rows per side = (terminal height - 4) / 2
        # The 4 accounts for: top frame, top border, bottom border, bottom margin
        max_pins_per_side = max(4, (height - 4) // 2)

        # How many unique ports do we need to show per side?
        half_ports = (len(unique) + 1) // 2
        left_count = min(half_ports, max_pins_per_side)
        right_count = min(len(unique) - left_count, max_pins_per_side)

        # Reserve last slot for overflow indicator if needed
        total_visible = left_count + right_count
        overflow = len(unique) - total_visible

        if overflow > 0 and left_count > 1:
            show_left = unique[: left_count - 1]
            left_overflow = len(unique) - (left_count - 1 + right_count)
        else:
            show_left = unique[:left_count]
            left_overflow = 0

        if overflow > 0 and right_count > 1:
            right_start = len(show_left)
            show_right = unique[right_start : right_start + right_count - 1]
            right_overflow = len(unique) - len(show_left) - len(show_right)
        else:
            right_start = len(show_left)
            show_right = unique[right_start : right_start + right_count]
            right_overflow = 0

        # Body height stretches to match the pin count (whichever side is taller)
        pin_side_rows = max(len(show_left) + (1 if left_overflow else 0),
                           len(show_right) + (1 if right_overflow else 0))
        body_h = max(body_min_content + 2, pin_side_rows + 2)  # +2 for ╔ and ╚

        # horizontal geometry
        port_w = 5                          # "  443" right-aligned
        sym_w = 1                           # "●"
        gap = 1                             # space between port and symbol
        trace_w = max(3, (width - body_w) // 2 - port_w - sym_w - gap - 1)
        left_pin_w = port_w + gap + sym_w + trace_w + 1  # +1 for ┤
        right_pin_w = 1 + trace_w + gap + sym_w + gap + port_w  # ├ + trace + sym + port

        body_left = left_pin_w
        body_right = body_left + body_w

        total_w = max(width, body_right + right_pin_w)

        # vertical: center body in available height
        body_top = max(1, (height - body_h) // 2)

        # ── stats ────────────────────────────────────────────────────
        n_listen = sum(1 for r in self.records if r.state == "LISTEN")
        n_est = sum(1 for r in self.records if r.state == "ESTABLISHED")
        n_total = len(self.records)
        n_other = n_total - n_listen - n_est
        user = _safe_getuser()

        # bar
        bar_w = body_content_w - 2  # small margin
        bl = _bar_seg(n_listen, n_total, bar_w)
        be = _bar_seg(n_est, n_total, bar_w)
        bo = max(0, bar_w - bl - be)
        bar_str = "▓" * bl + "▒" * be + "░" * bo

        # ── build plain-text rows ────────────────────────────────────
        lines: List[str] = []
        # metadata for styling: list of (row_index, col, length, style_name)
        spans: List[Tuple[int, int, int, str]] = []

        for row in range(height):
            body_row = row - body_top  # -1 = above body, 0 = top border

            # --- chip body ---
            if 0 <= body_row < body_h:
                body_line = self._body_line(
                    body_row, body_content_w, body_h, n_listen, n_est,
                    n_other, n_total, bar_str, user,
                )
                mid = "║" + body_line + "║"
                if body_row == 0:
                    mid = "╔" + "═" * body_content_w + "╗"
                elif body_row == body_h - 1:
                    mid = "╚" + "═" * body_content_w + "╝"
            else:
                mid = " " * body_w

            # --- left pin ---
            pin_index = body_row - 1  # body_row 1 = first pin row
            left_str = " " * left_pin_w
            if 0 <= pin_index < left_count and 0 <= body_row < body_h:
                if pin_index < len(show_left):
                    r = show_left[pin_index]
                    left_str = self._left_pin(r, port_w, trace_w)
                    # style spans
                    col = 0
                    spans.append((row, col, port_w, "port_label"))
                    spans.append((row, col + port_w + gap, sym_w, _color(r)))
                    spans.append((row, col + port_w + gap + sym_w, trace_w + 1, "trace"))
                elif left_overflow > 0 and pin_index == left_count - 1:
                    overflow_txt = f"... +{left_overflow} more"
                    left_str = overflow_txt.rjust(left_pin_w)
                    spans.append((row, left_pin_w - len(overflow_txt), len(overflow_txt), "body_dim"))

            # --- right pin ---
            right_str = " " * right_pin_w
            if 0 <= pin_index < right_count and 0 <= body_row < body_h:
                if pin_index < len(show_right):
                    r = show_right[pin_index]
                    right_str = self._right_pin(r, port_w, trace_w)
                    col = body_right
                    spans.append((row, col, 1 + trace_w, "trace"))
                    spans.append((row, col + 1 + trace_w + gap, sym_w, _color(r)))
                    spans.append((row, col + 1 + trace_w + gap + sym_w + gap, port_w, "port_label"))
                elif right_overflow > 0 and pin_index == right_count - 1:
                    overflow_txt = f"... +{right_overflow} more"
                    right_str = overflow_txt.ljust(right_pin_w)
                    spans.append((row, body_right, len(overflow_txt), "body_dim"))

            # --- body styling ---
            if 0 <= body_row < body_h:
                if body_row == 0 or body_row == body_h - 1:
                    spans.append((row, body_left, body_w, "chip_border"))
                else:
                    # ║ borders
                    spans.append((row, body_left, 1, "chip_border"))
                    spans.append((row, body_right - 1, 1, "chip_border"))
                    # body text
                    spans.append((row, body_left + 1, body_content_w, "body_text"))

                    # bar row gets special colors — find it by checking content
                    content_row = body_row - 1
                    inner_rows = body_h - 2
                    pad_top = max(0, (inner_rows - 8) // 2)
                    ci = content_row - pad_top
                    if ci == 5:  # bar is content line index 5
                        bar_start = body_left + 1 + (body_content_w - bar_w) // 2
                        spans.append((row, bar_start, bl, "bar_listen"))
                        spans.append((row, bar_start + bl, be, "bar_est"))
                        spans.append((row, bar_start + bl + be, bo, "bar_other"))

            full_line = left_str + mid + right_str
            # pad or trim to exact width
            if len(full_line) < total_w:
                full_line += " " * (total_w - len(full_line))
            lines.append(full_line[:total_w])

        # ── assemble styled Text ─────────────────────────────────────
        plain = "\n".join(lines)
        text = Text(plain)

        row_offsets = []
        offset = 0
        for line in lines:
            row_offsets.append(offset)
            offset += len(line) + 1  # +1 for \n

        for row_idx, col, length, style_name in spans:
            if row_idx >= len(row_offsets) or length <= 0:
                continue
            color = _COLORS.get(style_name, style_name)
            start = row_offsets[row_idx] + col
            end = start + length
            if end <= len(plain):
                text.stylize(color, start, end)

        return text

    # ── private helpers ──────────────────────────────────────────────

    def _loading_screen(self, width: int, height: int) -> Text:
        lines = []
        for i in range(height):
            if i == height // 2:
                lines.append("LOADING".center(width))
            elif i == height // 2 + 1:
                lines.append("····".center(width))
            else:
                lines.append(" " * width)
        return Text("\n".join(lines), style="bright_black")

    def _body_line(
        self, body_row: int, cw: int, body_h: int,
        n_listen: int, n_est: int, n_other: int, n_total: int,
        bar_str: str, user: str,
    ) -> str:
        """Return the inner content for one body row (between ║ walls).

        Content is vertically centered within the body.  The 8 content
        lines are: title, blank, stats1, stats2, blank, bar, blank, user.
        """
        content_lines = [
            "portwatch".center(cw),
            " " * cw,
            f"{n_listen} LISTEN · {n_est} ESTABLISHED".center(cw),
            f"{n_other} other · {n_total} total".center(cw),
            " " * cw,
            bar_str.center(cw),
            " " * cw,
            f" running as: {user}".ljust(cw),
        ]
        inner_rows = body_h - 2  # rows between ╔ and ╚
        # body_row 0 = ╔, body_row body_h-1 = ╚
        content_row = body_row - 1  # 0-indexed content row
        if content_row < 0 or content_row >= inner_rows:
            return " " * cw

        # Center the 8 content lines vertically
        pad_top = max(0, (inner_rows - len(content_lines)) // 2)
        ci = content_row - pad_top
        if 0 <= ci < len(content_lines):
            return content_lines[ci]
        return " " * cw

    def _left_pin(self, r: PortRecord, port_w: int, trace_w: int) -> str:
        """Build one left-side pin: '  443 ●───┤'"""
        port = str(r.local_port).rjust(port_w)
        sym = _sym(r)
        trace = "─" * trace_w + "┤"
        return f"{port} {sym}{trace}"

    def _right_pin(self, r: PortRecord, port_w: int, trace_w: int) -> str:
        """Build one right-side pin: '├───● 443  '"""
        port = str(r.local_port).ljust(port_w)
        sym = _sym(r)
        trace = "├" + "─" * trace_w
        return f"{trace} {sym} {port}"


# ── module-level helpers ─────────────────────────────────────────────

def _bar_seg(count: int, total: int, width: int) -> int:
    if total <= 0 or width <= 0:
        return 0
    return max(0, min(width, round((count / total) * width)))


def _safe_getuser() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return "unknown"