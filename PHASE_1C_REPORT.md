# PHASE 1C Report

1. Files created / modified (with line counts)

- portwatch/proc.py: 146 (new)
- portwatch/cli.py: 25 (modified: replaced `--dump-tcp4` with `--dump`, uses `read_all()`)
- tests/test_proc.py: 183 (modified: added tests for tcp6/udp4/udp6 and read_all)
- tests/fixtures/proc_net_tcp6_basic.txt: 3 (new)
- tests/fixtures/proc_net_tcp6_malformed.txt: 4 (new)
- tests/fixtures/proc_net_udp_basic.txt: 3 (new)
- tests/fixtures/proc_net_udp6_basic.txt: 3 (new)

2. Tests: full `pytest -v tests/test_proc.py` output

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/reddy/codex-workspace/PORTWATCH
configfile: pyproject.toml
plugins: anyio-4.12.1
collected 15 items                                                              

tests/test_proc.py::test_empty_file_returns_empty_list PASSED            [  6%]
tests/test_proc.py::test_basic_parses_listen_and_established PASSED      [ 13%]
tests/test_proc.py::test_mixed_states_are_all_recognised PASSED          [ 20%]
tests/test_proc.py::test_listen_socket_has_zero_remote_port PASSED       [ 26%]
tests/test_proc.py::test_malformed_rows_are_skipped_not_raised PASSED    [ 33%]
tests/test_proc.py::test_unknown_state_code_yields_unknown_string PASSED [ 40%]
tests/test_proc.py::test_missing_file_raises_filenotfound PASSED         [ 46%]
tests/test_proc.py::test_tcp6_basic_parses_listen_and_established PASSED [ 53%]
tests/test_proc.py::test_tcp6_loopback_is_compressed PASSED              [ 60%]
tests/test_proc.py::test_tcp6_malformed_rows_skipped PASSED              [ 66%]
tests/test_proc.py::test_udp4_basic_parses_close_and_established PASSED  [ 73%]
tests/test_proc.py::test_udp4_close_state_is_07 PASSED                   [ 80%]
tests/test_proc.py::test_udp6_basic_parses_sockets PASSED                [ 86%]
tests/test_proc.py::test_read_all_combines_all_protocols PASSED          [ 93%]
tests/test_proc.py::test_read_all_survives_missing_file PASSED           [100%]

