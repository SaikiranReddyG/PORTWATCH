# PHASE 2A — Textual App + Chip Widget (Static)

**Goal:** launch a Textual TUI app that renders the microcontroller chip diagram using a real snapshot from the host. No interaction, no live polling, no key bindings beyond `q` to quit. This phase proves the visual design works and that Textual is wired correctly.

**Definition of done:** running `portwatch --tui` opens a full-screen terminal app showing the chip diagram with real port data from the host, pins colored by state, and the chip body showing aggregate counts. Pressing `q` exits cleanly. The existing CLI behaviour (`portwatch` with no flags runs the text loop, `portwatch --dump` and `--version` still work) is unchanged.

---

## Context

You have completed Phase 1 (1A–1G). The repo contains:
- `portwatch/proc.py`, `process.py`, `snapshot.py`, `diff.py`, `loop.py` — the complete data layer
- `portwatch/cli.py` — entry point with `--dump`, `--version`, `--interval`, `--verbose`
- 52 passing tests

This phase introduces the first external dependency (Textual) and the first visual component.

Before reading further, you must have read `DECISIONS.md` (reference, not to-do list). The relevant sections are §5 (UI), §7 (package shape / widget contract), and §2.2 (permissions display).

If anything in this phase document conflicts with `DECISIONS.md`, follow this document and surface the conflict.

---

## In scope

### 1. New dependency

Add `textual>=0.70.0` and `rich` to the `[project.dependencies]` list in `pyproject.toml`. These are now runtime dependencies.

After updating `pyproject.toml`, reinstall with `pip install -e ".[dev]"` and verify import works: `python3 -c "import textual; print(textual.__version__)"`.

### 2. New files

Create the following structure:

```
portwatch/
├── widgets/
│   ├── __init__.py        # exports ChipWidget
│   └── chip.py            # the chip widget
├── app.py                 # the Textual app
```

### 3. The ChipWidget

Create `portwatch/widgets/chip.py`. This is the core visual component.

#### Data input

The widget receives a `list[PortRecord]` and renders the chip. In this phase, the data is passed once at construction time (static). In Phase 2B, it will be updated via Textual's reactive system.

#### Chip layout

The chip is rendered as a Rich renderable (using `rich.text.Text` or `rich.table.Table` or raw string assembly — whichever produces the cleanest output). The layout:

```
              ┌──────────────────────────────────────┐
    22 ●──────┤  ╔══════════════════════════════╗    ├──────● 80
    53 ●──────┤  ║        portwatch             ║    ├──────● 443
   631 ●──────┤  ║                              ║    ├──────● 3000
  3306 ◯──────┤  ║   26 LISTEN · 8 ESTABLISHED  ║    ├──────● 5432
  5432 ●──────┤  ║   61 other · 95 total         ║    ├──────● 6379
  6379 ◐──────┤  ║                              ║    ├──────● 8080
  8080 ●──────┤  ║   ▓▓▓▓▓▓░░░░  61% LISTEN     ║    ├──────◯ 9200
  9999 ✕──────┤  ╚══════════════════════════════╝    ├──────◐ 27017
              └──────────────────────────────────────┘
```

**Pin assignment rules (from DECISIONS.md §5.2):**
- On app start, collect all active ports (any socket in LISTEN, ESTABLISHED, or any non-closed state)
- Sort by port number ascending
- Split into left and right columns: first half on the left, second half on the right
- Left pins are right-aligned labels, right pins are left-aligned labels
- Maximum pins per side: if total active ports exceed what fits in the terminal height, show the top N that fit and add a `... +X more` indicator at the bottom of each side

**Pin symbols and colors (from DECISIONS.md §5.3 and §5.4):**

| State | Symbol | Color |
|-------|--------|-------|
| LISTEN, process known | `●` | green |
| LISTEN, process unknown (`???`) | `●` | yellow |
| ESTABLISHED | `◐` | cyan |
| TIME_WAIT, CLOSE_WAIT, FIN_WAIT* | `◯` | dim grey |
| CLOSE (UDP idle) | `◯` | dim grey |
| Suspicious (reserved, not active yet) | `✕` | red |
| Never-used slot | `····` | dim grey |

