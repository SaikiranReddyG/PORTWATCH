# PHASE 2B Report — Live Updates + Interaction

Date: 2026-05-20

## Summary
- Implemented live polling in `portwatch/app.py` with `asyncio.to_thread` polling, diff tracking, sticky slot assignment, filtering, search state, detail panel state, and session summary printing on quit.
- Updated `portwatch/cli.py` to pass `--interval` through to the TUI.
- Added phase 2B coverage in `tests/test_app.py` for the display refresh path, sticky slot logic, expiry, filtering, and session stats.
- Kept `portwatch/widgets/chip.py` untouched in this phase.

## Files Created
- `PHASE_2B_REPORT.md` — 152 lines
- `phase2b_live_update.png` — screenshot artifact
- `phase2b_navigation.png` — screenshot artifact
- `phase2b_filter.png` — screenshot artifact

## Files Modified
- `portwatch/app.py` — replaced the single-snapshot TUI with a polling app, session stats, focus/filter/search state, and sticky slot management.
- `portwatch/cli.py` — passed `--interval` into `run_tui()`.
- `tests/test_app.py` — added phase 2B unit coverage for display refresh, slot management, filters, and stats.

## Manual Verification

### 1. `pytest -v`

```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0 -- /home/reddy/codex-workspace/PORTWATCH/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/reddy/codex-workspace/PORTWATCH
configfile: pyproject.toml
collecting ... collected 61 items

tests/test_app.py::test_chip_widget_renders_without_error PASSED         [  1%]
tests/test_app.py::test_chip_widget_empty_records_shows_loading PASSED   [  3%]
tests/test_app.py::test_chip_widget_pin_count_matches_records PASSED     [  4%]
tests/test_app.py::test_status_bar_contains_version PASSED               [  6%]
tests/test_app.py::test_chip_display_update_records PASSED               [  8%]
tests/test_app.py::test_sticky_slots_preserve_position PASSED            [  9%]
tests/test_app.py::test_sticky_slots_expiry PASSED                       [ 11%]
tests/test_app.py::test_filter_listen_only PASSED                        [ 13%]
tests/test_app.py::test_session_stats_accumulate PASSED                  [ 14%]
tests/test_diff.py::test_identical_snapshots_diff_is_empty PASSED        [ 16%]
tests/test_diff.py::test_new_port_detected_as_added PASSED               [ 18%]
tests/test_diff.py::test_closed_port_detected_as_removed PASSED          [ 19%]
tests/test_diff.py::test_state_change_detected PASSED                    [ 21%]
tests/test_diff.py::test_process_change_detected PASSED                  [ 22%]
tests/test_diff.py::test_pid_change_same_process_name_detected PASSED    [ 24%]
tests/test_diff.py::test_remote_endpoint_change_detected PASSED          [ 26%]
tests/test_diff.py::test_uid_change_alone_not_detected PASSED            [ 27%]
tests/test_diff.py::test_multiple_changes_at_once PASSED                 [ 29%]
tests/test_diff.py::test_empty_previous_all_added PASSED                 [ 31%]
tests/test_diff.py::test_empty_current_all_removed PASSED                [ 32%]
tests/test_diff.py::test_both_empty_is_empty PASSED                      [ 34%]
tests/test_loop.py::test_session_stats_defaults PASSED                   [ 36%]
tests/test_loop.py::test_format_added_line PASSED                        [ 37%]
tests/test_loop.py::test_format_removed_line PASSED                      [ 39%]
tests/test_loop.py::test_format_changed_line PASSED                      [ 40%]
tests/test_loop.py::test_format_unresolved_process PASSED                [ 42%]
tests/test_loop.py::test_exit_summary_format PASSED                      [ 44%]
tests/test_loop.py::test_exit_summary_short_runtime PASSED               [ 45%]
tests/test_loop.py::test_exit_summary_long_runtime PASSED                [ 47%]
tests/test_loop.py::test_baseline_summary_counts PASSED                  [ 49%]
tests/test_proc.py::test_empty_file_returns_empty_list PASSED            [ 50%]
tests/test_proc.py::test_basic_parses_listen_and_established PASSED      [ 52%]
tests/test_proc.py::test_mixed_states_are_all_recognised PASSED          [ 54%]
tests/test_proc.py::test_listen_socket_has_zero_remote_port PASSED       [ 55%]
tests/test_proc.py::test_malformed_rows_are_skipped_not_raised PASSED    [ 57%]
tests/test_proc.py::test_unknown_state_code_yields_unknown_string PASSED [ 59%]
tests/test_proc.py::test_missing_file_raises_filenotfound PASSED         [ 60%]
tests/test_proc.py::test_tcp6_basic_parses_listen_and_established PASSED [ 62%]
tests/test_proc.py::test_tcp6_loopback_is_compressed PASSED              [ 63%]
tests/test_proc.py::test_tcp6_malformed_rows_skipped PASSED              [ 65%]
tests/test_proc.py::test_udp4_basic_parses_close_and_established PASSED  [ 67%]
tests/test_proc.py::test_udp4_close_state_is_07 PASSED                   [ 68%]
tests/test_proc.py::test_udp6_basic_parses_sockets PASSED                [ 70%]
tests/test_proc.py::test_read_all_combines_all_protocols PASSED          [ 72%]
tests/test_proc.py::test_read_all_survives_missing_file PASSED           [ 73%]
tests/test_process.py::test_build_inode_map_finds_socket_inodes PASSED   [ 75%]
tests/test_process.py::test_build_inode_map_skips_permission_error PASSED [ 77%]
tests/test_process.py::test_resolve_pid_full_info PASSED                 [ 78%]
tests/test_process.py::test_resolve_pid_missing_exe PASSED               [ 80%]
tests/test_process.py::test_resolve_pid_username_fallback PASSED         [ 81%]
tests/test_process.py::test_resolve_inode_found PASSED                   [ 83%]
tests/test_process.py::test_resolve_inode_not_found PASSED               [ 85%]
tests/test_process.py::test_resolve_inodes_batch PASSED                  [ 86%]
tests/test_process.py::test_cmdline_null_bytes_replaced PASSED           [ 88%]
tests/test_snapshot.py::test_take_snapshot_joins_socket_and_process PASSED [ 90%]
tests/test_snapshot.py::test_take_snapshot_unresolved_process_is_none PASSED [ 91%]
tests/test_snapshot.py::test_take_snapshot_multiple_protocols PASSED     [ 93%]
tests/test_snapshot.py::test_take_snapshot_empty_system PASSED           [ 95%]
tests/test_snapshot.py::test_take_snapshot_preserves_order PASSED        [ 96%]
tests/test_snapshot.py::test_convenience_properties PASSED               [ 98%]
tests/test_snapshot.py::test_read_all_accepts_proc_root PASSED           [100%]

============================== 61 passed in 0.23s ==============================
```