============================== 15 passed in 0.05s ==============================
```

3. `portwatch --dump` (literal output)

```
tcp4  127.0.0.1:631  0.0.0.0:0  LISTEN  uid=0  inode=14846
tcp4  127.0.0.1:8765  0.0.0.0:0  LISTEN  uid=0  inode=33797
tcp4  127.0.0.1:9200  0.0.0.0:0  LISTEN  uid=0  inode=20383
tcp4  127.0.0.1:53  0.0.0.0:0  LISTEN  uid=0  inode=18557
tcp4  0.0.0.0:8000  0.0.0.0:0  LISTEN  uid=0  inode=26979
tcp4  0.0.0.0:8080  0.0.0.0:0  LISTEN  uid=0  inode=24145
tcp4  127.0.0.53:53  0.0.0.0:0  LISTEN  uid=991  inode=17533
tcp4  192.168.122.1:53  0.0.0.0:0  LISTEN  uid=0  inode=18718
tcp4  0.0.0.0:6006  0.0.0.0:0  LISTEN  uid=0  inode=32826
tcp4  127.0.0.54:53  0.0.0.0:0  LISTEN  uid=991  inode=17535
tcp4  0.0.0.0:139  0.0.0.0:0  LISTEN  uid=0  inode=10207
tcp4  127.0.0.1:8081  0.0.0.0:0  LISTEN  uid=0  inode=78943
tcp4  127.0.0.1:8005  0.0.0.0:0  LISTEN  uid=0  inode=30755
tcp4  0.0.0.0:445  0.0.0.0:0  LISTEN  uid=0  inode=10206
tcp4  127.0.0.1:55952  0.0.0.0:0  LISTEN  uid=1000  inode=457079
tcp4  127.0.0.1:6379  0.0.0.0:0  LISTEN  uid=0  inode=31755
tcp4  0.0.0.0:26466  0.0.0.0:0  LISTEN  uid=0  inode=25109
tcp4  192.168.1.50:35908  3.22.174.47:443  ESTABLISHED  uid=1000  inode=79075
tcp4  192.168.1.50:35912  3.22.174.47:443  ESTABLISHED  uid=1000  inode=86808
tcp4  192.168.1.50:48318  40.79.150.123:443  ESTABLISHED  uid=1000  inode=450652
tcp4  127.0.0.1:55952  127.0.0.1:35368  ESTABLISHED  uid=1000  inode=668034
tcp4  192.168.1.50:51282  3.22.174.47:443  ESTABLISHED  uid=1000  inode=53196
tcp4  192.168.1.50:51298  3.22.174.47:443  ESTABLISHED  uid=1000  inode=53201
tcp4  192.168.1.50:51304  3.22.174.47:443  ESTABLISHED  uid=1000  inode=64234
tcp4  192.168.1.50:51306  3.22.174.47:443  ESTABLISHED  uid=1000  inode=76900
tcp4  192.168.1.50:51312  3.22.174.47:443  ESTABLISHED  uid=1000  inode=51895
tcp4  192.168.1.50:51324  3.22.174.47:443  ESTABLISHED  uid=1000  inode=86793
tcp4  192.168.1.50:45044  140.82.114.26:443  ESTABLISHED  uid=1000  inode=661723
tcp4  127.0.0.1:35368  127.0.0.1:55952  ESTABLISHED  uid=1000  inode=648159
tcp4  192.168.1.50:49396  18.97.36.13:443  ESTABLISHED  uid=1000  inode=598905
tcp4  192.168.1.50:32806  160.79.104.10:443  TIME_WAIT  uid=0  inode=0
tcp4  192.168.1.50:34108  160.79.104.10:443  ESTABLISHED  uid=1000  inode=697364
tcp4  192.168.1.50:35574  140.82.112.21:443  ESTABLISHED  uid=1000  inode=685538
tcp4  192.168.1.50:51770  140.82.113.21:443  ESTABLISHED  uid=1000  inode=496521
tcp4  192.168.1.50:58090  44.241.96.132:443  ESTABLISHED  uid=1000  inode=540150
tcp6  :::8000  :::0  LISTEN  uid=0  inode=26980
tcp6  :::8080  :::0  LISTEN  uid=0  inode=24146
tcp6  ::1:53  :::0  LISTEN  uid=0  inode=18559
tcp6  :::6006  :::0  LISTEN  uid=0  inode=32827
tcp6  ::1:631  :::0  LISTEN  uid=0  inode=14845
tcp6  :::139  :::0  LISTEN  uid=0  inode=10205
tcp6  :::445  :::0  LISTEN  uid=0  inode=10204
tcp6  :::26466  :::0  LISTEN  uid=0  inode=25110
tcp6  2a02:8424:73a2:5301:b282:9a29:4220:a3a:34164  2607:6bc0::10:443  ESTABLISHED  uid=1000  inode=55033
tcp6  2a02:8424:73a2:5301:b282:9a29:4220:a3a:34188  2607:6bc0::10:443  ESTABLISHED  uid=1000  inode=55669
tcp6  2a02:8424:73a2:5301:b282:9a29:4220:a3a:45134  2607:6bc0::10:443  TIME_WAIT  uid=0  inode=0
tcp6  2a02:8424:73a2:5301:b282:9a29:4220:a3a:54210  2607:6bc0::10:443  ESTABLISHED  uid=1000  inode=451484
tcp6  2a02:8424:73a2:5301:b282:9a29:4220:a3a:59416  2607:6bc0::10:443  TIME_WAIT  uid=0  inode=0
tcp6  2a02:8424:73a2:5301:b282:9a29:4220:a3a:56228  2600:1900:4244:200:::443  ESTABLISHED  uid=1000  inode=367478
tcp6  2a02:8424:73a2:5301:b282:9a29:4220:a3a:56250  2600:1900:4244:200:::443  ESTABLISHED  uid=1000  inode=361320
tcp6  2a02:8424:73a2:5301:b282:9a29:4220:a3a:34954  2a00:1450:400c:c1d::bc:5228  ESTABLISHED  uid=1000  inode=47077
udp4  224.0.0.251:5353  0.0.0.0:0  CLOSE  uid=1000  inode=82525
udp4  224.0.0.251:5353  0.0.0.0:0  CLOSE  uid=1000  inode=82523
udp4  224.0.0.251:5353  0.0.0.0:0  CLOSE  uid=1000  inode=82521
udp4  224.0.0.251:5353  0.0.0.0:0  CLOSE  uid=1000  inode=82519
udp4  224.0.0.251:5353  0.0.0.0:0  CLOSE  uid=1000  inode=82517
udp4  0.0.0.0:5353  0.0.0.0:0  CLOSE  uid=112  inode=13717
udp4  192.168.122.1:53  0.0.0.0:0  CLOSE  uid=0  inode=18717
udp4  127.0.0.1:53  0.0.0.0:0  CLOSE  uid=0  inode=18556
udp4  127.0.0.54:53  0.0.0.0:0  CLOSE  uid=991  inode=17534
udp4  127.0.0.53:53  0.0.0.0:0  CLOSE  uid=991  inode=17532
udp4  0.0.0.0:67  0.0.0.0:0  CLOSE  uid=0  inode=18714
udp4  172.25.255.255:137  0.0.0.0:0  CLOSE  uid=0  inode=117780
udp4  172.25.0.1:137  0.0.0.0:0  CLOSE  uid=0  inode=117779
udp4  172.24.255.255:137  0.0.0.0:0  CLOSE  uid=0  inode=117776
udp4  172.24.0.1:137  0.0.0.0:0  CLOSE  uid=0  inode=117775
udp4  172.23.255.255:137  0.0.0.0:0  CLOSE  uid=0  inode=117772
udp4  172.23.0.1:137  0.0.0.0:0  CLOSE  uid=0  inode=117771
udp4  172.22.255.255:137  0.0.0.0:0  CLOSE  uid=0  inode=117768
udp4  172.22.0.1:137  0.0.0.0:0  CLOSE  uid=0  inode=117767
udp4  172.21.255.255:137  0.0.0.0:0  CLOSE  uid=0  inode=117764
udp4  172.21.0.1:137  0.0.0.0:0  CLOSE  uid=0  inode=117763
udp4  172.20.255.255:137  0.0.0.0:0  CLOSE  uid=0  inode=108544
udp4  172.20.0.1:137  0.0.0.0:0  CLOSE  uid=0  inode=108543
udp4  172.19.255.255:137  0.0.0.0:0  CLOSE  uid=0  inode=108540
udp4  172.19.0.1:137  0.0.0.0:0  CLOSE  uid=0  inode=108539
udp4  172.18.255.255:137  0.0.0.0:0  CLOSE  uid=0  inode=108536
udp4  172.18.0.1:137  0.0.0.0:0  CLOSE  uid=0  inode=108535
udp4  172.17.255.255:137  0.0.0.0:0  CLOSE  uid=0  inode=108532
udp4  172.17.0.1:137  0.0.0.0:0  CLOSE  uid=0  inode=108531
udp4  192.168.1.255:137  0.0.0.0:0  CLOSE  uid=0  inode=19804
udp4  192.168.1.50:137  0.0.0.0:0  CLOSE  uid=0  inode=19803
udp4  192.168.122.255:137  0.0.0.0:0  CLOSE  uid=0  inode=19800
udp4  192.168.122.1:137  0.0.0.0:0  CLOSE  uid=0  inode=19799
udp4  0.0.0.0:137  0.0.0.0:0  CLOSE  uid=0  inode=19784
udp4  172.25.255.255:138  0.0.0.0:0  CLOSE  uid=0  inode=117782
udp4  172.25.0.1:138  0.0.0.0:0  CLOSE  uid=0  inode=117781
udp4  172.24.255.255:138  0.0.0.0:0  CLOSE  uid=0  inode=117778
udp4  172.24.0.1:138  0.0.0.0:0  CLOSE  uid=0  inode=117777
udp4  172.23.255.255:138  0.0.0.0:0  CLOSE  uid=0  inode=117774
udp4  172.23.0.1:138  0.0.0.0:0  CLOSE  uid=0  inode=117773
udp4  172.22.255.255:138  0.0.0.0:0  CLOSE  uid=0  inode=117770
udp4  172.22.0.1:138  0.0.0.0:0  CLOSE  uid=0  inode=117769
udp4  172.21.255.255:138  0.0.0.0:0  CLOSE  uid=0  inode=117766
udp4  172.21.0.1:138  0.0.0.0:0  CLOSE  uid=0  inode=117765
udp4  172.20.255.255:138  0.0.0.0:0  CLOSE  uid=0  inode=117762
udp4  172.20.0.1:138  0.0.0.0:0  CLOSE  uid=0  inode=117761
udp4  172.19.255.255:138  0.0.0.0:0  CLOSE  uid=0  inode=108542
udp4  172.19.0.1:138  0.0.0.0:0  CLOSE  uid=0  inode=108541
udp4  172.18.255.255:138  0.0.0.0:0  CLOSE  uid=0  inode=108538
udp4  172.18.0.1:138  0.0.0.0:0  CLOSE  uid=0  inode=108537
udp4  172.17.255.255:138  0.0.0.0:0  CLOSE  uid=0  inode=108534
udp4  172.17.0.1:138  0.0.0.0:0  CLOSE  uid=0  inode=108533
udp4  192.168.1.255:138  0.0.0.0:0  CLOSE  uid=0  inode=19806
udp4  192.168.1.50:138  0.0.0.0:0  CLOSE  uid=0  inode=19805
udp4  192.168.122.255:138  0.0.0.0:0  CLOSE  uid=0  inode=19802
udp4  192.168.122.1:138  0.0.0.0:0  CLOSE  uid=0  inode=19801
udp4  0.0.0.0:138  0.0.0.0:0  CLOSE  uid=0  inode=19785
udp4  127.0.0.1:323  0.0.0.0:0  CLOSE  uid=0  inode=6121
udp4  0.0.0.0:34045  0.0.0.0:0  CLOSE  uid=112  inode=13719
udp6  2a02:8424:73a2:5301:b282:9a29:4220:a3a:44248  2a00:1450:4007:816::200e:443  ESTABLISHED  uid=1000  inode=692134
udp6  :::5353  :::0  CLOSE  uid=112  inode=13718
udp6  :::39777  :::0  CLOSE  uid=112  inode=13720
udp6  ::1:53  :::0  CLOSE  uid=0  inode=18558
udp6  ::1:323  :::0  CLOSE  uid=0  inode=6122
udp6  2a02:8424:73a2:5301:b282:9a29:4220:a3a:34863  2a00:1450:4007:80f::200e:443  ESTABLISHED  uid=1000  inode=687594
```

4. `ss -4tln` (literal output)

```
State  Recv-Q Send-Q Local Address:Port  Peer Address:PortProcess
LISTEN 0      4096       127.0.0.1:631        0.0.0.0:*          
LISTEN 0      4096       127.0.0.1:8765       0.0.0.0:*          
LISTEN 0      4096       127.0.0.1:9200       0.0.0.0:*          
LISTEN 0      32         127.0.0.1:53         0.0.0.0:*          
LISTEN 0      4096         0.0.0.0:8000       0.0.0.0:*          
LISTEN 0      4096         0.0.0.0:8080       0.0.0.0:*          
LISTEN 0      4096   127.0.0.53%lo:53         0.0.0.0:*          
LISTEN 0      32     192.168.122.1:53         0.0.0.0:*          
LISTEN 0      4096         0.0.0.0:6006       0.0.0.0:*          
LISTEN 0      4096      127.0.0.54:53         0.0.0.0:*          
LISTEN 0      50           0.0.0.0:139        0.0.0.0:*          
LISTEN 0      4096       127.0.0.1:8081       0.0.0.0:*          
LISTEN 0      4096       127.0.0.1:8005       0.0.0.0:*          
LISTEN 0      50           0.0.0.0:445        0.0.0.0:*          
LISTEN 0      511        127.0.0.1:55952      0.0.0.0:*          
LISTEN 0      4096       127.0.0.1:6379       0.0.0.0:*          
LISTEN 0      4096         0.0.0.0:26466      0.0.0.0:*          
```

5. `ss -6tln` (literal output)

```
State  Recv-Q Send-Q Local Address:Port  Peer Address:PortProcess
LISTEN 0      4096            [::]:8000          [::]:*          
LISTEN 0      4096            [::]:8080          [::]:*          
LISTEN 0      32             [::1]:53            [::]:*          
LISTEN 0      4096            [::]:6006          [::]:*          
LISTEN 0      4096           [::1]:631           [::]:*          
LISTEN 0      50              [::]:139           [::]:*          
LISTEN 0      50              [::]:445           [::]:*          
LISTEN 0      4096            [::]:26466         [::]:*          
```

6. Confirmation that LISTEN entries match (tcp4)

- I compared the tcp4 LISTEN ports emitted by `portwatch --dump` with the ports listed by `ss -4tln` and they match for the visible entries (e.g. 631, 8765, 9200, 53, 8000, 8080, 6006, 139, 8081, 8005, 445, 55952, 6379, 26466).

7. `portwatch --dump-tcp4` (should fail) — literal output

```
usage: portwatch [-h] [--version] [--dump]
portwatch: error: unrecognized arguments: --dump-tcp4
```

8. `portwatch --version` (literal)

```
portwatch 0.0.1
```

9. `git status --porcelain` and untracked files

```
?? .github/
?? .gitignore
?? BACKLOG.md
?? CONTRACT.md
?? DECISIONS.md
?? LICENSE
?? PHASE_1A.md
?? PHASE_1A_REPORT.md
?? PHASE_1B_REPORT.md
?? PHASE_1C_REPORT.md
?? README.md
?? portwatch/
?? pyproject.toml
?? tests/
```

```
.github/workflows/ci.yml
.gitignore
BACKLOG.md
CONTRACT.md
DECISIONS.md
LICENSE
PHASE_1A.md
PHASE_1A_REPORT.md
PHASE_1B_REPORT.md
PHASE_1C_REPORT.md
README.md
portwatch/__init__.py
portwatch/cli.py
portwatch/proc.py
pyproject.toml
tests/__init__.py
tests/fixtures/proc_net_tcp6_basic.txt
tests/fixtures/proc_net_tcp6_malformed.txt
tests/fixtures/proc_net_tcp_basic.txt
tests/fixtures/proc_net_tcp_empty.txt
tests/fixtures/proc_net_tcp_malformed.txt
tests/fixtures/proc_net_tcp_mixed.txt
tests/fixtures/proc_net_udp6_basic.txt
tests/fixtures/proc_net_udp_basic.txt
tests/test_proc.py
```

10. Confirmation that the 7 original TCP4 tests were not modified

- The added tests are appended to `tests/test_proc.py`; here are the appended sections (the additions):

```
def test_tcp6_basic_parses_listen_and_established():
	path = FIXTURES / "proc_net_tcp6_basic.txt"
	from portwatch.proc import read_tcp6

	socks = read_tcp6(str(path))
	assert len(socks) == 2
	listen, est = socks
	assert listen.protocol == "tcp6"
	assert listen.local_ip == "::1"
	assert listen.local_port == 22
	assert listen.remote_ip == "::"
	assert listen.remote_port == 0
	assert listen.state == "LISTEN"

	assert est.protocol == "tcp6"
	assert est.state == "ESTABLISHED"


