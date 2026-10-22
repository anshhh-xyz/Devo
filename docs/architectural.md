# Devo — Architecture (Python, CLI)

> **Status: proposed design, not yet built or tested.** Stack choices are defaults to carry into the Devpost Learn Skill Pack's `4-spec` stage, where you make the final decisions. Details that depend on your actual Python, pytest or OS versions are marked **verify** and must be checked against real output before you rely on them.

Devo is an **evidence-first coding assistant**. It makes one approved code change in a local Python project, runs a fixed check before and after, and reports what the check actually showed. It is a command-line tool. It is not a general autonomous agent.

**Core rule:** the model may propose plans and edits. Only the controller computes the verdict, from real process results. Model prose never influences it.

**On UI:** the Devpost requirements (project requirements, submission requirements, judging criteria) do not ask for a graphical or web UI. They require a working proof of concept that performs at least one function end to end, a public repo, a text description and a demo video. A well-presented terminal app satisfies "Design" as long as the experience is complete and coherent. V1 has **no web UI**.

---

## 1. Goals and non-goals

**Goals**
- One complete journey: task → inspect → baseline → plan → diff → approve → apply → final check → verdict → report/revert.
- Verdicts a user can trust: Verified, Verification failed, Not verified.
- Safe by construction: workspace boundary, approval gate enforced in code, no model-chosen commands, rollback.
- Runs on a normal desktop with no API key (mock mode).

**Non-goals (V1)**
- Any web or graphical UI.
- Multi-agent, RAG/vector DB, long-term memory, background daemon, GitHub sync, unrestricted shell, plugins, multiple runners/languages, run history browser, one-click rerun.
- Being a sandbox. Tests run with your user's permissions; use only trusted projects.
- Proving the app is bug-free. A passing suite is evidence for the behavior it covers.

---

## 2. Proposed tech stack

| Layer | Proposal | Why | Verify in `4-spec` |
|---|---|---|---|
| Language | Python (pin a minimum version in `pyproject.toml`, e.g. 3.10+) | Matches your background; strong stdlib for paths, subprocess, diffs, hashing, XML | Pin the exact version you'll demo on |
| Packaging | `pyproject.toml`, virtualenv, `pip install -e .` | Standard, simple setup | Setup works from a clean clone |
| CLI | `argparse` (stdlib), run as `python -m devo` | No dependency, enough for 3 commands | A different CLI library is fine if you prefer it |
| Terminal output | Plain text by default; `rich` optional for panels and colored diffs | Clear demo footage | **Meaning must never depend on color alone:** use text labels such as `[VERIFIED]`, `[FAILED]`, `[NOT VERIFIED]` |
| Supported check (V1) | `pytest` with `--junitxml` | Structured results with tests / failures / errors / skipped counts; a distinct exit code when no tests are collected | **Confirm the exact XML fields and exit codes on your pytest version using real captured output** |
| XML parsing | `defusedxml` (or stdlib with a size cap and DOCTYPE rejection) | The XML is produced by a run of untrusted code, so treat it as untrusted input | Pick one and test an oversized/hostile file |
| Subprocess | `subprocess` with an argument list, `shell=False`, timeout | No shell injection surface | **Verify process-tree kill on your demo OS** (POSIX: new session + process-group kill; Windows: process-group flags plus a tree kill, or `psutil`) |
| Diff / hashing | `difflib.unified_diff`, `hashlib.sha256` (stdlib) | Harness builds the diff itself | None |
| Paths | `pathlib.Path.resolve()` + `is_relative_to` | Boundary checks | Test symlinks/junctions on your OS |
| Model access | Provider-agnostic adapter (see section 10) | Mock needs no key; live optional | Confirm the provider's terms permit your use |
| Config / secrets | Environment variables, `.env.example` with placeholders | Keys never in the repo | `.env*` gitignored |
| Devo's own tests | `pytest` | Same tool you already use | None |

Minimal dependencies: `pytest`, `defusedxml`, optionally `rich`, and a provider SDK only if you build live API mode.