### 2. Live update test

I captured render-based screenshots of the live TUI state rather than an interactive terminal recording in this harness.

- [Live update screenshot](phase2b_live_update.png)

### 3. Navigation test

- [Navigation screenshot](phase2b_navigation.png)

### 4. Filter test

- [Filter screenshot](phase2b_filter.png)

### 5. `portwatch --version` and `portwatch --dump`

```text
portwatch 0.0.1
```

```text
tcp4  127.0.0.1:53  0.0.0.0:0  LISTEN  ??? (pid=-, inode=15246)  uid=0
tcp4  127.0.0.1:631  0.0.0.0:0  LISTEN  ??? (pid=-, inode=13858)  uid=0
tcp4  0.0.0.0:6006  0.0.0.0:0  LISTEN  ??? (pid=-, inode=21325)  uid=0
tcp4  127.0.0.1:8765  0.0.0.0:0  LISTEN  ??? (pid=-, inode=545396)  uid=0
tcp4  127.0.0.1:9200  0.0.0.0:0  LISTEN  ??? (pid=-, inode=20038)  uid=0
tcp4  127.0.0.54:53  0.0.0.0:0  LISTEN  ??? (pid=-, inode=14982)  uid=991
tcp4  0.0.0.0:8080  0.0.0.0:0  LISTEN  ??? (pid=-, inode=27124)  uid=0
tcp4  0.0.0.0:8000  0.0.0.0:0  LISTEN  ??? (pid=-, inode=29866)  uid=0
tcp4  192.168.122.1:53  0.0.0.0:0  LISTEN  ??? (pid=-, inode=14000)  uid=0
tcp4  0.0.0.0:26466  0.0.0.0:0  LISTEN  ??? (pid=-, inode=25359)  uid=0
tcp4  0.0.0.0:445  0.0.0.0:0  LISTEN  ??? (pid=-, inode=11933)  uid=0
tcp4  0.0.0.0:139  0.0.0.0:0  LISTEN  ??? (pid=-, inode=11934)  uid=0
```

### 6. `git diff --stat`

```text
 portwatch/app.py  | 602 +++++++++++++++++++++++++++++++++++++++++++++++++++---
 portwatch/cli.py  |   2 +-
 tests/test_app.py |  57 +++++-
 3 files changed, 634 insertions(+), 27 deletions(-)
```

## Screenshots
- [phase2b_live_update.png](phase2b_live_update.png)
- [phase2b_navigation.png](phase2b_navigation.png)
- [phase2b_filter.png](phase2b_filter.png)

## Decisions and Notes
- I used `asyncio.to_thread` for polling to avoid blocking the Textual event loop.
- The sticky-slot logic lives in `portwatch/app.py` as requested for this phase.
- The screenshots were generated from the app's render state for review in this environment.
- The current live TUI render is functional and test-covered, but the visual layout is still plain-text oriented rather than a fully stylized Rich theme.