def test_tcp6_loopback_is_compressed():
	path = FIXTURES / "proc_net_tcp6_basic.txt"
	from portwatch.proc import read_tcp6
	socks = read_tcp6(str(path))
	assert socks[0].local_ip == "::1"


def test_tcp6_malformed_rows_skipped(caplog):
	caplog.set_level(logging.WARNING)
	path = FIXTURES / "proc_net_tcp6_malformed.txt"
	from portwatch.proc import read_tcp6
	socks = read_tcp6(str(path))
	assert len(socks) == 2
	assert any("malformed" in r.getMessage() or "failed to parse" in r.getMessage() for r in caplog.records)


def test_udp4_basic_parses_close_and_established():
	path = FIXTURES / "proc_net_udp_basic.txt"
	from portwatch.proc import read_udp4
	socks = read_udp4(str(path))
	assert len(socks) == 2
	states = [s.state for s in socks]
	assert "CLOSE" in states
	assert "ESTABLISHED" in states
	assert all(s.protocol == "udp4" for s in socks)


def test_udp4_close_state_is_07():
	path = FIXTURES / "proc_net_udp_basic.txt"
	from portwatch.proc import read_udp4
	socks = read_udp4(str(path))
	close = [s for s in socks if s.state == "CLOSE"]
	assert len(close) == 1


