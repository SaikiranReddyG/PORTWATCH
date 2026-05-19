# portwatch — terminal-native port visualiser

**Status:** v0.1 in development — data layer is being built. Chip UI lands in v0.2.

What it is

portwatch is a terminal-native, real-time port and socket visualiser for Linux. It renders the host's network surface as a microcontroller-style chip diagram, where each active port is presented as a pin with state expressed through symbols and colour.

What it is not

- Not a packet sniffer (no libpcap, no eBPF, no traffic byte counters in v1)
- Not a firewall (does not write nftables/iptables rules)
- Not a vulnerability scanner
- Not a long-term forensics tool (no persistent history)

Install

pipx install portwatch  # placeholder — not on PyPI yet

Usage

At this stage the only supported command is:

```
portwatch --version
```

Project structure

Planned layout:

```
portwatch/
├── core/        # poll, parse, diff — pure logic, no UI imports
├── widgets/     # ChipWidget, DetailPanel — Textual widgets, no I/O
├── app.py       # standalone Textual app
└── pulse_panel.py
```

Phased build

Development proceeds in small, ordered phases. Each phase produces a runnable, testable artefact and is documented in its own `PHASE_*.md` file. This repository is currently in Phase 1A (repo scaffold).

License

MIT — see the LICENSE file for details.
