# Devo — Evidence-First Coding Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

> Built for the Devpost **Build with AI: Basics** Hackathon.
> Includes planning documents generated with the Devpost Learn Skill Pack (`devpost/scope.md`, `devpost/prd.md`, `devpost/spec.md`).

Devo is an **evidence-first command-line coding assistant** for local Python projects. It makes one approved code change, runs a fixed test check before and after, and reports what the check actually showed.

**Core rule:** The AI model may propose plans and structured edits, but **only the deterministic harness computes the verdict** from real test process execution. Model prose never influences it. Devo reports *"passed N tests"*, never *"it works"*.

---

## The Verdict Model

Devo replaces hallucinated claims of success with three honest, test-backed verdicts:

| Verdict | Meaning | Evidence Category |
|---|---|---|
| `[VERIFIED]` | All tests passed after the edit. Executed test count did not regress. | `red_to_green` (baseline failed → final passed) or `no_regression_only` (baseline was already passing). |
| `[FAILED]` | Tests failed, broke syntax, or threw runtime errors after the change. | `none`. File changes can be immediately reverted with `python -m devo revert`. |
| `[NOT VERIFIED]` | Check timed out, aborted, collected 0 tests, or fewer tests ran than before (e.g. model deleted or skipped tests). | `none`. Untrusted change is never certified. |

---

## Key Safety Controls

- **Workspace Boundary:** Path traversal (`../`), symlink escapes, and absolute paths pointing outside the workspace are blocked in code.
- **Diff-Bound Approval Gate:** Devo displays a unified diff and halts. Writing files requires an approval token cryptographically bound (`SHA-256`) to the exact diff text displayed.
- **Automatic Backups & Rollback:** Original files are backed up to `.devo-runs/<run-id>/backup/` before any edits occur, and can be restored byte-for-byte with `python -m devo revert`.
- **Immutable Presets:** Commands are strictly hard-coded presets (`pytest -q --junitxml=... -p no:cacheprovider`). Neither the model nor workspace configuration can dictate what shell commands run.
- **Secret Redaction & Subprocess Scrubbing:** API keys, database passwords, and auth tokens are scrubbed from the child environment and redacted from traces.
- **Output Hygiene:** Terminal escape sequences and ANSI control characters from untrusted child processes and models are stripped to prevent terminal injection.

---

## Quickstart

### 1. Requirements & Setup

- Python 3.10+ (tested on Python 3.13)
- Git

```bash
# Clone the repository
git clone https://github.com/anshhh-xyz/Devo.git
cd Devo

# Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install in editable mode with dependencies
pip install -e .
```

### 2. Reset the Seeded Demo Workspace

Devo ships with a seeded demo project (`demo/seed`) containing one planted bug and 5 pytest tests:

```bash
python -m devo demo-reset
```

### 3. Run Verification (Mock Mode — No API Key Required)

Devo includes deterministic fixtures to reproduce all three verdict states:

```bash
# 1. Verified Scenario (red to green fix)
python -m devo run --workspace demo/workspace --task "Fix division in mathutils.py" --backend mock --scenario scenario_verified

# 2. Failed Scenario (wrong fix, followed by revert)
python -m devo run --workspace demo/workspace --task "Fix division" --backend mock --scenario scenario_failed

# 3. Not Verified Scenario (hang / infinite loop hits timeout)
python -m devo run --workspace demo/workspace --task "Introduce loop" --backend mock --scenario scenario_not_verified --timeout 1.0
```

### 4. Rollback a Run

To revert any applied change back to its exact pre-run byte state:

```bash
python -m devo revert --run <RUN_ID> --workspace demo/workspace
```

### 5. Run the Test Suite

Devo's own test suite includes table-driven verdict tests, XML parser security checks, boundary tests, and end-to-end integration scenarios:

```bash
pytest tests/
```

---

## Optional: Live Model Backend (API Mode)

To use a live LLM instead of mock mode:

```bash
# Set your API key
set DEVO_API_KEY=your_key_here  # Windows cmd
$env:DEVO_API_KEY="your_key_here"  # Windows PowerShell
export DEVO_API_KEY="your_key_here"  # Linux/macOS

# Run with the API backend
python -m devo run --workspace demo/workspace --task "Fix division bug in mathutils.py" --backend api
```

---

## Honest Limits

- **Not a Sandbox:** Running a project's test suite executes that project's code with your local user permissions. Only run Devo on codebases you trust.
- **Evidence, Not Proof:** A passing test suite proves that the tested assertions passed; it does not prove code is free from untested defects.
- **Supported Framework:** V1 supports Python projects using `pytest`.

---

## License

[MIT](LICENSE)