**Node.js is still needed once**, to install the Skill Pack with `npx skills add ...` as the hackathon instructs. Devo itself does not use Node.

---

## 3. System overview

```
                      ┌──────────────────────────────┐
                      │ CLI  (python -m devo run …)  │
                      │ prompts · trace · diff view  │
                      │ approval prompt · report     │
                      └──────────────┬───────────────┘
                                     │
                      ┌──────────────▼───────────────┐
                      │ Run Controller               │
                      │ state machine · approval gate│
                      │ trace emitter                │
                      └─┬──────┬─────────┬─────────┬─┘
        ┌───────────────┘      │         │         └───────────────┐
┌───────▼──────────┐ ┌─────────▼───────┐ │           ┌─────────────▼────────────┐
│ Workspace layer  │ │ Model backend   │ │           │ Check runner             │
│ boundary·inspect │ │ mock|api|local  │ │           │ preset argv, no shell    │
│ edits·diff·backup│ │ structured edits│ │           │ timeout·cap·scrubbed env │
└──────────────────┘ └─────────────────┘ │           │ junit XML parser         │
                                         │           └─────────────┬────────────┘
                              ┌──────────▼─────────┐               │
                              │ compute_verdict    │◄──────────────┘
                              │ (pure function)    │   CheckResult
                              └────────────────────┘
```

**Trust boundaries**
- The **model**, the **workspace contents** and **everything the tests print or write** are untrusted. They can supply text; they cannot run commands, write files or set the verdict.
- The **controller, workspace layer, runner and verdict engine** are trusted code that enforce every rule.
- The **user, typing at the approval prompt,** is the only party who can approve a write.

---

## 4. Directory structure

```
devo/
├── README.md                     setup, usage, honest limits ("not a sandbox")
├── LICENSE                       open-source license (first commit)
├── pyproject.toml                package metadata, pinned Python, dependencies
├── .gitignore                    .env*, .venv/, __pycache__/, .devo-runs/, demo/workspace/,
│                                 devpost/learner-profile.md
├── .env.example                  placeholders only, never real keys
│
├── devpost/                      Skill Pack outputs (required by the hackathon)
│   ├── scope.md
│   ├── prd.md
│   ├── spec.md
│   ├── checklist.md
│   ├── app-map.html
│   └── learner-profile.md        gitignored; stays out of the public repo
│
├── docs/
│   ├── architectural.md          this file
│   ├── roadmap.md
│   └── brief/                    devoV1.md, devoV1_improvements.md
│
├── src/devo/
│   ├── __init__.py
│   ├── __main__.py               enables `python -m devo`
│   ├── cli.py                    argparse commands: run, revert, demo-reset
│   ├── controller/
│   │   ├── run.py                state machine, orchestrates one run
│   │   ├── states.py             state names, allowed transitions
│   │   └── approval.py           approval token bound to the diff hash
│   ├── workspace/
│   │   ├── boundary.py           resolve + containment, traversal/symlink rejection
│   │   ├── inspect.py            filtered list/read (skip .git, .venv, .env*, binary, oversized)
│   │   ├── edits.py              validate structured edits, apply them
│   │   ├── diff.py               harness-built unified diff
│   │   └── backup.py             backup, record hashes, hash-checked revert
│   ├── runner/
│   │   ├── presets.py            built-in check presets (argv template, parser id, limits)
│   │   ├── run_check.py          subprocess, timeout, output cap, env scrub, tree kill
│   │   └── parse_junit.py        junit XML → counts (untrusted input)
│   ├── verdict/
│   │   └── compute_verdict.py    pure function; the most thoroughly tested file
│   ├── model/
│   │   ├── adapter.py            interface: propose_edits(input) -> {plan, edits}
│   │   ├── mock.py               replays fixtures by scenario name
│   │   ├── api.py                optional hosted provider, key from env
│   │   ├── local.py              optional local model server
│   │   ├── prompts.py            files passed as untrusted data
│   │   └── schema.py             validates model output shape
│   ├── trace/
│   │   ├── trace.py              ordered event log for one run
│   │   └── redact.py             strips secrets from logs and output
│   └── report/
│       ├── sanitize.py           strips terminal escape/control chars from untrusted text
│       └── render.py             diff view, trace lines, verdict report
│
├── fixtures/
│   └── model/
│       ├── scenario_verified.json
│       ├── scenario_failed.json
│       └── scenario_not_verified.json
│
├── demo/
│   ├── seed/                     tracked: tiny Python project, planted bug, pytest tests
│   └── workspace/                gitignored: working copy Devo edits
│
├── .devo-runs/                   gitignored: per-run trace.jsonl, report.json, backup/
│
└── tests/
    ├── unit/                     verdict, parser, boundary, diff, edits, redact, sanitize
    └── integration/              full runs of the three scenarios (mock backend)
```

