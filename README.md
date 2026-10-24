# Devo — Evidence-First Coding Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Tests: 52 passing](https://img.shields.io/badge/tests-52%20passing-brightgreen.svg)](tests/)

> Built for the Devpost **Build with AI: Basics** Hackathon.

---

## The Problem

AI coding assistants frequently claim *"the fix is applied and everything works"* — but the tests tell a different story. They may:

- Report success while tests are still **failing**
- Silently **delete** the failing test so the suite goes green
- **Weaken assertions** so the test passes the bug instead of catching it
- Claim a fix worked when the process **timed out** or never ran

**Devo enforces a strict boundary:** The AI model may only *propose* structured code edits. Only the deterministic test harness computes the verdict — from real process execution, real exit codes, and real test counts. Model prose never influences the result.

---

## What Devo Does

Devo runs a **5-step verification loop** on a local Python project:

```
1. Run baseline tests        → record result and test count BEFORE any edit
2. Ask model for a patch     → structured JSON: exact search/replace edits + explanation
3. Show unified diff         → require your explicit typed approval
4. Apply patch and re-run    → same sandboxed subprocess, same timeout
5. Compare results           → emit [VERIFIED], [FAILED], or [NOT VERIFIED]
```

The verdict is always one of three honest outcomes:

| Verdict | What it means | Evidence Category |
|---|---|---|
| `[VERIFIED]` | Tests passed. Count didn't regress. Bug was genuinely fixed. | `red_to_green` or `no_regression_only` |
| `[FAILED]` | Tests still fail after the patch. Fix didn't work. Roll back instantly. | `none` |
| `[NOT VERIFIED]` | Suite is green but fewer tests ran — model deleted or skipped tests. Or process timed out. | `none` |

---

## Quickstart

### 1. Clone and set up

```bash
git clone https://github.com/anshhh-xyz/Devo.git
cd Devo
python -m venv .venv

# Windows PowerShell:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1

# macOS / Linux:
source .venv/bin/activate

pip install -e ".[dev]"
```

### 2. Health check

```bash
pytest tests/
# Expected: 52 passed, 1 skipped
```

### 3. Reset the demo workspace

```bash
# Mock demo (mathutils, no API key needed):
python -m devo demo-reset --seed demo/seed --workspace demo/workspace

# Live API demo (textutils, requires an API key):
python -m devo demo-reset --seed demo/seed_api --workspace demo/workspace_api
```

> **Always reset before a demo run** — Devo modifies files in the workspace directory. Reset restores them to the original seed state.

### 4. Run a scenario

```bash
# Scenario 1 — Genuine fix (mock, no key needed)
python -m devo run \
  --workspace demo/workspace \
  --task "Fix the divide function in mathutils.py" \
  --backend mock \
  --scenario scenario_verified
```

When the diff appears, type `approve` to apply it or press Enter to reject.

### 5. Undo any change

Every run prints its **Run ID** at the bottom. Revert with:

```bash
python -m devo revert --run <RUN_ID> --workspace demo/workspace
```

---

## API Key Setup

Devo auto-detects your key — no config file needed.

| Provider | Environment variable(s) | Notes |
|---|---|---|
| **Groq** *(recommended)* | `GROQ_API_KEY` or `GROQ_API_KEY_1`…`4` | Free tier, fastest inference |
| **Gemini** | `GEMINI_API_KEY` | Google AI Studio free tier |
| **OpenAI** | `OPENAI_API_KEY` or `DEVO_API_KEY` | Standard key |

```powershell
# Windows PowerShell — set once per session
$env:GROQ_API_KEY = "gsk_your_key_here"
```

```bash
# macOS / Linux
export GROQ_API_KEY="gsk_your_key_here"
```

Then run with `--backend api`. Mock mode (`--backend mock`) runs entirely without a key.
See [`.env.example`](.env.example) for reference.

---

## Using Devo on Your Own Project

You can run Devo on any local Python codebase that uses `pytest`.

