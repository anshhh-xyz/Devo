---
doc: prd
status: approved
---

# Devo — Product Requirements

An evidence-first command-line coding assistant for Python developers who need provable test-backed verification of AI changes.
Source: `scope.md > Who It's For` and `scope.md > The Unique Kernel`.

## The Core Journey
1. **Invocation:** Developer runs `python -m devo run --workspace ./demo/workspace --task "Fix division by zero"`.
2. **Inspection:** Devo resolves the workspace boundary and performs filtered reads of target code files, logging each to `trace.jsonl`.
3. **Baseline Check:** Devo executes the preset `pytest` runner against original unedited code, recording exit code, test counts, and junit XML.
4. **Planning & Diff:** The model backend returns structured search/replace edits. Devo generates a unified diff and checks if test files were touched.
5. **Interactive Approval Gate:** Devo displays the plan and unified diff, prompting the user for explicit approval (`approve`). An approval token bound to the SHA-256 hash of the diff is minted.
6. **Apply & Backup:** Originals are backed up under `.devo-runs/<run-id>/backup/` with original hashes recorded. The edits are applied.
7. **Final Check:** The same preset check is rerun with identical timeouts and environment limits.
8. **Verdict Computation:** `compute_verdict` evaluates baseline vs. final results, asserting executed test counts did not regress, and outputs a clear verdict label (`[VERIFIED]`, `[FAILED]`, or `[NOT VERIFIED]`).
9. **Rollback Option:** If the run failed or user wants to undo, `python -m devo revert --run <run-id>` safely restores backed up files.

## Interaction Surface (Terminal CLI)
Devo runs entirely in the developer's terminal.
- Command entry: `python -m devo <command> [options]`
- Live trace stream indicating state transitions: `INSPECTING`, `BASELINE_RUNNING`, `PLANNING`, `DIFF_READY`, `AWAITING_APPROVAL`, `APPLYING`, `FINAL_RUNNING`, `DONE`.
- Diff view: Formatted unified diff with explicit warning tags if tests are edited.
- Prompts: Interactive prompt requiring the user to type `approve` (empty Enter rejects).
- Final report: Summary box with verdict, evidence category (`red_to_green` / `no_regression_only`), duration, exit code, test numbers, and caveats.

## Look and Feel
- Honest, clear, and disciplined output.
- Color formatting is informative but meaning is **never** conveyed by color alone: explicit text tags like `[VERIFIED]`, `[FAILED]`, and `[NOT VERIFIED]` are always printed.
- Untrusted text from subprocesses and models is sanitized of ANSI control/escape sequences before printing.

## Features and Behavior

### 1. Workspace Boundary & Safe Edits
- Every path must resolve within the workspace directory; symlink escapes and traversal attempts (`../`) are blocked.
- Edits use single-match search/replace (`old_str` -> `new_str`). If `old_str` does not match exactly once, the change is rejected.
- File modifications are backed up before writes occur.

### 2. Check Runner & Preset Sandbox Limits
- Check commands are strictly built-in presets (e.g. `pytest --junitxml=...`). Neither the model nor workspace config files may alter the command.
- Subprocesses execute with `shell=False`, scrubbed environment variables (secrets/keys removed), hard timeouts with process-tree kills, and output caps.

### 3. Verdict Engine
- Pure function `compute_verdict(baseline, final, confirmed_min) -> Verdict`.
- Test count preservation: `final.executed` must be `>= max(baseline.executed, confirmed_min, 1)`. If fewer tests ran, the verdict is `NOT_VERIFIED`.
- Clear categorization:
  - Baseline failed + Final passed = `VERIFIED (red_to_green)`
  - Baseline passed + Final passed = `VERIFIED (no_regression_only)`
  - Final tests failed or syntax error = `FAILED`
  - Timeout, crash, or no tests collected = `NOT_VERIFIED`

### 4. CLI Commands
- `run`: Orchestrates the complete verification lifecycle.
- `revert`: Restores backed-up files from a previous run ID after checking hashes to prevent overwriting user edits.
- `demo-reset`: Copies clean `demo/seed` to `demo/workspace` for repeatable demonstration.

## States and Boundaries
- State machine: `IDLE` -> `WORKSPACE_SELECTED` -> `INSPECTING` -> `BASELINE_RUNNING` -> `PLANNING` -> `DIFF_READY` -> `AWAITING_APPROVAL` -> `APPLYING` -> `FINAL_RUNNING` -> `DONE`.
- If user rejects at `AWAITING_APPROVAL`, transition to `REJECTED` without any file writes.
- If any check or model call encounters an unrecoverable error, transition to `ERROR` and emit `NOT_VERIFIED`.
