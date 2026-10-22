# Devo — Roadmap (Python CLI, phase-wise build plan)

> **Status: plan, nothing built yet.** Read `architectural.md` first. Time figures are rough guesses, not measurements. **Submission deadline: October 27, 2026 @ 2:30 PM EDT** (5 days from kickoff on Oct 22, 2026). Plan phase times backwards from it.

**Scope note.** The Devpost requirements ask for a working proof of concept, a public repo, a text description and a demo video. They do not ask for a graphical or web UI. Devo V1 is a **command-line app**, so there is no server or UI phase.

## How to use this roadmap

- Work the phases **in order**. Each has steps, a "done when" test and a commit point. Don't start the next phase until the current one's "done when" is true.
- Write tests **in the phase that builds the code**, not at the end.
- The Skill Pack's `5-build` will generate its own `checklist.md` from your spec. Make its slices follow Phases 1–4 below.
- Anything marked **(your call)** is a decision you make yourself in the Skill Pack interviews.

## Overview

| Phase | Goal | Rough time | Cut priority |
|---|---|---|---|
| 0 | Setup, Skill Pack planning, locked decisions | 1.5–3 h | Required |
| 1 | Verdict engine, runner, junit parser, seeded demo project | 2–3 h | **Never cut** |
| 2 | Workspace boundary and safe change lifecycle | 2–3 h | **Never cut** |
| 3 | Model backend (mock first), controller, end-to-end run in tests | 2–3 h | **Never cut** |
| 4 | CLI experience: approval prompt, trace, report, revert | 1.5–2.5 h | Rich styling can be cut |
| 5 | Hardening and failure paths | 1–2 h | Trim edge cases last |
| 6 | Repo, docs, clean-checkout test | 1–1.5 h | Required |
| 7 | Demo video and submission | 1.5–2.5 h | Required |

That is roughly a full day of focused work, more than the pack's advertised "2–4 hours." If time is short, use the cut line at the end.

---

## Phase 0 — Setup and planning

**Goal:** a fresh project folder, approved planning documents, and every blocking decision made.

**Steps**
1. **Confirm the deadline** and write it down. Plan phase times backwards from it.
2. **Create an empty folder** and run `git init`. Do **not** copy anything from June. Devo is a new project.
3. **Install the Skill Pack** (needs Node.js and Git, only for this step):
   `npx skills add challengepost/learn-ai-basics --all -y`
4. **Set up Python:** create a virtual environment (`python -m venv .venv`), activate it, and note your Python version.
5. **First commit**, done early so history shows new work and secrets never enter it:
   - `LICENSE` (open-source; the choice is yours)
   - `.gitignore` containing at least `.env*`, `.venv/`, `__pycache__/`, `.devo-runs/`, `demo/workspace/`, `devpost/learner-profile.md`
   - A short README stub
6. **Run the skills in order** inside your coding agent: `1-start`, `2-scope`, `3-prd`, `4-spec`.
   - Put `devoV1.md`, `devoV1_improvements.md`, `architectural.md` and this file in `docs/brief/` and use them as input to your `2-scope` brain dump.
   - **Answer the interview yourself.** Expect the agent to push back and cut. Don't paste pre-written planning documents in their place; Stage One judging checks that the pack's process produced `scope.md`, `prd.md` and `spec.md`.
   - In the PRD interview, describe the **terminal experience** (what the run looks like), since the UI is a CLI.
7. **Decide and record:**
   - **(your call)** The specific target user.
   - Python version, pytest version, and how project `pytest` config/`conftest.py` is handled.
   - How `confirmed_min` works and the skipped-test policy.
   - Which model backends to build beyond mock.
   - CLI command and option names; plain vs `rich` output.
   - Time box per phase and the cut order.
8. **Verify pytest's real behavior before relying on it.** In a scratch folder, run `pytest --junitxml=out.xml` on tiny test files for: all passing, one failing, no tests, and a syntax error. Look at the actual exit codes and XML. Write down what you see; the verdict table must match reality, not memory.

**Done when**
- `devpost/scope.md`, `prd.md` and `spec.md` exist with `status: approved`.
- Python/pytest versions and the config/conftest handling are written in `spec.md`.
- The audience statement is in your own words.

**Commit point:** "Add approved planning documents."

---

## Phase 1 — Verdict engine, runner, parser and seeded demo project

**Goal:** the trustworthy core, working with no model and no CLI.

**Why first:** if everything else slips, a correct verdict engine and runner are still a demonstrable product and the thing judges remember.