**Symbols are load-bearing** — meaning must be clear even without color (DECISIONS.md §5.3). Color is decorative reinforcement.

**Pin label format:** `<port_number> <symbol>` on the left side, `<symbol> <port_number>` on the right side. Port numbers are right-aligned on the left (padded to 5 chars) and left-aligned on the right.

**Pin trace lines:** the `──────┤` and `├──────` connecting pins to the chip body. Use `─` (box drawing thin horizontal). Length adjusts to terminal width — the chip body is centered, traces fill the gap.

#### Chip body content

The chip body (the rectangle in the center) displays:
- Title: `portwatch` centered on the first line
- Blank line
- State counts: `N LISTEN · N ESTABLISHED · N other · N total`
- Blank line
- A simple bar showing the proportion of LISTEN vs ESTABLISHED vs other, using `▓` for LISTEN, `▒` for ESTABLISHED, `░` for other. Bar width is 20 characters. Show the LISTEN percentage as a label.
- Blank line
- Privilege indicator: `running as: <username>` (or `running as: root` if running with sudo)

#### Chip border

Use double-line box drawing for the chip body (`╔`, `╗`, `╚`, `╝`, `║`, `═`) and single-line for the outer frame (`┌`, `┐`, `└`, `┘`, `│`, `─`). This creates the visual distinction between the IC package (outer) and the die (inner).

#### Terminal size handling (DECISIONS.md §5.5)

- Minimum 80 columns × 24 rows
- If the terminal is smaller, display a centered message: `portwatch needs at least 80×24` and do not render the chip
- The widget must respond to terminal resize (Textual handles this via `on_resize`)

### 4. The Textual App

Create `portwatch/app.py`:

```python
class PortwatchApp(textual.app.App):
```

**Behaviour:**
- On mount: take a single snapshot via `take_snapshot()`, pass it to `ChipWidget`, compose the widget
- CSS: dark background, no default Textual chrome (no header, no footer). The chip should be the only thing on screen, centered vertically and horizontally
- Key binding: `q` quits the app
- Key binding: `ctrl+c` quits the app (same as `q`)

