# PHASE 1D Report

1. Files created / modified (with line counts)

- portwatch/process.py: 143 (new)
- portwatch/cli.py: 34 (modified: batch-resolve inodes and show process info in `--dump`)
- tests/test_process.py: 190 (new)

2. Tests: full `pytest -v` output

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/reddy/codex-workspace/PORTWATCH
configfile: pyproject.toml
plugins: anyio-4.12.1
collecting ... collected 24 items

tests/test_proc.py::test_empty_file_returns_empty_list PASSED            [  4%]
tests/test_proc.py::test_basic_parses_listen_and_established PASSED      [  8%]
tests/test_proc.py::test_mixed_states_are_all_recognised PASSED          [ 12%]
tests/test_proc.py::test_listen_socket_has_zero_remote_port PASSED       [ 16%]
tests/test_proc.py::test_malformed_rows_are_skipped_not_raised PASSED    [ 20%]
tests/test_proc.py::test_unknown_state_code_yields_unknown_string PASSED [ 25%]
tests/test_proc.py::test_missing_file_raises_filenotfound PASSED         [ 29%]
tests/test_proc.py::test_tcp6_basic_parses_listen_and_established PASSED [ 33%]
tests/test_proc.py::test_tcp6_loopback_is_compressed PASSED              [ 37%]
tests/test_proc.py::test_tcp6_malformed_rows_skipped PASSED              [ 41%]
tests/test_proc.py::test_udp4_basic_parses_close_and_established PASSED  [ 45%]
tests/test_proc.py::test_udp4_close_state_is_07 PASSED                   [ 50%]
tests/test_proc.py::test_udp6_basic_parses_sockets PASSED                [ 54%]
tests/test_proc.py::test_read_all_combines_all_protocols PASSED          [ 58%]
tests/test_proc.py::test_read_all_survives_missing_file PASSED           [ 62%]
tests/test_process.py::test_build_inode_map_finds_socket_inodes PASSED   [ 66%]
tests/test_process.py::test_build_inode_map_skips_permission_error PASSED [ 70%]
tests/test_process.py::test_resolve_pid_full_info PASSED                 [ 75%]
tests/test_process.py::test_resolve_pid_missing_exe PASSED               [ 79%]
tests/test_process.py::test_resolve_pid_username_fallback PASSED         [ 83%]
tests/test_process.py::test_resolve_inode_found PASSED                   [ 87%]
tests/test_process.py::test_resolve_inode_not_found PASSED               [ 91%]
tests/test_process.py::test_resolve_inodes_batch PASSED                  [ 95%]
tests/test_process.py::test_cmdline_null_bytes_replaced PASSED           [100%]

============================== 24 passed in 0.07s ==============================
```

3. `portwatch --dump` (first 20 lines)

```
tcp4  127.0.0.1:631  0.0.0.0:0  LISTEN  ??? (pid=-, inode=14846)  uid=0
tcp4  127.0.0.1:8765  0.0.0.0:0  LISTEN  ??? (pid=-, inode=33797)  uid=0
tcp4  127.0.0.1:9200  0.0.0.0:0  LISTEN  ??? (pid=-, inode=20383)  uid=0
tcp4  127.0.0.1:53  0.0.0.0:0  LISTEN  ??? (pid=-, inode=18557)  uid=0
tcp4  0.0.0.0:8000  0.0.0.0:0  LISTEN  ??? (pid=-, inode=26979)  uid=0
tcp4  0.0.0.0:8080  0.0.0.0:0  LISTEN  ??? (pid=-, inode=24145)  uid=0
tcp4  127.0.0.53:53  0.0.0.0:0  LISTEN  ??? (pid=-, inode=17533)  uid=991
tcp4  192.168.122.1:53  0.0.0.0:0  LISTEN  ??? (pid=-, inode=18718)  uid=0
tcp4  0.0.0.0:6006  0.0.0.0:0  LISTEN  ??? (pid=-, inode=32826)  uid=0
tcp4  127.0.0.54:53  0.0.0.0:0  LISTEN  ??? (pid=-, inode=17535)  uid=991
tcp4  0.0.0.0:139  0.0.0.0:0  LISTEN  ??? (pid=-, inode=10207)  uid=0
tcp4  127.0.0.1:8081  0.0.0.0:0  LISTEN  ??? (pid=-, inode=78943)  uid=0
tcp4  127.0.0.1:8005  0.0.0.0:0  LISTEN  ??? (pid=-, inode=30755)  uid=0
tcp4  0.0.0.0:445  0.0.0.0:0  LISTEN  ??? (pid=-, inode=10206)  uid=0
tcp4  127.0.0.1:55952  0.0.0.0:0  LISTEN  code (pid=76750, /usr/share/code/code)  uid=1000(reddy)
tcp4  127.0.0.1:6379  0.0.0.0:0  LISTEN  ??? (pid=-, inode=31755)  uid=0
tcp4  0.0.0.0:26466  0.0.0.0:0  LISTEN  ??? (pid=-, inode=25109)  uid=0
tcp4  192.168.1.50:35908  3.22.174.47:443  ESTABLISHED  chrome (pid=7771, /app/extra/chrome)  uid=1000(reddy)
tcp4  192.168.1.50:35912  3.22.174.47:443  ESTABLISHED  chrome (pid=7771, /app/extra/chrome)  uid=1000(reddy)
```

4. Spot-checks

- Port 631 (CUPS): the dump shows the LISTEN entry for `127.0.0.1:631` as `??? (pid=-, inode=14846)` — this is expected when running without root or when the inode is not visible via the `fd` scan (permission/race). The code correctly falls back to `???` per the phase spec.

- Example of a resolved process: `127.0.0.1:55952` shows `code (pid=76750, /usr/share/code/code)  uid=1000(reddy)`.

- Example of an unresolved process (expected for some system sockets): `127.0.0.1:631` is unresolved as `???`.

5. `portwatch --version`

```
portwatch 0.0.1
```

6. Git / commit info

- Current branch: `phase-1d`
- Last commit: `PHASE_1D: add process resolution, CLI batch inode resolution, and tests`

```
3 files changed, 343 insertions(+), 1 deletion(-)
  portwatch/cli.py      |  11 ++-
  portwatch/process.py  | 143 +++++++++++++++++++++++++++++++++++++
  tests/test_process.py | 190 ++++++++++++++++++++++++++++++++++++++++++++++++++
```

7. Decisions and notes

- Implemented a naive per-call `_build_inode_map(proc_root)` as specified. Comment in code notes this is an optimization point for PHASE_1E/1F.
- The CLI uses `resolve_inodes()` (batch) to avoid scanning `/proc` per socket.
- Many system sockets (for root or restricted processes) may be unresolved and display `???` when running as an unprivileged user; this is expected and not a bug.

8. Ambiguities / surprises

- `127.0.0.1:631` (CUPS) resolved to `???` in this run — on some systems CUPS' socket inode is visible and would show `cupsd`; on this host it was not exposed to the scanning process (permissions or timing), so it remains unresolved.

---

If you want, I can now:
- Attempt to push the `phase-1d` branch to a remote (provide remote URL or set `origin`).
- Run `portwatch --dump` as root (sudo) to show more resolved processes (requires your approval).
