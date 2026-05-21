# PHASE 2B — Live Updates + Interaction

**Goal:** the TUI now polls every 2 seconds, updates the chip in real time, and supports keyboard interaction: arrow keys to move focus, Enter to inspect a pin, `d` to dismiss, `/` to search, `f` to filter, and `q` to quit with a session summary.

**Definition of done:** running `portwatch --tui` shows a live-updating chip where pins appear, disappear, and change state in real time. The user can navigate pins and inspect port details. Pressing `q` exits with the same session summary as the text loop.

---

## Context

You have completed PHASE_2A. The repo contains:
- `portwatch/widgets/chip.py` — the chip renderer (externally rewritten, do not modify the render logic)
- `portwatch/app.py` — the Textual app (externally rewritten, do not modify the compose structure)
- The complete data layer from Phase 1 (proc, process, snapshot, diff, loop)
- 52+ passing tests

Before reading further, you must have read `DECISIONS.md` (reference, not to-do list). The relevant sections are §2.3 (poll interval), §5.2 (sticky slots), §5.7 (keybindings), and §5.8 (exit summary).

If anything in this phase document conflicts with `DECISIONS.md`, follow this document and surface the conflict.

---

## In scope

### 1. Live polling in the TUI

Modify `portwatch/app.py` to poll on a timer instead of taking a single snapshot.

Use Textual's `set_interval` to schedule a callback every N seconds (default 2.0, respecting `--interval` from the CLI):

```python
def on_mount(self) -> None:
    self._poll()  # first snapshot immediately
    self.set_interval(self.poll_interval, self._poll)
```

The `_poll` method:
1. Calls `take_snapshot()`
2. Updates the `ChipDisplay` widget with the new records
3. Updates the status bar with the current time and socket count

**Important:** `take_snapshot()` is a blocking call (it reads `/proc` and scans fd directories). On a busy system this can take 100–500ms. Textual runs in an async event loop — a blocking call will freeze the UI. Use Textual's `run_worker` to run the snapshot in a background thread:

```python
@work(thread=True)
def _poll(self) -> None:
    snapshot = take_snapshot()
    self.call_from_thread(self._update_chip, snapshot)
```

If `run_worker` or `@work` is not available in the installed Textual version, use `asyncio.to_thread` as a fallback.

### 2. ChipDisplay update method

Add an `update_records(records)` method to `ChipDisplay` that:
1. Stores the new records
2. Re-renders the chip at the current terminal size
3. Calls `self.update(content)` to refresh the display

The `ChipWidget` is reconstructed each time — it is stateless. The `ChipDisplay` owns the Textual widget lifecycle.

### 3. Sticky pin slots (DECISIONS.md §5.2)

When the chip re-renders with new data, pins should not jump around. Implement sticky slot assignment:

- On the first render, assign slots sorted by port number (this is already done by `chip.py`)
- On subsequent renders, keep existing ports in their assigned slots
- New ports fill the first available empty slot
- A port that disappears: its slot stays reserved (dim `····`) for 30 seconds, then becomes available
- This logic belongs in `ChipDisplay` (or a new small helper), NOT in `chip.py`. The `ChipWidget.render()` receives a pre-ordered list of `PortRecord | None` where `None` represents an empty/reserved slot.

**Implementation approach:**
- `ChipDisplay` maintains a `_slot_map: dict[int, int]` mapping `port_number → slot_index`
- `ChipDisplay` maintains a `_slot_expiry: dict[int, float]` tracking when a vacated slot expires (30s after the port disappeared)
- On each poll, build the ordered slot list and pass it to `ChipWidget`

**Modify `ChipWidget` to handle `None` entries:** when it encounters a `None` in the records list, render that pin position as `····` (four dots) in dim grey with no trace line.

### 4. Diff-driven status line

When the diff between previous and current snapshot is non-empty, briefly flash a change indicator in the status bar:

```
portwatch v0.0.1 · 98 sockets · +2 -1 ~3 · last update 14:15:32 · q to quit
```

The `+2 -1 ~3` shows adds/removes/changes from the last diff. If the diff is empty (nothing changed), omit the diff section:

```
portwatch v0.0.1 · 98 sockets · last update 14:15:32 · q to quit
```

### 5. Keyboard interaction

Add the following key bindings to `PortwatchApp`:

**Navigation:**
- `Up` / `Down` — move focus to the previous/next pin (wraps around)
- `Left` / `Right` — jump between left and right pin columns
- The focused pin is highlighted with a reverse-video or bright-white background on its port label

**Inspection:**
- `Enter` — open a detail panel for the focused pin

**Detail panel:**
When Enter is pressed on a focused pin, show a panel (a Textual `Static` widget or overlay) at the bottom or right side of the screen with:
```
Port 8080 · tcp4 · 0.0.0.0
State: LISTEN
Process: nginx (pid=1234)
Binary: /usr/sbin/nginx
Cmdline: nginx: master process /usr/sbin/nginx
UID: 33 (www-data)
Remote: —
```