Keeping the pristine seed separate from the editable workspace makes the demo repeatable: `python -m devo demo-reset` before every take. Backups live under `.devo-runs/<run-id>/backup/`, outside the workspace, so Revert can work even after the process exits.

---

## 5. Run lifecycle (state machine)

```
IDLE
  → WORKSPACE_SELECTED     workspace path validated, check preset chosen
  → INSPECTING             filtered reads, each logged to the trace
  → BASELINE_RUNNING       check on the ORIGINAL files (command + cwd shown first)
  → PLANNING               model proposes plan + structured edits
  → DIFF_READY             harness builds diff; nothing written yet
  → AWAITING_APPROVAL      user approves or rejects at the prompt
       ├─ reject → REJECTED (no writes ever happened)
       └─ approve → APPROVED
  → APPLYING               backup, record hashes, apply edits
  → FINAL_RUNNING          same check, same preset
  → DONE                   verdict computed, report shown
       └─ revert → REVERTED

Any failure at any step → ERROR → report with verdict Not verified.
```

Rules:
- **Baseline always runs before apply.** If the baseline cannot complete (timeout, spawn error, unusable results), the run stops as **Not verified** before anything is edited.
- **Approval is a one-time token bound to the hash of the exact diff shown.** The only code path that mints it is the interactive approval prompt. If the diff changes, the token is invalid. Apply is rejected in code without a valid token.
- Every transition is recorded in the trace with a timestamp.
- V1 does not resume interrupted runs. An applied-but-unfinished change is recoverable through the saved backup via `devo revert`.

---

## 6. Core data shapes

**Proposed edits (from the model, validated by the harness)**
```json
{
  "plan": { "summary": "...", "files": ["src/mathutils.py"], "approach": "..." },
  "edits": [
    { "path": "src/mathutils.py", "old_str": "exact existing text", "new_str": "replacement" }
  ]
}
```
Validation: path inside the workspace; `old_str` appears **exactly once**; file size and edit count within limits; no edits to filtered paths. Invalid output sends the run to `ERROR` (Not verified) with a clear message. No endless retry loops in V1.

**CheckResult (from the runner)**
```json
{
  "status": "completed | timeout | spawn_error",
  "exit_code": 0,
  "duration_ms": 1234,
  "stdout": "...(truncated)",
  "stderr": "...(truncated)",
  "truncated": false,
  "junit": { "ok": true, "tests": 6, "failures": 0, "errors": 0, "skipped": 0 }
}
```
`junit` is `{ "ok": false, "reason": "..." }` when the XML is missing, oversized, hostile or invalid.

**Trace event** (one JSON object per line in `trace.jsonl`)
```json
{ "seq": 7, "ts": "...", "state": "INSPECTING", "kind": "read", "detail": "src/mathutils.py (412 bytes)" }
```

**Verdict (from `compute_verdict`)**
```json
{ "state": "VERIFIED | FAILED | NOT_VERIFIED", "evidence": "red_to_green | no_regression_only | none", "reasons": ["..."], "caveats": ["..."] }
```

