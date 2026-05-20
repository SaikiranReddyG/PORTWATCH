PHASE_1F Report

Files created (with line counts):
- portwatch/diff.py: 73
- tests/test_diff.py: 127

Files modified: none

Full pytest -v output (43 tests):

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/reddy/codex-workspace/PORTWATCH
configfile: pyproject.toml
plugins: anyio-4.12.1
collecting ... collected 43 items

tests/test_diff.py::test_identical_snapshots_diff_is_empty PASSED        [  2%]
tests/test_diff.py::test_new_port_detected_as_added PASSED               [  4%]
tests/test_diff.py::test_closed_port_detected_as_removed PASSED          [  6%]
tests/test_diff.py::test_state_change_detected PASSED                    [  9%]
tests/test_diff.py::test_process_change_detected PASSED                  [ 11%]
tests/test_diff.py::test_pid_change_same_process_name_detected PASSED    [ 13%]
tests/test_diff.py::test_remote_endpoint_change_detected PASSED          [ 16%]
tests/test_diff.py::test_uid_change_alone_not_detected PASSED            [ 18%]
tests/test_diff.py::test_multiple_changes_at_once PASSED                 [ 20%]
tests/test_diff.py::test_empty_previous_all_added PASSED                 [ 23%]
tests/test_diff.py::test_empty_current_all_removed PASSED                [ 25%]
tests/test_diff.py::test_both_empty_is_empty PASED                      [ 27%]
tests/test_proc.py::test_empty_file_returns_empty_list PASSED            [ 30%]
tests/test_proc.py::test_basic_parses_listen_and_established PASSED      [ 32%]
tests/test_proc.py::test_mixed_states_are_all_recognised PASSED          [ 34%]
tests/test_proc.py::test_listen_socket_has_zero_remote_port PASSED       [ 37%]
tests/test_proc.py::test_malformed_rows_are_skipped_not_raised PASSED    [ 39%]
tests/test_proc.py::test_unknown_state_code_yields_unknown_string PASSED [ 41%]
tests/test_proc.py::test_missing_file_raises_filenotfound PASSED         [ 44%]
tests/test_proc.py::test_tcp6_basic_parses_listen_and_established PASSED [ 46%]
tests/test_proc.py::test_tcp6_loopback_is_compressed PASSED              [ 48%]
tests/test_proc.py::test_tcp6_malformed_rows_skipped PASSED              [ 51%]
tests/test_proc.py::test_udp4_basic_parses_close_and_established PASSED  [ 53%]
tests/test_proc.py::test_udp4_close_state_is_07 PASSED                   [ 55%]
tests/test_proc.py::test_udp6_basic_parses_sockets PASSED                [ 58%]
tests/test_proc.py::test_read_all_combines_all_protocols PASSED          [ 60%]
tests/test_proc.py::test_read_all_survives_missing_file PASSED           [ 62%]
tests/test_process.py::test_build_inode_map_finds_socket_inodes PASSED   [ 65%]
tests/test_process.py::test_build_inode_map_skips_permission_error PASSED [ 67%]
tests/test_process.py::test_resolve_pid_full_info PASSED                 [ 69%]
tests/test_process.py::test_resolve_pid_missing_exe PASSED               [ 72%]
tests/test_process.py::test_resolve_pid_username_fallback PASSED         [ 74%]
tests/test_process.py::test_resolve_inode_found PASSED                   [ 76%]
tests/test_process.py::test_resolve_inode_not_found PASSED               [ 79%]
tests/test_process.py::test_resolve_inodes_batch PASSED                  [ 81%]
tests/test_process.py::test_cmdline_null_bytes_replaced PASSED           [ 83%]
tests/test_snapshot.py::test_take_snapshot_joins_socket_and_process PASSED [ 86%]
tests/test_snapshot.py::test_take_snapshot_unresolved_process_is_none PASSED [ 88%]
tests/test_snapshot.py::test_take_snapshot_multiple_protocols PASSED     [ 90%]
tests/test_snapshot.py::test_take_snapshot_empty_system PASSED           [ 93%]
tests/test_snapshot.py::test_take_snapshot_preserves_order PASSED        [ 95%]
tests/test_snapshot.py::test_convenience_properties PASSED               [ 97%]
tests/test_snapshot.py::test_read_all_accepts_proc_root PASSED           [100%]

============================== 43 passed in 0.13s
```

`python3 -c "from portwatch.diff import diff_snapshots, SnapshotDiff; print('import OK')"` output:

```
import OK
```

Manual sanity check (example code and output):

```py
from portwatch.snapshot import PortRecord
from portwatch.proc import Socket
from portwatch.process import ProcessInfo
from portwatch.diff import diff_snapshots

s1 = Socket('tcp4','0.0.0.0',80,'0.0.0.0',0,'LISTEN',100,0)
p1 = ProcessInfo(pid=100,name='nginx',exe='/usr/sbin/nginx',cmdline='nginx',uid=0,username='root')
r1 = PortRecord(socket=s1, process=p1)

s2 = Socket('tcp4','0.0.0.0',443,'0.0.0.0',0,'LISTEN',101,0)
p2 = ProcessInfo(pid=101,name='nginx',exe='/usr/sbin/nginx',cmdline='nginx',uid=0,username='root')
r2 = PortRecord(socket=s2, process=p2)

res = diff_snapshots([r1],[r1,r2])
print('added:', [r.local_port for r in res.added])
```

```
added: [443]
```

`portwatch --version` output:

```
portwatch 0.0.1
```

`portwatch --dump` first 3 lines (regression check):

```
tcp4  127.0.0.1:53  0.0.0.0:0  LISTEN  ??? (pid=-, inode=15246)  uid=0
tcp4  127.0.0.1:631  0.0.0.0:0  LISTEN  ??? (pid=-, inode=13858)  uid=0
tcp4  0.0.0.0:6006  0.0.0.0:0  LISTEN  ??? (pid=-, inode=21325)  uid=0
```

Last git stat for PHASE_1F commit:

```text
commit 1f502406d24c40581a5161d319ca228b8f1b298f (HEAD -> phase-1f)
Author: GANGULA SAI KIRAN REDDY <saikiranreddy19565@gmail.com>
Date:   Wed May 20 12:36:26 2026 +0200

	PHASE_1F: add diff engine and unit tests

 portwatch/diff.py  |  73 ++++++++++++++++++++++++++++++
 tests/test_diff.py | 127 +++++++++++++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 200 insertions(+)
```

