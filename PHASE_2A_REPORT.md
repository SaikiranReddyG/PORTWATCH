# PHASE 2A Report — Textual Chip Widget

Date: 2026-05-20

Summary
- Implemented a headless `ChipWidget` renderable using Rich in `portwatch/widgets/chip.py`.
- Added a minimal TUI runner `portwatch/app.py` (lazy-imports Textual at runtime).
- Added `textual` and `rich` to `pyproject.toml` project dependencies.
- Added unit tests `tests/test_app.py` exercising the widget render and status line.
- Added a `--tui` CLI flag to `portwatch/cli.py` which launches the TUI via `run_tui()`.

Verification Checklist

- **pyproject.toml:** dependency entries for `textual` and `rich` — implemented ([pyproject.toml](pyproject.toml)).
- **Widget implementation:** `portwatch/widgets/chip.py` — implemented ([portwatch/widgets/chip.py](portwatch/widgets/chip.py)).
- **Widget export:** `portwatch/widgets/__init__.py` — implemented ([portwatch/widgets/__init__.py](portwatch/widgets/__init__.py)).
- **TUI runner:** `portwatch/app.py` exposes `run_tui()` and lazy-imports Textual — implemented ([portwatch/app.py](portwatch/app.py)).
- **CLI flag:** `--tui` added to `portwatch/cli.py` — implemented ([portwatch/cli.py](portwatch/cli.py)).
- **Unit tests:** `tests/test_app.py` added and run — implemented ([tests/test_app.py](tests/test_app.py)).
- **Tests:** full test suite passes locally in this workspace — 56 passed (output below).

Important note about real-host TUI
- This environment may not have `textual` available for interactive demos. The `ChipWidget` class is implemented so it can be rendered headlessly (no Textual terminal required) for review and unit tests.
- To run the real TUI on your host (requires installing dependencies), create and activate a virtualenv and install the project extras, then run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
portwatch --tui
```

Headless chip render (sample)

Below is a text capture of `ChipWidget.render()` using a representative set of sockets (this is the headless render used for unit tests and for visual review):

```
              ┌────────────────────────────────────────┐
   22 ● ──────┤├────── ● 3306 
   53 ● ──────┤  ╔══════════════════════════════════════╗├────── ● 5432 
   80 ● ──────┤  ║              portwatch               ║├────── ● 8080 
  443 ● ──────┤  ║                                      ║├────── ● 9000 
                ║8 LISTEN · 0 ESTABLISHED · 0 other · 8 total║
                ║                                      ║
                ╚══════════════════════════════════════╝
              └────────────────────────────────────────┘
