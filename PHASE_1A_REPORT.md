# PHASE 1A Report

1. Files created (with line counts)

- README.md: 46
- BACKLOG.md: 3
- CONTRACT.md: 1
- LICENSE: 21
- .gitignore: 39
- pyproject.toml: 18
- portwatch/__init__.py: 1
- portwatch/cli.py: 16
- tests/__init__.py: 1
- .github/workflows/ci.yml: 32
- PHASE_1A_REPORT.md: 9

2. Files modified

- None (DECISIONS.md was present and not modified)

3. Verification commands run locally

- `python3 -c "import portwatch; print(portwatch.__version__)"`  # printed `0.0.1`
- `python3 -m pytest -q`  # ran; tests directory contained no tests

4. Decisions requiring user review

- None discovered. PHASE_1A.md and DECISIONS.md do not conflict.

5. Ambiguities or surprises

- `python` command was not available in the environment used here; `python3` was used instead.

6. Verification results (commands and literal outputs)

- Editable install in a clean venv:

	- Created venv at `/tmp/portwatch_phase1a_venv` and ran `pip install -e "./[dev]"` against the repo root.
	- Outcome: success (package installed in editable mode with dev dependencies).

- `portwatch --version` (literal output):

```
portwatch 0.0.1
```

- `portwatch` with no arguments (literal output):

```
not yet implemented — see PHASE files for build status
```

- `git status` / untracked files (literal `git ls-files --others --exclude-standard` output):

```
.github/workflows/ci.yml
.gitignore
BACKLOG.md
CONTRACT.md
DECISIONS.md
LICENSE
PHASE_1A.md
PHASE_1A_REPORT.md
README.md
portwatch/__init__.py
portwatch/cli.py
pyproject.toml
tests/__init__.py
```

- Comparison with expected Phase 1A files:

	- Expected (this phase): `README.md`, `BACKLOG.md`, `CONTRACT.md`, `LICENSE`, `.gitignore`, `pyproject.toml`, `portwatch/__init__.py`, `portwatch/cli.py`, `tests/__init__.py`, `.github/workflows/ci.yml`, `PHASE_1A_REPORT.md`.
	- Extra untracked files: `DECISIONS.md`, `PHASE_1A.md`.

	Note: `DECISIONS.md` was present in the repo prior to this phase; here it appears as untracked in the working tree. If you expect a clean `git status` showing only the new files, commit or stage `DECISIONS.md` and `PHASE_1A.md` as appropriate.

- CI workflow verification:

	- `.github/workflows/ci.yml` includes `uses: actions/setup-python@v4` (correct).
	- The workflow uses `python -m pip install --upgrade pip`, `pip install -e ".[dev]"`, and `python -c "import portwatch; print(portwatch.__version__)"`, which rely on the Python provided by `actions/setup-python` rather than assuming a system `python` binary. This matches the PHASE_1A requirement.