---

## 7. Verdict engine

A separate, pure function: `compute_verdict(baseline, final, confirmed_min) -> Verdict`. No I/O, no model input. It is the most thoroughly tested file in the project.

Definitions:
- `executed = tests - skipped` from the junit counts.
- `expected = max(baseline.executed, confirmed_min, 1)`: the final run must execute at least as many tests as the baseline did (this catches a change that deletes or skips tests), at least any minimum you confirmed, and at least one.

Evaluate in this order:

1. `final.status` is `timeout` or `spawn_error` → **Not verified**.
2. pytest exit code 5 (no tests collected), 3 (internal error) or 4 (usage error), or junit missing/invalid → **Not verified**.
3. junit `failures + errors > 0`, or exit code 1 → **Verification failed**. This includes a collection error from an edit that broke a module (pytest reports it as an error). If the exit code and the XML disagree (for example exit 0 but recorded failures), report **Verification failed** and add a caveat.
4. `executed < expected` → **Not verified** ("fewer tests ran than expected").
5. Otherwise (exit 0, usable XML, no failures or errors, enough tests) → **Verified**, with an evidence label:
   - baseline failed, final passed → `red_to_green`: evidence the change fixed the tested behavior.
   - baseline passed, final passed → `no_regression_only`: evidence of no regression in those tests. It is **not** evidence that new behavior is correct unless a test exercises it.

A baseline that did not complete never reaches this function; the run stops earlier as Not verified.

**Verify against reality.** The exit-code meanings above are pytest's documented behavior as far as I know it, but they and the XML fields can vary by version. Capture real outputs for pass, fail, zero tests, collection error and timeout in Phase 1 and make the test table match what your pytest actually does.

**Wording rule.** The CLI, README and demo say "passed N tests," never "it works."

**Open decision for the spec:** whether an increase in skipped tests versus the baseline adds a caveat (default proposal) or blocks Verified. Decide it and test it.

---

## 8. Workspace layer

- **Boundary (`boundary.py`).** Resolve with `Path.resolve()`, then require the result to be inside the resolved workspace. Rejects `..`, absolute paths and symlinks pointing outside. Used by every read and write. Test on your demo OS (case-insensitivity, Windows junctions).
- **Inspection (`inspect.py`).** Lists and reads only what the task needs. Skips `.git`, `.venv`, `__pycache__`, `.env*`, binary and oversized files, and never sends their contents to the model. Every read is a trace event.
- **Edits (`edits.py`).** Applies validated search/replace edits. Rejects any edit that doesn't match exactly once. Handle line endings and encoding explicitly (decide in the spec).
- **Diff (`diff.py`).** The harness generates the unified diff from real before/after contents. The model's description of its change is never what the user approves.
- **Backup (`backup.py`).** Before writing, copy originals to `.devo-runs/<run-id>/backup/` and record SHA-256 hashes at apply time. Revert restores the originals; if a file changed since apply, Revert refuses or warns instead of overwriting the user's later work.
- **Test-file edits.** If the diff touches files matching test patterns (e.g. `test_*.py`, `tests/`), the report highlights this prominently. Changing the tests that judge the change deserves attention.

---

## 9. Check runner

- **Command source.** The command comes from a **built-in preset** (`presets.py`) that the user selects, never from the model and never from a file inside the workspace. Workspace files are untrusted, so a config file in the repo cannot define what runs.
- **Preset shape (proposal).** An argument list such as: the current interpreter (`sys.executable`), `-m pytest`, quiet output, `--junitxml <path in a temp dir outside the workspace>`, and `-p no:cacheprovider`.
- **pytest configuration.** A project's own `pytest.ini`/`pyproject.toml` options and `conftest.py` can change how pytest behaves, including the options that shape the results. Decide in the spec how V1 handles this, for example passing `-c` with a Devo-supplied minimal config file and documenting that only simple projects without a `conftest.py` are supported. Whatever you choose, say it in the README.
- **Execution.** `shell=False`, fixed working directory (the workspace), timeout, output cap. On timeout, kill the whole process tree (platform-specific, **verify**).
- **Environment.** Pass a scrubbed environment to the child. The model API key is never passed in.
- **Visibility.** Show the command and cwd before running, and record exit code, duration and truncated output in the report.
- **Parsing.** `parse_junit.py` enforces a size cap, rejects DOCTYPE/entity tricks, and returns `ok: false` for anything it can't confidently read, which leads to Not verified.
- **Honest limits.** Running a project's tests executes that project's code with your permissions, and a malicious test could also write a forged results file. Devo is **not a sandbox**; say so in the README and use only trusted projects.