**Steps**
1. **Package skeleton:** `pyproject.toml` (pinned Python, dependencies `pytest`, `defusedxml`), `src/devo/` layout from `architectural.md` section 4 (create folders as you need them), `pip install -e .`.
2. **Seeded demo project** in `demo/seed/`: a tiny Python project with one planted bug and 4–6 pytest tests, no extra dependencies. Add the `demo-reset` logic (copy seed → `demo/workspace`).
3. **Capture real outputs** from the seed for: all passing, one failing, zero tests collected, a collection error (syntax error), and a hang. Save the junit XML and exit codes as test fixtures. Write the parser from these captures, not from memory of the format.
4. **Write the `compute_verdict` tests first** (table-driven, see `architectural.md` section 13), then implement `verdict/compute_verdict.py` until they pass.
5. **Parser** (`runner/parse_junit.py`): `defusedxml`, size cap, reject DOCTYPE/entity tricks, return `ok: false` for anything unreadable. Tests include an oversized file and a hostile one.
6. **Preset** (`runner/presets.py`): the one built-in pytest check (argv list, junit path in a temp dir outside the workspace, default timeout, output cap).
7. **Runner** (`runner/run_check.py`): `shell=False`, fixed cwd, timeout with process-tree kill, output cap, scrubbed environment. Return a `CheckResult`. **Test the tree kill on the OS you'll demo on.**
8. **Runner tests:** timeout kills the process and its children, output is capped, a missing command gives `spawn_error`, a planted fake key is absent from the child's environment.

**Done when**
- `pytest` passes for Devo's own tests, including the whole verdict table.
- Running the runner on `demo/workspace` yields correct `CheckResult`s for pass, fail, zero-test, collection-error and timeout cases.
- The unmodified seed gives a baseline **failing** result (the planted bug).

**Commit point:** "Verdict engine, runner, junit parser and demo seed with tests."

---

## Phase 2 — Workspace boundary and safe change lifecycle

**Goal:** Devo can only touch the selected folder, and only writes with approval, with a safe way back.

**Steps**
1. **Boundary** (`workspace/boundary.py`): `resolve()` + containment. Tests first: `../x`, absolute path, symlink pointing outside, path equal to the workspace root.
2. **Inspection** (`workspace/inspect.py`): filtered list and read (skip `.git`, `.venv`, `__pycache__`, `.env*`, binary, oversized). Each read emits a trace event. Tests for the filters.
3. **Trace and redaction** (`trace/trace.py`, `trace/redact.py`): ordered events with timestamps written to `trace.jsonl`; a planted key never appears in output or files.
4. **Edit validation and apply** (`workspace/edits.py`): `old_str` must appear exactly once; path inside the workspace; size and count limits; explicit line-ending and encoding handling. Tests for missing, duplicate, outside-path, CRLF and non-ASCII cases.
5. **Diff** (`workspace/diff.py`): `difflib` unified diff from real before/after contents. Flag edits that touch test files.
6. **Approval** (`controller/approval.py`): one-time token bound to the SHA-256 of the exact diff. Apply refuses without a valid token. Tests: no token, wrong token, token for a different diff.
7. **Backup and revert** (`workspace/backup.py`): copy originals to `.devo-runs/<run-id>/backup/`, record hashes at apply time, restore on revert. Revert refuses or warns if files changed since apply. Tests: restore matches the original; refusal on changed files.

**Done when**
- All boundary, approval, edit and revert tests pass.
- From a short Python script you can: build a hand-written edit, see its diff, fail to apply it without approval, apply it with approval, then revert and get byte-identical files.

**Commit point:** "Workspace boundary, diff, approval gate, backup and revert with tests."

---

## Phase 3 — Model backend, controller and an end-to-end run in tests

**Goal:** the full journey works end to end on the mock backend, driven by tests, before any CLI polish.

**Why this order:** a working journey proves the architecture. The CLI is then a thin layer on top, and presentation problems can't hide logic problems.

**Steps**
1. **Schema and adapter interface** (`model/schema.py`, `model/adapter.py`): the shape in `architectural.md` section 6. Reject malformed output with a clear error and no endless retry.
2. **Mock backend** (`model/mock.py`) and three fixtures in `fixtures/model/`:
   - `scenario_verified.json`: fixes the planted bug.
   - `scenario_failed.json`: a wrong fix that fails the tests.
   - `scenario_not_verified.json`: introduces an infinite loop so the check times out.
   Record fixtures against the real seed so `old_str` matches exactly.