**App CSS (inline or in a `.tcss` file, your choice):**
- Background: `$surface` (Textual's dark theme default)
- No scrollbars
- The chip widget is centered in the available space

### 5. Status bar

At the bottom of the screen (last row), render a single-line status bar:

```
portwatch v0.0.1 · 95 sockets · snapshot taken at 12:34:56 · q to quit
```

Use Textual's `Footer` or a custom `Static` widget pinned to the bottom. Dim/muted color so it doesn't compete with the chip.

### 6. Loading state (DECISIONS.md §5.6)

When the app first launches, before the snapshot is ready, show all pin slots as `····` with a `LOADING` text centered in the chip body. This state should be visible for at most 1–2 seconds on a normal system. After the snapshot arrives, replace with real data.

The loading state is implemented by having the widget render with an empty `PortRecord` list initially, then updating after mount.

### 7. CLI wiring

Add `--tui` flag to `portwatch/cli.py`. When present, launch the Textual app instead of the text loop.

- `portwatch` → text loop (unchanged, default behaviour from Phase 1G)
- `portwatch --tui` → Textual app (this phase)
- `portwatch --dump` → one-shot dump (unchanged)
- `portwatch --version` → version (unchanged)

Do **not** make `--tui` the default yet. The text loop remains the default until the TUI is proven stable across multiple phases.

### 8. Tests

Create `tests/test_app.py` with limited but meaningful tests:

1. `test_chip_widget_renders_without_error` — construct a `ChipWidget` with a small synthetic `list[PortRecord]` (3 records: one LISTEN, one ESTABLISHED, one TIME_WAIT). Call its `render()` method. Assert it returns a renderable without raising an exception. Do not assert exact visual output — that's too brittle.

2. `test_chip_widget_empty_records_shows_loading` — construct a `ChipWidget` with an empty list. Assert the rendered output contains the string `LOADING` or `····`.

3. `test_chip_widget_pin_count_matches_records` — construct a `ChipWidget` with 10 records. Assert the rendered output contains all 10 port numbers as substrings.

4. `test_chip_widget_respects_min_terminal_size` — this is hard to test in isolation; mark it as `@pytest.mark.skip(reason="requires live terminal — verified manually")` and include it in the manual checklist instead.

5. `test_status_bar_contains_version` — if the status bar is a separate widget, construct it and assert the output contains `v0.0.1`.

Total test count after this phase: **56** (52 existing + 4 new, 1 skipped).

### 9. CI update

The CI now needs to install Textual. Since `textual` is in `[project.dependencies]`, the existing `pip install -e ".[dev]"` will pick it up automatically. No workflow changes needed.

However: Textual tests may fail in CI if they try to render to a real terminal. Ensure all tests in `test_app.py` use Textual's headless mode or avoid calling `app.run()`. The widget's `render()` method should be testable without a live terminal.

---

## Out of scope (do not implement)

- Live polling / reactive updates to the chip (PHASE_2B)
- Any keyboard interaction beyond `q` to quit — no arrow keys, no Enter, no detail panel, no search, no filter (PHASE_2B)
- The suspicious heuristic or learning mode (PHASE_3)
- Pulse integration (PHASE_4)
- Widget extraction for Pulse reuse (PHASE_2C)
- Any modification to the data layer modules (`proc.py`, `process.py`, `snapshot.py`, `diff.py`, `loop.py`)
- Color theme customisation or user-configurable palettes
- Mouse interaction
- Animations beyond the initial loading → data transition

---

## Design intent (read this before coding)

The chip should look like a **real IC package** — not a table with borders. The visual metaphor matters. Think of it as a DIP (Dual Inline Package) chip viewed from above:

- The pins extend outward from the chip body, with trace lines connecting them
- The chip body is the "brain" — it shows aggregate intelligence, not raw data
- Each pin is a port — its symbol tells you the state at a glance
- The overall shape should be instantly recognisable to anyone who's seen a microcontroller datasheet

Err on the side of **too much whitespace** rather than too little. The chip should breathe. Cramming information into every cell makes it look like a table, not a chip.

The hacker aesthetic (DECISIONS.md §5.4) means: no rounded corners, no emoji, no pastel colors. Sharp edges, monospace precision, terminal green. Think `htop`, not `bpytop`.

---

## Manual verification checklist

After completing this phase, verify the following and include screenshots or pasted terminal output in `PHASE_2A_REPORT.md`.

1. `pytest -v` shows 56 tests (52 old + 4 new + 1 skipped) — paste full output

2. `portwatch --tui` launches a full-screen app showing the chip diagram. **Take a screenshot or paste the terminal output.** This is the most important verification item.

3. The chip shows real port data from the host — spot-check that port 631 (CUPS), port 53 (DNS), and port 6379 (Redis) appear as pins if they are listening

4. Pin symbols match states: LISTEN pins show `●`, ESTABLISHED pins show `◐`, TIME_WAIT pins show `◯`

5. The chip body shows correct aggregate counts — compare the "N LISTEN" count with `ss -tln | wc -l`

6. The status bar at the bottom shows the version, socket count, and timestamp

7. Pressing `q` exits the app cleanly (no traceback, returns to shell)

8. Terminal smaller than 80×24: resize your terminal to 60×20 and run `portwatch --tui` — confirm it shows the "needs at least 80×24" message instead of a broken layout

9. `portwatch` (no flags) still starts the text loop — **not** the TUI (regression check)

10. `portwatch --version` and `portwatch --dump` still work (regression check)

11. `git diff --stat` shows only the expected new/modified files

All outputs go into the report. For item 2, a screenshot is strongly preferred — paste the rendered chip as text if screenshots aren't possible.

---

## Phase report

At the end of this phase, create `PHASE_2A_REPORT.md` containing:

1. Files created with line counts
2. Files modified with a short description
3. The literal output of every command in the manual verification checklist
4. A screenshot or text paste of the chip rendering (this is the centrepiece of the report)
5. Any decisions you had to make that this document did not specify — visual design choices especially
6. Anything that looks wrong visually but you weren't sure how to fix — flag it for review rather than guessing

Do not start PHASE_2B. Wait for the user to review the report — **especially the visual output** — and hand you `PHASE_2B.md`.