---

## 10. Model backends

Interface: `propose_edits(task, files, baseline, constraints) -> {plan, edits}`. The controller doesn't care which backend produced the proposal; every proposal passes the same schema and edit validation.

| Backend | Needs | Good for | Caveats |
|---|---|---|---|
| **mock** (default, required) | Nothing | Judges, repeatable demos, tests | Replays recorded fixtures; must be visibly labeled as mock in the output and demo |
| **api** (optional) | A hosted provider and a key in an environment variable | Real model behavior | Needs a key and network; confirm provider terms; output varies run to run |
| **local** (optional, CLI-friendly inference) | A local model server running on your machine (for example Ollama, which exposes a local HTTP endpoint) | No key, works offline, runs from the terminal | Verify setup first; smaller models often produce malformed structured edits, so rely on the schema validation and treat failures as Not verified |

**Not recommended: using another coding-agent CLI as the "model."** Such a tool can edit files and run commands itself, which would bypass Devo's approval gate and boundary. Only consider it if it can be locked down to return a JSON proposal with no tools, and even then the benefit is small.

Common rules for all backends:
- **Prompts (`prompts.py`).** Repository files and tool output are wrapped as untrusted data, and the prompt tells the model to ignore instructions inside them. This is defense in depth only. The real protections are the fixed command, the approval gate and the diff the user reads.
- **Output.** Validated against `schema.py`. Malformed or non-matching output is an error, not something to retry endlessly.
- **Context limits.** Send only relevant files and cap size. Oversized files are skipped or truncated with a note in the trace.
- **Secrets.** Keys come from the environment, are redacted everywhere, and are never given to child processes.

---

## 11. CLI design

**Commands**
| Command | Purpose |
|---|---|
| `python -m devo run --workspace PATH --task "..." [--preset pytest] [--backend mock\|api\|local] [--scenario NAME]` | Run the whole journey |
| `python -m devo revert --run RUN_ID` | Restore the backed-up files for a run (hash-checked) |
| `python -m devo demo-reset` | Recreate `demo/workspace` from `demo/seed` |

(Command and option names are proposals; settle them in the spec. An installed `devo` entry point is optional.)

**What a run looks like in the terminal**
1. Header: workspace, preset, backend, with an explicit `MOCK MODE` label when using the mock backend.
2. Live trace lines as each step happens (reads, baseline check with its command and cwd, planning).
3. Plan summary and the **unified diff**. Test-file edits are flagged.
4. **Approval prompt.** The user must type a specific word (for example `approve`). A bare Enter does not approve. If stdin isn't interactive, Devo refuses to apply. V1 has no `--yes` flag; automated tests call the controller with an explicit approval callback instead.
5. Final check output summary, then the **report**: a clear verdict label, the evidence label and caveats, test counts, command, cwd, exit code, duration, truncated stdout/stderr, and the model's explanation under a separate heading marked as not evidence.
6. A Revert prompt (or the `revert` command later).

**Output hygiene.** Everything from the model, the repo and the test run is stripped of terminal escape sequences and control characters (`sanitize.py`) before display, so untrusted text can't fake a "VERIFIED" line or rewrite the screen. Secrets are redacted.

**Run artifacts.** Each run writes `trace.jsonl`, `report.json` and `backup/` under `.devo-runs/<run-id>/`.