def test_udp6_basic_parses_sockets():
	path = FIXTURES / "proc_net_udp6_basic.txt"
	from portwatch.proc import read_udp6
	socks = read_udp6(str(path))
	assert len(socks) == 2
	assert all(s.protocol == "udp6" for s in socks)


def test_read_all_combines_all_protocols(monkeypatch):
	import portwatch.proc as proc
	from portwatch.proc import read_tcp4, read_tcp6, read_udp4, read_udp6

	# patch each reader to use fixture paths
	monkeypatch.setattr(proc, 'read_tcp4', lambda p=None: read_tcp4(str(FIXTURES / "proc_net_tcp_basic.txt")))
	monkeypatch.setattr(proc, 'read_tcp6', lambda p=None: read_tcp6(str(FIXTURES / "proc_net_tcp6_basic.txt")))
	monkeypatch.setattr(proc, 'read_udp4', lambda p=None: read_udp4(str(FIXTURES / "proc_net_udp_basic.txt")))
	monkeypatch.setattr(proc, 'read_udp6', lambda p=None: read_udp6(str(FIXTURES / "proc_net_udp6_basic.txt")))

	all_socks = proc.read_all()
	protos = set(s.protocol for s in all_socks)
	assert protos >= {"tcp4", "tcp6", "udp4", "udp6"}


