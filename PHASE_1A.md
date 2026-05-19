# PHASE 1A — Repo Scaffold

**Goal:** create the empty skeleton of the portwatch project. No application logic. No parsing. No UI. Just structure that proves the packaging works.

**Definition of done:** `pipx install --editable .` succeeds, `portwatch --version` prints a version string, `pytest` runs (with zero tests) and exits cleanly.

---

## Context

This is the very first phase of the portwatch project. Before reading further, you must have read `DECISIONS.md`. That document is **reference**: it describes the final shape of the v1 project. It is not a to-do list. Your work in this phase is bounded strictly by what this document tells you to build.

If anything in this phase document appears to conflict with `DECISIONS.md`, follow this document and surface the conflict to the user.

---

## In scope

You will create exactly the following:

### 1. Repository files (at repo root)

- `README.md` — portfolio-grade introduction. See §"README content" below for required sections.
- `DECISIONS.md` — already exists, do not modify.
- `BACKLOG.md` — create with a single placeholder section: `## Deferred from v1` followed by an empty bullet list. Future phases will populate this.
- `CONTRACT.md` — create with a single line: `Event schema specification — populated in Phase 4 when Pulse integration begins.` Nothing more.
- `LICENSE` — MIT license, current year, author placeholder `<AUTHOR_NAME>`.
- `.gitignore` — standard Python gitignore (Python build artefacts, virtualenv directories, `__pycache__`, `.pytest_cache`, `*.egg-info`, `.env`, `dist/`, `build/`). Do not invent custom entries.
- `pyproject.toml` — see §"pyproject.toml content" below.

### 2. Package skeleton

```
portwatch/
├── __init__.py        # contains: __version__ = "0.0.1"
└── cli.py             # contains the entry point — see §"cli.py content"
```

### 3. Test skeleton

```
tests/
└── __init__.py        # empty file
```

No test files yet. The directory must exist so pytest discovers it cleanly.

### 4. CI stub

```
.github/
└── workflows/
    └── ci.yml         # see §"CI content"
```

---

## Out of scope (do not implement, even though DECISIONS.md mentions them)

The following are explicitly forbidden in this phase. They belong to later phases. If you find yourself reaching for any of these, stop and re-read this list.

- Any `/proc` parsing whatsoever
- Any socket, port, PID, or process logic
- Any Textual widgets, Rich rendering, or UI code
- Any Pulse integration, `httpx` imports, or HTTP code
- Any heuristic, suspicious detection, or learning-mode code
- Any `.env` loading code
- Any logging configuration beyond the Python default
- Any tests beyond the empty `tests/` directory
- Any CHANGELOG.md (deferred until first tag)
- Any screenshots in README (the UI does not exist yet)

The package must import cleanly and the CLI must do nothing more than print a version string when invoked with `--version`.

---

## File contents — exact specifications

### README content

The README is portfolio-grade from day one. Required sections in this order:

1. **Title and tagline.** One sentence describing what portwatch is.
2. **Status banner.** A clear note: `**Status:** v0.1 in development — data layer is being built. Chip UI lands in v0.2.`
3. **What it is.** Two to four sentences. Use the language from `DECISIONS.md §1.1`.
4. **What it is not.** Bullet list from `DECISIONS.md §1.2`. This is a portfolio signal: it shows scope discipline.
5. **Install.** `pipx install portwatch` (placeholder — not on PyPI yet, mention that).
6. **Usage.** `portwatch --version` is the only working command at this stage. Be honest about it.
7. **Project structure.** A short tree showing the planned layout. Use the structure from `DECISIONS.md §7.1`.
8. **Phased build.** A short paragraph explaining the phased approach. This is interview gold — recruiters love seeing planned, disciplined development.
9. **License.** MIT, link to `LICENSE`.

No screenshots. No demo GIFs. No "coming soon" emoji clutter. Direct, honest, dated.

### pyproject.toml content

- Build backend: `setuptools` (no Poetry, no Hatch — keep it standard)
- `[project]` metadata: name `portwatch`, version `0.0.1`, Python `>=3.11`, license MIT, authors placeholder
- `[project.scripts]` entry: `portwatch = "portwatch.cli:main"`
- `[project.optional-dependencies].dev`: just `pytest`
- No runtime dependencies in this phase (Textual, httpx, Rich are added in later phases when needed)

### cli.py content

A single `main()` function. It uses `argparse` to handle `--version` and prints `portwatch <version>` reading from `portwatch.__version__`. Any other invocation prints a "not yet implemented — see PHASE files for build status" message and exits with code 0.

No `if __name__ == "__main__"` boilerplate beyond the entry point hook in `pyproject.toml`.

### CI content

A single GitHub Actions workflow that on push and pull request:
- Checks out the repo
- Sets up Python 3.11 and 3.12 in a matrix
- Installs the package with `pip install -e ".[dev]"`
- Runs `pytest` (which will pass with zero tests collected)
- Runs `python -c "import portwatch; print(portwatch.__version__)"` as a smoke test

No linters, no formatters, no coverage tools. Those come later if at all.

---

## Manual verification checklist

After completing this phase, the user verifies the following by hand. Include this checklist in `PHASE_1A_REPORT.md` at the end.

1. `git status` shows only the files this phase was supposed to create.
2. `pip install -e ".[dev]"` succeeds inside a clean virtualenv.
3. `portwatch --version` prints `portwatch 0.0.1`.
4. `portwatch` with no arguments prints the "not yet implemented" message.
5. `pytest` exits 0 with "no tests ran" or equivalent.
6. `python -c "import portwatch; print(portwatch.__version__)"` prints `0.0.1`.
7. The CI workflow file is valid YAML (no syntax errors when viewed in GitHub).

If any check fails, the phase is not complete.

---

## Phase report

At the end of this phase, create `PHASE_1A_REPORT.md` containing:

1. A list of every file created, with line counts
2. A list of every file modified (should be empty if you followed scope)
3. The exact commands you ran to verify the phase locally
4. Any decisions you had to make that were not specified in this document — these need user review before Phase 1B starts
5. Anything that surprised you or felt ambiguous — log it so future phases can be specified more tightly

Do not start Phase 1B. Wait for the user to review the report and hand you `PHASE_1B.md`.