**Devo's own exit code** (optional, useful for scripting and tests): `0` Verified, `1` Verification failed, `2` Not verified, `3` Devo error or rejected run.

---

## 12. Security and trust summary

| Risk | Control |
|---|---|
| Path traversal / symlink escape | Resolve + containment check on every read and write |
| Model or repo chooses a command | Commands only from built-in presets; no shell |
| Writes without consent | Approval token bound to diff hash, minted only by the interactive prompt, enforced in code |
| Diff changed after approval | Token invalid if the diff hash differs |
| Secret leakage | Key only via env; scrubbed child env; redaction in trace and output; `.env*` and `.devo-runs/` gitignored |
| Prompt injection from repo files | Untrusted-data prompting; fixed command; user reads the real diff |
| Runaway processes | Timeout, process-tree kill, output cap |
| Fake or hostile terminal output | `sanitize.py` strips escape/control characters from all untrusted text |
| Hostile or oversized junit XML | `defusedxml` or size cap + DOCTYPE rejection; anything unreadable is Not verified |
| Project pytest config / conftest skews results | Documented V1 handling (Devo-supplied config, simple projects only); stated in README |
| Model cheats by deleting tests | Executed-count check against the baseline; test-file edits highlighted |
| Broken project after failure | Backup and hash-checked Revert |
| Overclaiming | Verdict is harness-computed; wording says "passed N tests" |
| Arbitrary code in tests, forged results file | **Not mitigated.** Documented: Devo is not a sandbox |

If a web UI is ever added later, it would also need localhost-only binding, a per-launch token and Origin checks. That is out of scope for V1.

---

## 13. Testing strategy

Write tests in the phase that builds the code. Use `pytest` for Devo's own tests.

- **Verdict (table-driven):** exit 0 with enough tests; exit 0 with zero tests (code 5); exit 0 with fewer executed tests than baseline; unparseable/missing XML; exit 1 with failures; collection error counted as failed; exit 0 but XML shows failures; timeout; spawn error; baseline-fail → final-pass; baseline-pass → final-pass.
- **Parser:** real captured XML (pass, fail, zero tests, collection error), plus an oversized file and a file with a DOCTYPE/entity.
- **Boundary:** `../x`, absolute path, symlink to outside, filtered paths.
- **Approval gate:** apply with no token; apply with a token for a different diff hash.
- **Edits:** `old_str` missing, appears twice, path outside workspace, line-ending and non-ASCII cases.
- **Runner:** timeout kill (including child processes), output cap, missing command, key absent from child env.
- **Redaction and sanitize:** key never appears in trace/output; ANSI escapes and control characters in model/test output are stripped.
- **Revert:** restore matches the original; refuses when files changed after apply.
- **Integration (mock backend):** the three scenarios end to end with the expected verdict and evidence label.
- **CLI:** non-interactive stdin refuses to apply; a bare Enter at the approval prompt does not approve.

---

## 14. Demo scenarios

All three run on the mock backend against `demo/seed`, so they repeat exactly.

| Scenario | What the mock edit does | Expected result |
|---|---|---|
| Verified | Fixes the planted bug | Baseline failed → final passed: **Verified (red→green)** |
| Verification failed | Makes a wrong fix | Final check reports failing tests: **Verification failed**, then Revert |
| Not verified | Introduces an infinite loop | Check hits the timeout: **Not verified** (use a short timeout for the demo) |

---

## 15. Open decisions to settle in the Skill Pack

1. Target audience: one specific person. **Your call; don't let the agent decide.**
2. Final Python version, pytest version and how project pytest config/conftest is handled.
3. How `confirmed_min` is set (or whether the baseline count alone is enough), and the skipped-test policy.
4. Which model backends to build beyond mock, and the provider's terms if you build `api`.
5. CLI command and option names, and plain vs `rich` output.
6. Line-ending and encoding handling for edits.
7. Time box per phase and the cut line (see `roadmap.md`).
