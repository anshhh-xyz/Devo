---
doc: scope
status: approved
---

# Devo

An evidence-first CLI coding assistant that makes one approved change, verifies it with real pytest runs before and after, and reports what the check actually showed.

## The Unique Kernel
The model may propose plans and structured edits, but only the deterministic controller computes the verdict from real process execution results. Model prose never influences the verdict. The CLI reports "passed N tests", never "it works".

## Who It's For
Python developers working with AI coding agents who are tired of models claiming code is fixed when tests are failing, skipped, or broken.

## The Core Loop
1. The user specifies a workspace and task (`python -m devo run --workspace PATH --task "..."`).
2. Devo inspects files within strict workspace boundaries and runs a baseline check (`pytest`).
3. The model proposes a structured edit.
4. Devo generates a unified diff and presents an interactive approval prompt bound to the diff's SHA-256 hash.
5. Upon explicit human approval (`approve`), Devo applies the change and runs the final check.
6. The pure-function verdict engine computes the verdict (`[VERIFIED]`, `[FAILED]`, or `[NOT VERIFIED]`).
7. The user can roll back immediately with hash-checked `revert`.

## Inspiration & Identity
Clean, robust UNIX-style CLI developer tool. Dense, transparent, and honest terminal experience. Plain text labels by default (`[VERIFIED]`, `[FAILED]`, `[NOT VERIFIED]`) with optional clean `rich` formatting.

## Why This Matters to the Learner
To demonstrate that AI development tools can be made safe by construction, transparent, and grounded in real automated testing rather than trusting hallucinated model claims.

## What "Working" Looks Like
A CLI session running end-to-end against a seeded demo project demonstrating three distinct, repeatable outcomes:
- **Verified:** Baseline failed → change applied → final passed (`red_to_green`).
- **Verification failed:** Erroneous fix applied → final check fails → immediate hash-checked `revert`.
- **Not verified:** Hung process / infinite loop hits timeout and is safely terminated and labeled `Not verified`.

## The POC Boundary
- Local Python projects using `pytest`.
- CLI commands: `run`, `revert`, `demo-reset`.
- Deterministic mock backend for rock-solid reproducible demo and integration tests, plus optional API backend.
- Workspace path traversal protection, process-tree timeout kill, and SHA-256 diff-bound approval tokens.

## Later
- Multi-language test runners (Jest, Cargo, Go).
- Multi-step iterative repair loops.
- Terminal UI / TUI panels.

## Explicitly Cut
- Web or GUI interface (hackathon requires a working PoC; CLI is complete and coherent).
- Autonomous command execution by model (security risk; commands are fixed presets only).
- Background daemon or complex database (unnecessary complexity for V1).