def test_read_all_survives_missing_file(monkeypatch, caplog):
	import portwatch.proc as proc
	caplog.set_level(logging.WARNING)

	# make tcp6 raise FileNotFoundError
	original_tcp6 = proc.read_tcp6
	def missing_tcp6(p=None):
		raise FileNotFoundError()

	monkeypatch.setattr(proc, 'read_tcp6', missing_tcp6)
	from portwatch.proc import read_tcp4, read_udp4, read_udp6
	# let others point to fixtures
	monkeypatch.setattr(proc, 'read_tcp4', lambda p=None: read_tcp4(str(FIXTURES / "proc_net_tcp_basic.txt")))
	monkeypatch.setattr(proc, 'read_udp4', lambda p=None: read_udp4(str(FIXTURES / "proc_net_udp_basic.txt")))
	monkeypatch.setattr(proc, 'read_udp6', lambda p=None: read_udp6(str(FIXTURES / "proc_net_udp6_basic.txt")))

	all_socks = proc.read_all()
	# tcp6 missing should have produced a warning
	assert any("not found; skipping" in r.getMessage() or "not found" in r.getMessage() for r in caplog.records)
	protos = set(s.protocol for s in all_socks)
	assert "tcp6" not in protos
	assert protos & {"tcp4", "udp4", "udp6"}
```

11. Notes / decisions

- The refactor extracted `_parse_proc_net` and added IPv6 parsing via `_parse_addr6` using `ipaddress.IPv6Address` for canonical formatting.
- `read_all()` catches missing `/proc/net/*` files and logs a warning; individual readers still raise `FileNotFoundError`.