If the process is unresolved, show `Process: ???` and omit the binary/cmdline lines.

Press `Escape` or `Enter` again to close the detail panel.

**Filtering:**
- `f` — cycle through filter modes: All → LISTEN only → ESTABLISHED only → Suspicious only (placeholder, shows all for now) → back to All
- Show the active filter in the status bar: `[filter: LISTEN]`
- When a filter is active, only matching pins are rendered. Slots for filtered-out pins are hidden, not shown as empty.

**Search:**
- `/` — open a search input at the bottom of the screen
- Type a port number or process name to filter pins to matches
- `Escape` to cancel search, `Enter` to apply
- Search is a temporary filter — pressing `/` again or `Escape` clears it

**Dismiss (placeholder):**
- `d` — placeholder for dismiss-suspicious in Phase 3. For now, show a brief "no suspicious flags to dismiss" message in the status bar. Wire the keybinding so it exists.

**Quit:**
- `q` — exit the app and print the session summary to stdout (same format as the text loop from Phase 1G)
- `Ctrl+C` — same as `q`

### 6. Session tracking

Port the `SessionStats` tracking from `loop.py` into the TUI app. On each poll:
- Increment `snapshot_count`
- Update `peak_port_count` if the current count exceeds the previous peak
- Accumulate `changes_detected` from the diff

On quit, print the same summary format as Phase 1G to stdout (after the Textual app exits).

### 7. Pass `--interval` to the TUI

Update `cli.py` so that `portwatch --tui --interval 1` passes the interval to the app. The `PortwatchApp` should accept `poll_interval` as a constructor parameter.

### 8. Tests

Add to `tests/test_app.py`:

1. `test_chip_display_update_records` — construct a `ChipDisplay`, call `update_records` with new data, verify it doesn't raise.

2. `test_sticky_slots_preserve_position` — create a slot map with ports [22, 80, 443]. Update with [22, 443, 8080]. Assert port 22 stays in slot 0, port 443 stays in slot 2, port 8080 fills slot 1 (where 80 was). This tests the slot assignment logic, not the widget rendering.

3. `test_sticky_slots_expiry` — create a slot map, remove a port, advance time by 31 seconds (mock `time.time`), assert the slot is now available for reuse.

4. `test_filter_listen_only` — apply LISTEN filter to a mixed list of records, assert only LISTEN records remain.

5. `test_session_stats_accumulate` — simulate 3 poll cycles with known diffs, assert the stats match.

Total test count after this phase: **57+** (existing + 5 new).

### 9. CI

No CI changes needed. Textual widget tests should not require a live terminal.

---

## Out of scope (do not implement)

- Modifying the chip render logic in `chip.py` (the renderer is locked — only pass different data to it)
- The suspicious heuristic or learning mode (PHASE_3)
- Pulse integration (PHASE_4)
- Widget extraction for Pulse reuse (PHASE_2C)
- Mouse interaction
- Color theme customization
- Any changes to `proc.py`, `process.py`, `snapshot.py`, or `diff.py`

---

## Manual verification checklist

After completing this phase, verify the following and include literal outputs or screenshots in `PHASE_2B_REPORT.md`.

1. `pytest -v` shows all tests passing — paste full output

2. **Live update test:** run `portwatch --tui` in one terminal. In another terminal run `python3 -m http.server 7777`. Within 4 seconds, a new pin labeled `7777` should appear on the chip with a green `●`. Kill the http server. Within 34 seconds, the pin should dim to `····` and then disappear. **Screenshot or describe what you see.**

3. **Navigation test:** press Up/Down arrow keys. Confirm a pin gets highlighted (focused). Press Enter. Confirm the detail panel shows port info. Press Escape. Confirm the panel closes.

4. **Filter test:** press `f`. Confirm the status bar shows `[filter: LISTEN]` and only LISTEN pins remain. Press `f` again to cycle.

5. **Search test:** press `/`, type `8080`, press Enter. Confirm only port 8080 is shown. Press Escape to clear.

6. **Exit summary:** press `q`. Confirm the session summary prints to stdout with non-zero runtime, snapshot count, and changes count.

7. **Interval override:** run `portwatch --tui --interval 1`. Confirm the status bar updates every 1 second instead of every 2.

8. `portwatch --version` and `portwatch --dump` still work (regression check)

9. `git diff --stat` shows only expected files

---

## Phase report

At the end of this phase, create `PHASE_2B_REPORT.md` containing:

1. Files created with line counts
2. Files modified with a short description
3. The literal output of every command in the manual verification checklist
4. Screenshots of the live update, navigation, and filter behaviour
5. Any decisions you had to make that this document did not specify
6. Anything that looks wrong visually or feels off — flag it for review

Do not start PHASE_2C. Wait for the user to review the report and hand you `PHASE_2C.md`.
