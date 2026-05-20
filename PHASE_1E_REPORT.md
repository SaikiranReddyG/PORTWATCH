Last commit stat:

```text
commit 267212a3132534925b35e39e51b2a94cfb892adb (HEAD -> phase-1d)

	PHASE_1E: add snapshot builder, PortRecord, CLI integration, tests and fixture

 PHASE_1D_REPORT.md     | 112 +++++++++++++++++++++++++++++++++++++++++++++++++
 portwatch/cli.py       |  15 +++----
 portwatch/proc.py      |  12 +++---
 portwatch/snapshot.py  |  57 +++++++++++++++++++++++++
 tests/conftest.py      |  40 ++++++++++++++++++
 tests/test_process.py  |  68 ++++++++++--------------------
 tests/test_snapshot.py |  95 +++++++++++++++++++++++++++++++++++++++++
 7 files changed, 338 insertions(+), 61 deletions(-)
```
PHASE_1E Report

Files changed:
- portwatch/cli.py: updated to call take_snapshot()
- portwatch/snapshot.py: new snapshot builder and PortRecord dataclass
- portwatch/proc.py: read_all(proc_root) updated to accept proc_root
- tests/conftest.py: new fake_proc fixture
- tests/test_process.py: refactored to use fake_proc fixture
- tests/test_snapshot.py: new snapshot tests

Test output (pytest -v):

```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/reddy/codex-workspace/PORTWATCH
configfile: pyproject.toml
plugins: anyio-4.12.1
collecting ... collected 31 items

tests/test_proc.py::test_empty_file_returns_empty_list PASSED            [  3%]
tests/test_proc.py::test_basic_parses_listen_and_established PASSED      [  6%]
tests/test_proc.py::test_mixed_states_are_all_recognised PASSED          [  9%]
tests/test_proc.py::test_listen_socket_has_zero_remote_port PASSED       [ 12%]
tests/test_proc.py::test_malformed_rows_are_skipped_not_raised PASSED    [ 16%]
tests/test_proc.py::test_unknown_state_code_yields_unknown_string PASSED [ 19%]
tests/test_proc.py::test_missing_file_raises_filenotfound PASSED         [ 22%]
tests/test_proc.py::test_tcp6_basic_parses_listen_and_established PASSED [ 25%]
tests/test_proc.py::test_tcp6_loopback_is_compressed PASSED              [ 29%]
tests/test_proc.py::test_tcp6_malformed_rows_skipped PASSED              [ 32%]
tests/test_proc.py::test_udp4_basic_parses_close_and_established PASSED  [ 35%]
tests/test_proc.py::test_udp4_close_state_is_07 PASSED                   [ 38%]
tests/test_proc.py::test_udp6_basic_parses_sockets PASSED                [ 41%]
tests/test_proc.py::test_read_all_combines_all_protocols PASSED          [ 45%]
tests/test_proc.py::test_read_all_survives_missing_file PASSED           [ 48%]
tests/test_process.py::test_build_inode_map_finds_socket_inodes PASSED   [ 51%]
tests/test_process.py::test_build_inode_map_skips_permission_error PASSED [ 54%]
tests/test_process.py::test_resolve_pid_full_info PASSED                 [ 58%]
tests/test_process.py::test_resolve_pid_missing_exe PASSED               [ 61%]
tests/test_process.py::test_resolve_pid_username_fallback PASSED         [ 64%]
tests/test_process.py::test_resolve_inode_found PASSED                   [ 67%]
tests/test_process.py::test_resolve_inode_not_found PASSED               [ 70%]
tests/test_process.py::test_resolve_inodes_batch PASSED                  [ 74%]
tests/test_process.py::test_cmdline_null_bytes_replaced PASSED           [ 77%]
tests/test_snapshot.py::test_take_snapshot_joins_socket_and_process PASSED [ 80%]
tests/test_snapshot.py::test_take_snapshot_unresolved_process_is_none PASSED [ 83%]
tests/test_snapshot.py::test_take_snapshot_multiple_protocols PASSED     [ 87%]
tests/test_snapshot.py::test_take_snapshot_empty_system PASSED           [ 90%]
tests/test_snapshot.py::test_take_snapshot_preserves_order PASSED        [ 93%]
tests/test_snapshot.py::test_convenience_properties PASSED               [ 96%]
tests/test_snapshot.py::test_read_all_accepts_proc_root PASSED           [100%]

============================== 31 passed in 0.10s
```

`portwatch --dump` first 10 lines (via `from portwatch.cli import main; main(['--dump'])`):

```text

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
```

`python3 -c "from portwatch.snapshot import take_snapshot, PortRecord; s=take_snapshot(); print(len(s), type(s[0]) if s else 'no-records')"` output:

```text
119
<class 'portwatch.snapshot.PortRecord'>
```

`portwatch --version` output:

```text
portwatch 0.0.1
```

tests/test_process.py — imports + example test using `fake_proc` fixture:

```python
import os
import stat
import pwd
import shutil
import logging
from pathlib import Path

import pytest


from tests.conftest import fake_proc  # type: ignore


def test_build_inode_map_finds_socket_inodes(fake_proc):
	from portwatch.process import _build_inode_map

	pids = [
		{
			"pid": 100,
			"comm": "proc100",
			"exe": "/bin/proc100",
			"cmdline": "proc100",
			"uid": 1000,
			"fds": [{"fd_num": 3, "target": "socket:[111]"}, {"fd_num": 4, "target": "pipe:[222]"}],
		},
	]
	root = fake_proc(pids)
	m = _build_inode_map(root)
	assert m[111] == 100
	assert 222 not in m
```



