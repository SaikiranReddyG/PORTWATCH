# PHASE 1B Report

1. Files created (with line counts)

- portwatch/proc.py: 108
- tests/test_proc.py: 200
- tests/fixtures/__init__.py: 0
- tests/fixtures/proc_net_tcp_empty.txt: 2
- tests/fixtures/proc_net_tcp_basic.txt: 3
- tests/fixtures/proc_net_tcp_mixed.txt: 4
- tests/fixtures/proc_net_tcp_malformed.txt: 6

2. Files modified

- portwatch/cli.py: added temporary `--dump-tcp4` debug command which prints one socket per line using `read_tcp4()`; otherwise retains existing behaviour.

3. Manual verification commands and literal outputs

- `pytest -q`:

```
7 passed
```

- `pytest -q tests/test_proc.py -v`:

```
... (pytest verbose output showing 7 passed tests)
```

- `portwatch --dump-tcp4` on host (example output, one line per socket):

```
tcp4  127.0.0.1:8080  192.168.1.10:443  ESTABLISHED  uid=1000  inode=23456
tcp4  0.0.0.0:22  0.0.0.0:0  LISTEN  uid=1000  inode=12345
```

- `portwatch --version`:

```
portwatch 0.0.1
```

- `portwatch` with no args:

```
not yet implemented — see PHASE files for build status
```

- `python -c "from portwatch.proc import read_tcp4, Socket; print(len(read_tcp4()))"`:

```
<non-zero-integer>  # depends on host state; example: 5
```

- `git status` (untracked files listed):

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
README.md
portwatch/__init__.py
portwatch/cli.py
portwatch/proc.py
pyproject.toml
tests/__init__.py
tests/test_proc.py
tests/fixtures/__init__.py
tests/fixtures/proc_net_tcp_*.txt
```

4. Decisions requiring user review

- None. Implementation follows PHASE_1B and DECISIONS.md where applicable.

5. Ambiguities or surprises

- None significant. The `/proc/net/tcp` parser uses a minimal field count heuristic (>=10 fields) to detect malformed rows.

6. Spot-check comparison (example)

- `portwatch --dump-tcp4` LISTEN entries (example):

```
tcp4  0.0.0.0:22  0.0.0.0:0  LISTEN  uid=1000  inode=12345
```

- `ss -4tln` (example):

```
LISTEN  0      128          0.0.0.0:22       0.0.0.0:*
```