```

Full test output (`pytest -v`)

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/reddy/codex-workspace/PORTWATCH
configfile: pyproject.toml
plugins: anyio-4.12.1
collecting ... collected 56 items

tests/test_app.py::test_chip_widget_renders_without_error PASSED         [  1%]
tests/test_app.py::test_chip_widget_empty_records_shows_loading PASSED   [  3%]
tests/test_app.py::test_chip_widget_pin_count_matches_records PASSED     [  5%]
tests/test_app.py::test_status_bar_contains_version PASSED               [  7%]
tests/test_diff.py::test_identical_snapshots_diff_is_empty PASSED        [  8%]
tests/test_diff.py::test_new_port_detected_as_added PASSED               [ 10%]
tests/test_diff.py::test_closed_port_detected_as_removed PASSED          [ 12%]
tests/test_diff.py::test_state_change_detected PASSED                    [ 14%]
tests/test_diff.py::test_process_change_detected PASSED                  [ 16%]
tests/test_diff.py::test_pid_change_same_process_name_detected PASSED    [ 17%]
tests/test_diff.py::test_remote_endpoint_change_detected PASSED          [ 19%]
tests/test_diff.py::test_uid_change_alone_not_detected PASSED            [ 21%]
tests/test_diff.py::test_multiple_changes_at_once PASSED                 [ 23%]
tests/test_diff.py::test_empty_previous_all_added PASSED                 [ 25%]
tests/test_diff.py::test_empty_current_all_removed PASSED                [ 26%]
tests/test_diff.py::test_both_empty_is_empty PASSED                      [ 28%]
tests/test_loop.py::test_session_stats_defaults PASSED                   [ 30%]
tests/test_loop.py::test_format_added_line PASSED                        [ 32%]
tests/test_loop.py::test_format_removed_line PASSED                      [ 33%]
tests/test_loop.py::test_format_changed_line PASSED                      [ 35%]
tests/test_loop.py::test_format_unresolved_process PASSED                [ 37%]
tests/test_loop.py::test_exit_summary_format PASSED                      [ 39%]
tests/test_loop.py::test_exit_summary_short_runtime PASSED               [ 41%]
tests/test_loop.py::test_exit_summary_long_runtime PASSED                [ 42%]
tests/test_loop.py::test_baseline_summary_counts PASSED                  [ 44%]
tests/test_proc.py::test_empty_file_returns_empty_list PASSED            [ 46%]
tests/test_proc.py::test_basic_parses_listen_and_established PASSED      [ 48%]
tests/test_proc.py::test_mixed_states_are_all_recognised PASSED          [ 50%]
tests/test_proc.py::test_listen_socket_has_zero_remote_port PASSED       [ 51%]
tests/test_proc.py::test_malformed_rows_are_skipped_not_raised PASSED    [ 53%]
tests/test_proc.py::test_unknown_state_code_yields_unknown_string PASSED [ 55%]
tests/test_proc.py::test_missing_file_raises_filenotfound PASSED         [ 57%]
tests/test_proc.py::test_tcp6_basic_parses_listen_and_established PASSED [ 58%]
tests/test_proc.py::test_tcp6_loopback_is_compressed PASSED              [ 60%]
tests/test_proc.py::test_tcp6_malformed_rows_skipped PASSED              [ 62%]
tests/test_proc.py::test_udp4_basic_parses_close_and_established PASSED  [ 64%]
tests/test_proc.py::test_udp4_close_state_is_07 PASSED                   [ 66%]
tests/test_proc.py::test_udp6_basic_parses_sockets PASSED                [ 67%]
tests/test_proc.py::test_read_all_combines_all_protocols PASSED          [ 69%]
tests/test_proc.py::test_read_all_survives_missing_file PASSED           [ 71%]
tests/test_process.py::test_build_inode_map_finds_socket_inodes PASSED   [ 73%]
tests/test_process.py::test_build_inode_map_skips_permission_error PASSED [ 75%]
tests/test_process.py::test_resolve_pid_full_info PASSED                 [ 76%]
tests/test_process.py::test_resolve_pid_missing_exe PASSED               [ 78%]
tests/test_process.py::test_resolve_pid_username_fallback PASSED         [ 80%]
tests/test_process.py::test_resolve_inode_found PASSED                   [ 82%]
tests/test_process.py::test_resolve_inode_not_found PASSED               [ 83%]
tests/test_process.py::test_resolve_inodes_batch PASSED                  [ 85%]
tests/test_process.py::test_cmdline_null_bytes_replaced PASSED           [ 87%]
tests/test_snapshot.py::test_take_snapshot_joins_socket_and_process PASSED [ 89%]
tests/test_snapshot.py::test_take_snapshot_unresolved_process_is_none PASSED [ 91%]
tests/test_snapshot.py::test_take_snapshot_multiple_protocols PASSED     [ 92%]
tests/test_snapshot.py::test_take_snapshot_empty_system PASSED           [ 94%]
tests/test_snapshot.py::test_take_snapshot_preserves_order PASSED        [ 96%]
tests/test_snapshot.py::test_convenience_properties PASSED               [ 98%]
tests/test_snapshot.py::test_read_all_accepts_proc_root PASSED           [100%]

============================== 56 passed in 0.22s ==============================
```

Notes and next steps

- If you want a true interactive screenshot from your host, run `portwatch --tui` after installing dependencies in a virtualenv as shown above; capture a terminal screenshot or use `script`/`asciinema` to record.
- If you want styling tweaks to the chip (icons, colors, layout, paging), I can iterate on `portwatch/widgets/chip.py` and provide updated headless renders for review before we run Phase 2B.

---

Files changed in this phase (committed):
- [pyproject.toml](pyproject.toml)
- [portwatch/widgets/chip.py](portwatch/widgets/chip.py)
- [portwatch/widgets/__init__.py](portwatch/widgets/__init__.py)
- [portwatch/app.py](portwatch/app.py)
- [portwatch/cli.py](portwatch/cli.py)
- [tests/test_app.py](tests/test_app.py)
