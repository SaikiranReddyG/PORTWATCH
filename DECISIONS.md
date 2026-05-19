# DECISIONS.md

Locked architectural and design choices for **portwatch**.

This document is the source of truth for *what was decided and why*. The maintaining agent must not deviate from these decisions without explicit approval. If a decision needs to change, update this file first, then the code — never the other way around.

Decisions deferred to later versions live in `BACKLOG.md`, not here.

---

## 1. Identity & Scope

### 1.1 What portwatch is
A terminal-native, real-time port and socket visualiser for Linux. It renders the host's network surface as a microcontroller-style chip diagram, where each active port is a pin with state expressed through symbols and colour.

### 1.2 What portwatch is NOT
- Not a packet sniffer (no libpcap, no eBPF, no traffic byte counters in v1)
- Not a firewall (does not write nftables/iptables rules)
- Not a vulnerability scanner
- Not a long-term forensics tool (no persistent history)

If a feature request fits any of the above, it belongs in `BACKLOG.md` or a different repo.

### 1.3 Repo
- Name: `portwatch`
- Binary: `portwatch` (no short alias)
- Visibility: public on GitHub from Phase 1
- License: MIT

---

## 2. Runtime Model

### 2.1 Execution
- Foreground CLI process invoked by the user in a terminal
- Installed via `pipx install portwatch`
- Single `.env` for configuration (matches pulse-platform convention)
- One command to install, one command to run — same launch philosophy as pulse-platform
- No daemon mode, no headless mode, no Docker in v1 (deferred to `BACKLOG.md`)

### 2.2 Permissions
- Runs as the invoking user
- Without root: full socket listing, but process names show `???` for sockets owned by other users
- Detect root at startup; display the privilege level in the UI status bar
- Never attempt privilege escalation

### 2.3 Poll interval
- 2 seconds, configurable via `.env` (`PORTWATCH_POLL_INTERVAL=2`)
- The 2-second cadence governs UI refresh, diff generation, and event emission

---

## 3. Data Layer

### 3.1 Sources parsed
- `/proc/net/tcp`
- `/proc/net/tcp6`
- `/proc/net/udp`
- `/proc/net/udp6`

Unix sockets, raw sockets, and netlink sockets are out of scope.

### 3.2 Process resolution
- `/proc/PID/exe` for binary path
- `/proc/PID/cmdline` for invocation
- `/proc/PID/status` for UID
- Missing or permission-denied reads degrade to a `???` placeholder; never crash

### 3.3 State storage
- **In-memory only**
- The "previous snapshot" lives in a Python dict, lost on restart
- Baseline rebuilds during the first 60 seconds after start (see §4.2)
- No SQLite, no JSON state file, no `~/.portwatch/` directory in v1
- Rationale: nothing on disk means nothing to corrupt, nothing to migrate, nothing to gitignore

### 3.4 Parser error handling
- Log-and-skip: malformed lines are logged at WARN level and skipped
- A running counter of parse errors is displayed in the UI status bar
- The tool never crashes on a malformed `/proc` line

---

## 4. Suspicious Heuristic (v1)

### 4.1 Rules
Exactly three rules ship in v1. No more, no less.

1. **Unknown LISTEN** — a process opens a LISTEN socket on a port that this session has never seen that process listen on before
2. **Unexpected outbound** — a process establishes an outbound connection to a non-RFC1918 address, when that process has only ever connected locally before
3. **Suspicious binary path** — the listening process's binary lives in `/tmp/`, `/dev/shm/`, or `/var/tmp/`

Additional heuristics are tracked in `BACKLOG.md`.

### 4.2 Learning mode (baseline)
- For the first 60 seconds after startup, every observation is treated as "known" and added to the trust set
- After the 60-second warm-up, deltas from the baseline trigger the suspicious rules
- Baseline is in-memory; resets on restart

### 4.3 False-positive handling
- Press `d` to dismiss the current flag for the remainder of this session
- Dismissals do not persist across restarts (matches in-memory state policy)
- No "always trust" persistent whitelist in v1

---

## 5. UI

### 5.1 Framework
- Textual (Python TUI)
- Rich for the chip widget's `render()`

### 5.2 Layout
- Chip-shaped diagram, pins on left and right edges, body in the middle showing aggregate counts
- **Pin slot assignment**: on app start, slots are assigned sorted by port number (datasheet-style pinout). After startup, slots are *sticky* — a port keeps its slot until it has been gone for 30 seconds, then the slot is reclaimable
- Active pins render bright; recently-closed pins render dim; never-used slots render as `····`

### 5.3 Symbols (load-bearing — colour is decorative)
- `●` LISTEN, healthy
- `◐` ESTABLISHED, active
- `◯` known port, currently closed
- `▲` busy / high traffic (deferred; placeholder symbol reserved)
- `✕` suspicious
- `▒` blocked by firewall (deferred; placeholder symbol reserved)

Meaning is carried by the symbol so the UI remains usable in monochrome terminals and for users with red/green colour blindness.

### 5.4 Palette
- Hacker aesthetic: green / cyan / yellow / red on a dim grey background
- ASCII-leaning box characters
- No rounded corners, no gradients, no animations beyond a single blink on freshly-opened ports

### 5.5 Terminal size
- Minimum 80 cols × 24 rows
- Below minimum: render a polite "portwatch needs at least 80×24" message and exit cleanly
- Above 120 cols: detail panel appears on the right by default
- On resize: relayout happens on the next poll tick (not immediately) to avoid jitter

### 5.6 Empty / loading state
- All pin slots render as `····` with a `LOADING` banner until the first poll completes