3. **Controller state machine** (`controller/states.py`, `controller/run.py`): implement the lifecycle in `architectural.md` section 5. Baseline runs before apply. A baseline that can't complete stops the run as Not verified before any edit.
4. **Integration tests** (mock backend, approval supplied by an explicit test callback): the three scenarios end to end, asserting the verdict state, evidence label (`red_to_green` for the verified scenario) and that rejecting leaves files untouched.
5. **Optional backends** (`model/api.py`, `model/local.py`, `model/prompts.py`): build only after mock mode is solid, and never make them required. Keys come from environment variables; add `.env.example` with placeholders only. Files go into prompts as untrusted data and output is validated against the schema. For a local model, verify the setup yourself first and expect malformed output from small models.

**Done when**
- The three mock scenarios produce Verified, Verification failed and Not verified, with correct traces.
- Resetting the demo and running again gives the same results every time.
- If you built an optional backend, it works once on the seed. If not, mock mode still carries the project.

**Commit point:** "Controller, mock backend and end-to-end scenarios."

---

## Phase 4 — CLI experience

**Goal:** a complete, clear terminal journey a first-time user can follow, and the thing you'll show in the video.

**Steps**
1. **Commands** (`cli.py`, `__main__.py`): `run`, `revert`, `demo-reset` with the options in `architectural.md` section 11 (final names from your spec).
2. **Header and mode label:** show workspace, preset and backend, with an unmistakable `MOCK MODE` label for the mock backend.
3. **Live trace** lines as each step happens, including the baseline command and cwd before it runs.
4. **Plan and diff view** (`report/render.py`): plan summary plus the unified diff, with test-file edits flagged.
5. **Approval prompt:** the user must type a specific word. A bare Enter does not approve. Non-interactive stdin refuses to apply. No `--yes` flag in V1.
6. **Output hygiene** (`report/sanitize.py`): strip escape sequences and control characters from all model, repo and test output before display. Tests with ANSI injection strings.
7. **Report:** verdict as a text label (`[VERIFIED]`, `[FAILED]`, `[NOT VERIFIED]`), evidence label and caveats, test counts, command, cwd, exit code, duration, truncated output, and the model's explanation under a separate heading marked as not evidence. Color is optional and never the only cue.
8. **Run artifacts:** write `trace.jsonl`, `report.json` and the backup under `.devo-runs/<run-id>/`. Add the Revert prompt and the `revert` command.
9. **Optional:** Devo's own exit codes (`0` Verified, `1` failed, `2` not verified, `3` error/rejected) and `rich` styling.
10. **Wording check:** nowhere says "works" or "success" where it should say "passed N tests" or the plain verdict name.

**Done when**
- You can complete all three scenarios from a clean `demo-reset` using only the CLI.
- Approve is the only way a write happens; Reject leaves files untouched; a bare Enter doesn't approve.
- The three verdicts are visually and textually distinct in a screen recording.

**Commit point:** "CLI experience for the full journey."

---

## Phase 5 — Hardening and failure paths

**Goal:** it fails honestly and stays safe on the awkward cases.

**Steps**
1. **Walk the table** in `architectural.md` section 12 and confirm each control has a passing test or a manual check.
2. **Edge cases:** malformed model output; an edit that doesn't match; very large file; binary file; CRLF vs LF; non-ASCII text; edit to a test file; model deleting tests (confirm the executed-count check catches it with a fixture); a collection error caused by the edit (should be Verification failed).
3. **Process handling:** hung check killed with its children and reported; output flood capped; any tool or model error ends as Not verified, never as success.
4. **Revert edge cases:** after a verified run; after a failed run; refused when files changed afterward; `revert` from a new process.
5. **Platform check:** run the full journey on the OS you'll record on. Process-tree kill and path handling differ between Windows and macOS/Linux; state in the README what you tested and don't claim others.
6. **Safety review:** search the code for any place that builds a command string, uses a path without `boundary.py`, prints untrusted text without `sanitize.py`, or could send a secret to logs or the child environment.

**Done when**
- Every row of the security table is covered and all tests pass.
- No error path can print a Verified verdict.

**Commit point:** "Hardening and edge-case tests."

---

## Phase 6 — Repo and docs

**Goal:** a stranger can clone it, run it and understand it.

