---
doc: spec
status: approved
---

# Devo — Technical Spec

## How This Works, In Plain Language
Devo wraps AI code modifications inside a strict verification harness. When instructed to resolve a bug or task, it doesn't just ask an LLM to rewrite files and report back. Instead:
1. It validates the workspace folder boundaries so files outside cannot be touched.
2. It runs `pytest` in an isolated subprocess before making any changes (the baseline).
3. It asks the model for a minimal search-and-replace edit.
4. It displays the real unified diff and halts until a human explicitly types `approve`.
5. It applies the change only after backing up the original files.
6. It runs `pytest` again.
7. A pure Python function (`compute_verdict`) compares test results between baseline and final runs to determine whether the change legitimately passed all tests without skipping or deleting tests.

## The Core Journey Through the System
- User issues `python -m devo run --workspace ./demo/workspace --task "Fix bug" --backend mock --scenario scenario_verified`.
- `devo.cli` parses arguments and invokes `devo.controller.run.execute_run()`.
- `devo.workspace.boundary` checks that the workspace directory exists and resolves safely.
- `devo.workspace.inspect` discovers candidate source files, ignoring dotfiles, virtualenvs, and git.
- `devo.runner.run_check` executes the baseline preset (`python -m pytest --junitxml=... -p no:cacheprovider`).
- `devo.runner.parse_junit` parses the resulting XML via `defusedxml` to extract test metrics.
- `devo.model` returns the proposed structured edits (`old_str` and `new_str`).
- `devo.workspace.diff` creates the unified diff string and checks for modified test files.
- `devo.controller.approval` mints a token bound to `sha256(diff)`. The interactive prompt requests confirmation.
- `devo.workspace.backup` copies original files to `.devo-runs/<run-id>/backup/`.
- `devo.workspace.edits` applies the change.
- `devo.runner.run_check` runs the final check.
- `devo.verdict.compute_verdict` evaluates the results.
- `devo.report.render` prints the final honest report.

## Stack
- **Language:** Python 3.10+ (tested on Python 3.13)
- **Dependencies:**
  - `pytest`: Primary test runner and testing framework for Devo's test suite.
  - `defusedxml`: Safe parsing of untrusted junit XML output.
  - `rich` (optional): Clean terminal formatting of diffs and reports.
- **Packaging:** `pyproject.toml` with `pip install -e .`
- **Subprocess Execution:** `subprocess.Popen` with `shell=False`, argument list, and process-tree termination.

## File Structure
```
devo/
├── README.md
├── LICENSE
├── pyproject.toml
├── .gitignore
├── devpost/
│   ├── learner-profile.md
│   ├── scope.md
│   ├── prd.md
│   ├── spec.md
│   └── checklist.md
├── docs/
│   ├── architectural.md
│   └── roadmap.md
├── src/devo/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── controller/
│   │   ├── __init__.py
│   │   ├── run.py
│   │   ├── states.py
│   │   └── approval.py
│   ├── workspace/
│   │   ├── __init__.py
│   │   ├── boundary.py
│   │   ├── inspect.py
│   │   ├── edits.py
│   │   ├── diff.py
│   │   └── backup.py
│   ├── runner/
│   │   ├── __init__.py
│   │   ├── presets.py
│   │   ├── run_check.py
│   │   └── parse_junit.py
│   ├── verdict/
│   │   ├── __init__.py
│   │   └── compute_verdict.py
│   ├── model/
│   │   ├── __init__.py
│   │   ├── adapter.py
│   │   ├── mock.py
│   │   └── schema.py
│   ├── trace/
│   │   ├── __init__.py
│   │   ├── trace.py
│   │   └── redact.py
│   └── report/
│       ├── __init__.py
│       ├── sanitize.py
│       └── render.py
├── demo/
│   └── seed/
├── fixtures/
│   └── model/
└── tests/
    ├── unit/
    └── integration/
```

## Data Shapes
- **CheckResult:**
  ```python
  @dataclass
  class CheckResult:
      status: str  # "completed", "timeout", "spawn_error"
      exit_code: int
      duration_ms: int
      stdout: str
      stderr: str
      truncated: bool
      junit_ok: bool
      tests: int = 0
      failures: int = 0
      errors: int = 0
      skipped: int = 0
      reason: str = ""
  ```
- **Verdict:**
  ```python
  @dataclass
  class Verdict:
      state: str  # "VERIFIED", "FAILED", "NOT_VERIFIED"
      evidence: str  # "red_to_green", "no_regression_only", "none"
      reasons: list[str]
      caveats: list[str]
  ```

## Testing Strategy
- Unit tests for all pure modules: `compute_verdict`, `parse_junit`, `boundary`, `edits`, `diff`, `backup`, `redact`, `sanitize`.
- Integration tests executing all three scenarios end-to-end on mock fixtures:
  1. `scenario_verified.json`: Baseline fails -> final passes -> `VERIFIED (red_to_green)`
  2. `scenario_failed.json`: Final check fails -> `FAILED` -> `revert`
  3. `scenario_not_verified.json`: Timeout / hang -> `NOT_VERIFIED`
