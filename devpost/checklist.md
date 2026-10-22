---
doc: checklist
status: approved
---

# Build Checklist

Build mode: fast

## Slices

- [x] **1. Verdict engine, runner, junit parser, and seeded demo project**
  Becomes usable: Running pytest checks through Devo runner, parsing junit XML, and deterministic verdict computation with table-driven tests.
  Why now: The verdict engine and runner are the foundational core of Devo; verifying test outputs without any model or CLI proves the entire hypothesis.
  PRD ref: `prd.md > Check Runner & Preset Sandbox Limits`, `prd.md > Verdict Engine`
  Spec ref: `spec.md > Components`, `spec.md > Data Shapes`
  Build: Implement `pyproject.toml`, `devo.verdict.compute_verdict`, `devo.runner.parse_junit`, `devo.runner.presets`, `devo.runner.run_check`, and seeded demo project in `demo/seed/`.
  Verify (mechanical): Run unit tests for `compute_verdict` and `parse_junit` with 100% table coverage; run runner against demo seed and observe expected baseline failure.
  Commit: `Verdict engine, runner, junit parser and demo seed with tests`

- [x] **2. Workspace boundary and safe change lifecycle**
  Becomes usable: Devo can inspect a project, validate edits within boundary, generate unified diffs, demand cryptographic approval, and revert safely.
  Why now: Establishes safety-by-construction before introducing any model code proposals.
  PRD ref: `prd.md > Workspace Boundary & Safe Edits`
  Spec ref: `spec.md > File Structure`, `spec.md > Components`
  Build: Implement `workspace.boundary`, `workspace.inspect`, `workspace.edits`, `workspace.diff`, `workspace.backup`, `controller.approval`, `trace.trace`, and `trace.redact`.
  Verify (mechanical): Unit tests for traversal prevention, exact string match editing, diff calculation, approval token checks, and byte-for-byte rollback.
  Commit: `Workspace boundary, diff, approval gate, backup and revert with tests`

- [x] **3. Model backend, controller, and end-to-end integration runs**
  Becomes usable: The controller orchestrates the full state machine end-to-end using mock fixtures, reproducing all three verdict scenarios in automated integration tests.
  Why now: Connects the pieces and proves the complete journey before adding CLI UI layers.
  PRD ref: `prd.md > The Core Journey`, `prd.md > States and Boundaries`
  Spec ref: `spec.md > Core Journey Through the System`
  Build: Implement `model.schema`, `model.adapter`, `model.mock`, `controller.states`, and `controller.run`. Create 3 mock scenario fixtures.
  Verify (mechanical): Integration tests run all 3 scenarios (`scenario_verified`, `scenario_failed`, `scenario_not_verified`) and assert exact verdict states.
  Commit: `Controller, mock backend and end-to-end scenarios`

- [x] **4. CLI experience, sanitized reporting, and demo reset**
  Becomes usable: Complete interactive terminal tool with `run`, `revert`, and `demo-reset` commands, live traces, diff inspection, and clear reporting.
  Why now: The customer-facing product experience needed for the demo video.
  PRD ref: `prd.md > Interaction Surface (Terminal CLI)`, `prd.md > Look and Feel`
  Spec ref: `spec.md > Components`
  Build: Implement `cli.py`, `__main__.py`, `report.sanitize`, `report.render`, and `demo-reset` handling.
  Verify (mechanical): Run complete CLI workflow on `demo/workspace` for all 3 scenarios.
  Commit: `CLI experience for the full journey`

- [x] **5. Hardening and security reviews**
  Becomes usable: Robust handling of syntax errors, runaway loops, binary files, ANSI injection, and secret redaction.
  Commit: `Hardening and edge-case tests`

- [x] **6. Final clean-checkout verification and docs**
  Becomes usable: Fresh clone test, complete README, open source license check.
  Commit: `Docs, license and clean-checkout fixes`