### 5.7 Keybindings (v1)
- Arrow keys — move focus between pins
- `Enter` — open detail panel for focused pin
- `d` — dismiss the suspicious flag on focused pin for this session
- `/` — search by port or process name
- `f` — filter view (cycles: all → suspicious → LISTEN → foreign)
- `q` or `Ctrl+C` — exit (prints session summary)

Kill (`k`) and block (`b`) are deferred to `BACKLOG.md`.

### 5.8 Exit summary
On `q` or `Ctrl+C`, print to stdout:
- Total runtime
- Peak port count
- Number of suspicious flags raised
- Parse-error count

---

## 6. Pulse Integration

### 6.1 Toggle
- Controlled by `PULSE_ENABLED=true|false` in `.env`
- Default: `false` (standalone mode is the default)
- When disabled, no network code runs; portwatch is fully self-contained

### 6.2 Configuration
- `PULSE_ENDPOINT` — full URL to the pulse `/events` endpoint
- `PULSE_TOKEN` — bearer token for receiver auth
- Both required when `PULSE_ENABLED=true`; portwatch refuses to start otherwise

### 6.3 Transport
- HTTP POST to `PULSE_ENDPOINT` using `httpx`
- All HTTP calls happen in a single daemon thread
- 2-second timeout per request
- Bounded queue, max 100 events; overflow drops oldest events silently
- The TUI never blocks on a Pulse call and never displays a Pulse error

### 6.4 Batching
- 500 ms aggregation window
- One POST per window, with an array body conforming to pulse's `/events` contract
- If the window is empty, no POST is made

### 6.5 Event ID format
```
portwatch-<sha1(hostname + port + pid + state)[:12]>-<unix_minute>
```
- The minute suffix permits legitimate re-emission across minutes
- The hash de-duplicates within a minute
- Forward-compatible: new event_types add new payload fields, not new ID schemes

### 6.6 Severity mapping
| Condition                                                       | Severity   |
|-----------------------------------------------------------------|------------|
| New LISTEN by a known process                                   | `info`     |
| New ESTABLISHED outbound by a known process                     | `info`     |
| New LISTEN by an unknown process (post-baseline)                | `high`     |
| ESTABLISHED to non-RFC1918 by previously-local-only process     | `high`     |
| Binary in `/tmp`, `/dev/shm`, or `/var/tmp` opens a LISTEN port | `critical` |

### 6.7 Event types emitted (v1)
- `portwatch.port_opened`
- `portwatch.port_closed`
- `portwatch.connection_established`
- `portwatch.suspicious_flagged`

### 6.8 Isolation
- A Pulse outage must not affect the standalone TUI in any visible way
- A portwatch crash must not affect Pulse
- Coupling is exclusively through the event schema in `CONTRACT.md`

---

## 7. UI Sharing (Pulse Embedding)

### 7.1 Package shape
```
portwatch/
├── core/        # poll, parse, diff — pure logic, no UI imports
├── widgets/     # ChipWidget, DetailPanel — Textual widgets, no I/O
├── app.py       # standalone Textual app
└── pulse_panel.py
```

### 7.2 Widget contract
- `ChipWidget` accepts a data source object implementing `get_snapshot() -> PortSnapshot`
- Standalone mode feeds it from the live poller
- Pulse mode feeds it from a SQLite read of the pulse database
- The widget itself is unaware of which mode it is in

### 7.3 Dependency direction
- portwatch is an **optional** dependency of pulse-platform
- Pulse's dashboard imports `ChipWidget` inside a `try/except ImportError` block
- If portwatch is not installed, Pulse renders a "portwatch widget unavailable" placeholder and continues running
- A portwatch package failure must never bring down the Pulse dashboard

---

## 8. Testing

### 8.1 Policy
- Every parser, joiner, diff, and heuristic ships with unit tests in the same phase that introduces it
- UI rendering and live `/proc` reads are verified manually; each phase document includes a "manual verification" checklist
- CI runs tests on Python 3.11 and 3.12

### 8.2 Test layout
- Tests live in `tests/` mirroring the `portwatch/` package structure
- `pytest` is the runner
- Fixtures provide synthetic `/proc/net/tcp` content so the parser tests do not touch the host

---

## 9. Project Discipline

### 9.1 Phase boundaries
Development proceeds through small, ordered phases. Each phase is specified in its own `PHASE_*.md` file and produces a runnable, testable artefact. The agent works on one phase at a time and does not begin the next until the previous is verified.

### 9.2 BACKLOG.md
Any feature, refinement, or "wouldn't it be nice if" idea that is not in the current phase goes to `BACKLOG.md`. The agent must not implement backlog items unless explicitly promoted into a phase.

### 9.3 Repo files
The following files live in the repo and are visible publicly:
- `README.md` — portfolio-grade overview
- `DECISIONS.md` — this document
- `BACKLOG.md` — deferred features
- `CONTRACT.md` — event schema (for Pulse integration)
- `PHASE_*.md` — phase-by-phase build plans
- `CHANGELOG.md` — created when the first tag ships

Internal scratch notes are kept out of the repo entirely (not gitignored — never added).

### 9.4 Commit hygiene
- Conventional commits format
- One logical change per commit
- The agent does not amend commits authored by the user

---

## 10. Versioning

- Semantic versioning, starting from `0.1.0` when Phase 1 lands
- No tag, no release, no `pyproject.toml` version bump until the data layer is stable and tested
- Versioning is not in scope for Phase 1A; it activates from Phase 1G onward