### 1. Prerequisites for your project
* Your project should have automated tests runnable via `pytest` (e.g., in `tests/` or `test_*.py`).
* Set your API key in your terminal session (see [API Key Setup](#api-key-setup) above).

### 2. Run Devo on your codebase
Point `--workspace` to your project's root folder and describe the bug or fix in `--task`:

```bash
python -m devo run \
  --workspace /path/to/your/project \
  --task "Fix ZeroDivisionError in calculate_metrics when dataset is empty" \
  --backend api
```

*(On Windows, you can provide absolute paths like `C:\Users\you\repos\my-project` or relative paths like `../my-project`)*.

### 3. Step-by-Step Interactive Flow

1. **Baseline check**: Devo executes your existing test suite in a sandboxed subprocess and records passing/failing test counts *before* touching any code.
2. **Model patch generation**: Devo provides the model with the workspace context and test failure output. The model returns structured edits (exact search-and-replace blocks).
3. **Diff inspection & approval gate**: Devo calculates a unified diff and presents it in your terminal.
   * **To apply the patch**: Type `approve` and press Enter.
   * **To reject**: Press Enter without typing anything (or type `no`). Devo terminates immediately and makes **zero changes** to your workspace.
4. **Verification re-run**: If approved, Devo creates a byte-for-byte backup, applies the edits safely within the workspace boundary, and re-runs the exact same test suite under identical constraints.
5. **Verdict computation**: The pure-function verdict engine compares pre-run vs post-run test execution metrics and reports:
   * **`[VERIFIED]`**: All tests pass, and no test count regression occurred.
   * **`[FAILED]`**: Tests still failed or crashed after the edit.
   * **`[NOT VERIFIED]`**: Tests passed, but total test count decreased (caught test deletion) or tests timed out.

### 4. Undoing / Rolling Back Changes
If you want to undo what Devo modified, every run prints a unique **Run ID** (e.g., `run_20261025_015033_abc123`). Restore your workspace to its exact pre-run state with:

```bash
python -m devo revert --workspace /path/to/your/project --run <RUN_ID>
```

---

## CLI Reference

### `devo run` — Run the verification loop

| Flag | Description |
|---|---|
| `--workspace <path>` | Python project directory to work in |
| `--task <text>` | Natural language description of the bug to fix |
| `--backend mock\|api` | `mock` replays a fixture; `api` calls a live LLM |
| `--scenario <name>` | Fixture name when using `--backend mock` |
| `--model <name>` | Override LLM model (e.g. `gemini-2.0-flash`) |
| `--endpoint <url>` | Override API endpoint URL |
| `--timeout <secs>` | Override subprocess execution timeout |

### `devo revert` — Roll back a run

```bash
python -m devo revert --run <run-id> --workspace demo/workspace
```

Restores every modified file to its exact byte-for-byte pre-run state.

### `devo demo-reset` — Restore a seed workspace

```bash
python -m devo demo-reset --seed demo/seed --workspace demo/workspace
```

---

## The 5 Demo Scenarios

All scenarios below use `--backend mock` (no API key required).
**Reset the workspace before each run:**

```bash
python -m devo demo-reset --seed demo/seed --workspace demo/workspace
```

---

### Scenario 1 — Genuine Fix → `[VERIFIED]`

```bash
python -m devo run --workspace demo/workspace \
  --task "Fix the divide function in mathutils.py" \
  --backend mock --scenario scenario_verified
```

The model correctly replaces `return a * b` with `return a / b` in `mathutils.py`.
Tests go from 1 failing → 5 passing. Verdict: **`[VERIFIED]` — red_to_green**.

- **Source file fixed:** `demo/workspace/mathutils.py`
- **Test file:** `demo/workspace/test_mathutils.py`
- **Fixture:** `fixtures/model/scenario_verified.json`

---

### Scenario 2 — Bad Patch → `[FAILED]`

```bash
python -m devo run --workspace demo/workspace \
  --task "Fix division (bad attempt)" \
  --backend mock --scenario scenario_failed
```

The model applies a patch that still produces wrong output. Tests continue to fail.
Verdict: **`[FAILED]`**. Run `devo revert` to restore.

- **Fixture:** `fixtures/model/scenario_failed.json`

---

### Scenario 3 — Test Deletion Caught → `[NOT VERIFIED]`

```bash
python -m devo run --workspace demo/workspace \
  --task "Fix divide function" \
  --backend mock --scenario scenario_test_deleted
```

The model **removes `test_divide()`** from the test file instead of fixing the bug.
The suite exits 0, 0 failures. But Devo counts **4 tests where 5 ran before** and refuses to verify.
Verdict: **`[NOT VERIFIED]` — count regression**.

- **Test file touched:** `demo/workspace/test_mathutils.py`
- **Fixture:** `fixtures/model/scenario_test_deleted.json`

---

### Scenario 4 — Weakened Assertion → Diff Warning

```bash
python -m devo run --workspace demo/workspace \
  --task "Fix divide function" \
  --backend mock --scenario scenario_weakened_test
```

The model changes `assert divide(6,2) == 3` to `assert divide(6,2) == 12` to match the buggy output.
Devo prints a **`[!] CAUTION: This change modifies test files`** banner on the diff.
Press Enter to **reject** it.

- **Fixture:** `fixtures/model/scenario_weakened_test.json`

---

### Scenario 5 — Live API Run → `[VERIFIED]`

```bash
python -m devo demo-reset --seed demo/seed_api --workspace demo/workspace_api

python -m devo run \
  --workspace demo/workspace_api \
  --task "title_case returns uppercase instead of title case — fix it" \
  --backend api
```

A real LLM call fixes `return text.upper()` → `return text.title()` in `textutils.py`.
5/5 tests pass on live inference. Verdict: **`[VERIFIED]` — red_to_green**.

- **Source file fixed:** `demo/workspace_api/textutils.py`
- **Test file:** `demo/workspace_api/test_textutils.py`
- **API adapter:** `src/devo/model/api.py`

---

## How the Verdict Engine Works

The core logic is a single **pure Python function** with zero side effects, zero model input:

```python
# src/devo/verdict/compute_verdict.py

def compute_verdict(baseline: CheckResult, final: CheckResult) -> Verdict:
    # Rule 1: Process must complete (no timeout, no spawn error)
    # Rule 2: JUnit XML must be valid and parseable (defusedxml)
    # Rule 3: At least one test must have been collected
    # Rule 4: No test failures or errors in the final run
    # Rule 5: final.executed >= baseline.executed  ← catches test deletion
    # Rule 6: Check for increased skipped tests (warning only)
    # Rule 7: Classify evidence as red_to_green or no_regression_only
```

Model output **never reaches this function**. It only receives `CheckResult` objects
built from raw subprocess exit codes and parsed JUnit XML.

---

## Security Design

| Threat | Mitigation | File |
|---|---|---|
| AI edits files outside the project | Path traversal and symlink escape prevention | `src/devo/workspace/boundary.py` |
| AI deletes tests to hide failures | Executed test count regression check | `src/devo/verdict/compute_verdict.py` |
| AI modifies test files silently | `touches_tests` flag → visible `[!] CAUTION` banner | `src/devo/workspace/diff.py` |
| Malicious JUnit XML (XXE attack) | Uses `defusedxml`, rejects entity expansion | `src/devo/runner/parse_junit.py` |
| API keys leaked to subprocess | Full environment variable scrub before spawn | `src/devo/runner/run_check.py` |
| Output buffer overflow | stdout/stderr capped at 500 KB | `src/devo/runner/run_check.py` |
| Runaway test process | `taskkill /F /T` (Windows) / `os.killpg` (POSIX) | `src/devo/runner/run_check.py` |
| Unapproved edits applied | SHA-256 diff-bound approval token, requires typing `approve` | `src/devo/controller/approval.py` |
| Terminal injection from model | ANSI and control character stripping | `src/devo/report/sanitize.py` |

---

## Full File Structure

```
Devo/
│
├── src/devo/                          # All application source code
│   ├── cli.py                         # Entry point: run / revert / demo-reset commands
│   ├── __main__.py                    # Enables: python -m devo <command>
│   │
│   ├── controller/
│   │   ├── run.py                     # Orchestrates full verification lifecycle
│   │   ├── states.py                  # RunState and RunReport dataclasses
│   │   └── approval.py                # SHA-256 diff-bound approval token + interactive gate
│   │
│   ├── verdict/
│   │   └── compute_verdict.py         # CORE: pure-function verdict engine (no model input)
│   │
│   ├── runner/
│   │   ├── run_check.py               # Spawns sandboxed pytest subprocess, kills on timeout
│   │   ├── parse_junit.py             # Parses JUnit XML securely via defusedxml
│   │   └── presets.py                 # Hard-coded check preset definitions
│   │
│   ├── workspace/
│   │   ├── boundary.py                # Blocks path traversal and symlink escapes
│   │   ├── edits.py                   # Validates and applies search/replace edits
│   │   ├── diff.py                    # Computes unified diff, detects test file touches
│   │   ├── backup.py                  # Byte-for-byte pre-run snapshots and revert
│   │   ├── inspect.py                 # Lists workspace files safely within boundary
│   │   └── reset.py                   # Copies seed → workspace for demo resets
│   │
│   ├── model/
│   │   ├── adapter.py                 # Abstract base interface for model backends
│   │   ├── api.py                     # Live backend: auto-detects Groq / Gemini / OpenAI
│   │   ├── mock.py                    # Fixture-replay backend (no API key, deterministic)
│   │   ├── prompts.py                 # System prompt and user prompt builder
│   │   └── schema.py                  # Validates and parses model JSON output structure
│   │
│   ├── report/
│   │   ├── render.py                  # Terminal output: banners, diff view, verdict report
│   │   └── sanitize.py                # Strips ANSI codes and control characters
│   │
│   └── trace/
│       ├── trace.py                   # Structured execution trace emitter
│       └── redact.py                  # Redacts API keys and secrets from traces
│
├── tests/
│   ├── integration/
│   │   └── test_scenarios.py          # End-to-end lifecycle tests for all 5 scenarios
│   └── unit/
│       ├── test_compute_verdict.py    # 12 table-driven verdict engine test cases
│       ├── test_parse_junit.py        # JUnit parser tests including XXE attack fixture
│       ├── test_runner.py             # Subprocess runner tests (timeout, env scrub)
│       ├── test_boundary.py           # Path traversal and symlink escape tests
│       ├── test_edits_and_lifecycle.py # Edit validation + backup/revert tests
│       ├── test_api_adapter.py        # API credential auto-detection tests
│       ├── test_cli.py                # CLI command argument tests
│       ├── test_sanitize.py           # ANSI and control character sanitization tests
│       └── test_trace_and_redact.py   # Trace emitter and secret redaction tests
│
├── demo/
│   ├── seed/                          # mathutils: planted bug in divide() (a*b not a/b)
│   │   ├── mathutils.py               # Source with bug: divide() returns a * b
│   │   └── test_mathutils.py          # 5 tests — test_divide fails on the bug
│   ├── seed_api/                      # textutils: planted bug in title_case()
│   │   ├── textutils.py               # Source with bug: title_case() calls .upper()
│   │   └── test_textutils.py          # 5 tests — test_title_case fails on the bug
│   ├── workspace/                     # Live copy of mathutils (gitignored, reset before demo)
│   └── workspace_api/                 # Live copy of textutils (gitignored, reset before demo)
│
├── fixtures/
│   ├── model/                         # Mock model response fixtures (no API key needed)
│   │   ├── scenario_verified.json     # Correct fix: divide() returns a / b
│   │   ├── scenario_failed.json       # Wrong fix: still fails tests
│   │   ├── scenario_not_verified.json # Infinite loop: hits timeout → NOT VERIFIED
│   │   ├── scenario_test_deleted.json # Deletes test_divide() instead of fixing bug
│   │   └── scenario_weakened_test.json # Changes assertion to match buggy output
│   ├── junit_failing.xml              # Sample JUnit: 1 failure (parser unit tests)
│   ├── junit_passing.xml              # Sample JUnit: all pass (parser unit tests)
│   ├── junit_syntax.xml               # Sample JUnit: syntax/collection error
│   └── junit_zero.xml                 # Sample JUnit: 0 tests collected
│
├── devpost/                           # Hackathon planning documents
│   ├── scope.md                       # Approved project scope and PoC boundary
│   ├── prd.md                         # Product requirements — core journey, states, edge cases
│   ├── spec.md                        # Technical spec — stack, components, data shapes
│   └── checklist.md                   # Build checklist — all 6 slices complete
│
├── docs/
│   ├── roadmap.md                     # Phase-by-phase build and demo roadmap
│   └── architectural.md               # Architecture decisions and component diagram
│
├── .env.example                       # API key reference (never commit real keys)
├── pyproject.toml                     # Package config, dependencies (pytest, defusedxml)
├── LICENSE                            # MIT License
└── README.md                          # This file
```

---

## Running the Tests

```bash
pytest tests/                 # All 52 tests
pytest tests/unit/            # Unit tests only
pytest tests/integration/     # End-to-end scenario tests only
pytest tests/ -v              # Verbose output
```

All tests are fully self-contained. No API keys, no network, no local state required.

---

## Design Principles

1. **Evidence over claims** — Devo reports what tests actually showed, never model confidence.
2. **Human in the loop** — No file is changed without explicit terminal approval.
3. **Deterministic verdict** — Same test results always produce the same verdict. No randomness, no model influence.
4. **Defence in depth** — Algorithmic checks (count regression) + human gate (diff approval) + workspace boundary: three independent layers.
5. **Honest limits** — If a semantically weakened assertion keeps test count stable, Devo cannot detect it algorithmically. The diff warning and approval gate are the human's defence layer. Devo documents this clearly rather than overstating its guarantees.

---

## Hackathon Context

Built for the **Devpost Build with AI: Basics Hackathon**.

Planning documents are in `devpost/` (`scope.md`, `prd.md`, `spec.md`, `checklist.md`),
generated using the Devpost Learn Skill Pack and approved before any code was written.

**GitHub:** https://github.com/anshhh-xyz/Devo

---

## Honest Limits

- **Not a sandbox:** Running tests executes that project's code with your local user permissions. Only run Devo on codebases you trust.
- **Evidence, not proof:** Passing tests prove that the tested assertions passed — not that the code is free from untested defects.
- **Supported framework:** v0.1 supports Python projects using `pytest`.

---

## License

[MIT](LICENSE) — free to use, modify, and distribute.