**Steps**
1. **README:** what Devo is, the verdict model in plain words, setup (create venv, `pip install -e .`, `demo-reset`, `run`), mock vs optional backends, how to run tests, the platform and Python/pytest versions you tested, and the honest limits: **not a sandbox**, evidence not proof, pytest-only in V1, the config/conftest handling.
2. **Planning documents** present in `devpost/`: `scope.md`, `prd.md`, `spec.md`, `checklist.md`, `app-map.html`. Review them for private information. `learner-profile.md` stays out of the public repo.
3. **Disclosure:** state that Devo is a new project informed by lessons from June, with no June code copied, and list any pre-existing code, libraries or starter material used.
4. **Secret scan:** check tracked files and the full git history for keys and personal data before publishing. If something sensitive is in history, stop and fix it (rotate any exposed key); don't silently rewrite history.
5. **Clean-checkout test:** clone into a new empty folder, follow only the README, and run the mock journey. Fix whatever breaks.
6. **Make the repo public** (only when you've decided to), and confirm the license is detected in the repository's About section.

**Done when**
- A fresh clone runs the mock journey using only the README.
- The license shows in the About section.
- No secrets or personal files are tracked or in history.

**Commit point:** "Docs, license and clean-checkout fixes."

---

## Phase 7 — Demo and submission

**Goal:** a short video that shows it working, and a submission you wrote yourself.

**Steps**
1. **Prepare the recording:** `demo-reset`, enlarge the terminal font, close notifications and unrelated windows, and make sure no key, `.env` or personal data is visible. Dry-run all three scenarios.
2. **Record under 3 minutes** (aim for about 2:30) on the machine Devo was built for:
   - The problem and who it's for, in your own words.
   - **Verified** run: task → inspect → baseline → plan → diff → approve → check output and exit code → verdict.
   - **Verification failed** run: wrong edit → failure → Revert.
   - **Not verified** run: the check times out and is labeled honestly. Use a short timeout so you don't wait on camera.
   - A one-line close on the principle.
3. **No third-party trademarks or copyrighted music** in the video.
4. **Upload** to YouTube or Vimeo, set it **public**, and open the link in a logged-out window to confirm it plays.
5. **Write the submission yourself:** project name, description, other form fields and exit-survey answers. The pack's agent may correct spelling and grammar only; it won't draft or rewrite your copy, and you shouldn't ask it to.
6. **Check the form's requirements:** public repo URL, video link, text description and any other required fields on the current form.
7. **Submit on Devpost** and confirm the submission shows as received.

**Done when**
- The video link works while logged out and is under 3 minutes.
- The repo link works while logged out.
- You've submitted and seen the confirmation.

---

## Cut line (if time runs short)

Cut in this order, top first:
1. `rich` styling and other terminal polish (plain text labels are enough).
2. Optional backends (`api`, `local`); mock mode alone satisfies "runs with no key."
3. Edge-case tests beyond the security table's core rows.
4. Test-file highlighting in the diff.

**Do not cut:** the verdict engine, baseline-before-apply ordering, the approval gate, the workspace boundary, Revert, the failure scenario, the README's honest limits, the license, or the planning documents.

---

## Risks and fallbacks

| Risk | Fallback |
|---|---|
| pytest's exit codes or XML differ from what the verdict table assumes | Phase 0 step 8 and Phase 1 step 3 capture real outputs; fix the table to match reality |
| Process-tree kill doesn't work on your OS | Test in Phase 1; use platform-specific handling or `psutil`, and say what you tested |
| Project pytest config or `conftest.py` skews results | Use a Devo-supplied config and support only simple projects; document it |
| Optional model backends produce malformed edits | Keep mock mode for the demo, labeled clearly; treat bad output as Not verified |
| Verdict logic has a hole | The table-driven tests exist for this; add a row for every bug you find |
| Running out of time | Apply the cut line; a smaller journey that is correct beats a larger one that isn't |
| Overclaiming in output or video | Re-read every sentence for "works"/"success"; use "passed N tests" and the verdict names |

---

## Final checklist (before you submit)

- [ ] New project from an empty folder; no June code copied; lineage disclosed
- [ ] `scope.md`, `prd.md`, `spec.md` in the public repo; learner profile excluded
- [ ] Public repo with a detectable open-source license
- [ ] README setup works from a clean clone
- [ ] Mock mode runs with no API key; no secrets in files or history
- [ ] Verdict computed only by the harness; all three outcomes demonstrated
- [ ] Baseline runs before apply; approval bound to the diff; Revert works
- [ ] Demo under 3 minutes, public, plays logged-out
- [ ] Submission copy and exit survey written by you
