"""Core Run Controller orchestrating the full verification journey."""
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable
from devo.controller.approval import mint_approval_token
from devo.controller.states import RunState
from devo.model.adapter import ModelAdapter
from devo.model.schema import ModelProposal
from devo.runner.presets import get_preset
from devo.runner.run_check import run_check
from devo.trace.trace import TraceEmitter, TraceEvent
from devo.verdict.compute_verdict import CheckResult, Verdict, compute_verdict
from devo.workspace.boundary import resolve_safe_path
from devo.workspace.diff import DiffResult
from devo.workspace.edits import apply_validated_edits, prepare_and_validate_edits
from devo.workspace.inspect import inspect_workspace


@dataclass
class RunReport:
    run_id: str
    state: RunState
    verdict: Verdict
    baseline: CheckResult | None = None
    final: CheckResult | None = None
    proposal: ModelProposal | None = None
    diff: DiffResult | None = None
    events: list[TraceEvent] = None


def execute_run(
    workspace: Path | str,
    task: str,
    model_adapter: ModelAdapter,
    preset_name: str = "pytest",
    approval_callback: Callable[[DiffResult], bool] | None = None,
    timeout_override: float | None = None,
    confirmed_min: int = 0,
    run_id: str | None = None,
    runs_dir: str = ".devo-runs",
) -> RunReport:
    """Execute the complete Devo verification state machine.

    1. WORKSPACE_SELECTED
    2. INSPECTING
    3. BASELINE_RUNNING (stops as NOT_VERIFIED if baseline cannot complete)
    4. PLANNING
    5. DIFF_READY
    6. AWAITING_APPROVAL -> REJECTED if declined (no writes occur)
    7. APPLYING (backup & hash-checked apply)
    8. FINAL_RUNNING
    9. DONE -> compute_verdict
    """
    run_id = run_id or str(uuid.uuid4())[:8]
    ws = Path(workspace).resolve()

    trace_log = ws / runs_dir / run_id / "trace.jsonl"
    emitter = TraceEmitter(trace_log)

    current_state = RunState.WORKSPACE_SELECTED
    emitter.emit(current_state.value, "workspace", str(ws))

    # Validate workspace
    if not ws.is_dir():
        v = Verdict(state="NOT_VERIFIED", evidence="none", reasons=[f"Workspace not found: {ws}"])
        emitter.emit(RunState.ERROR.value, "error", v.reasons[0])
        return RunReport(run_id=run_id, state=RunState.ERROR, verdict=v, events=emitter.events)

    preset = get_preset(preset_name)

    # 2. INSPECTING
    current_state = RunState.INSPECTING
    emitter.emit(current_state.value, "start", "Inspecting candidate source files")
    files = inspect_workspace(ws, emitter=emitter)

    # 3. BASELINE_RUNNING
    current_state = RunState.BASELINE_RUNNING
    emitter.emit(current_state.value, "start", f"Running baseline check ({preset_name})")
    baseline_result = run_check(ws, preset=preset, timeout_override=timeout_override)
    emitter.emit(
        current_state.value,
        "completed",
        f"Exit: {baseline_result.exit_code}, Tests: {baseline_result.tests}, Failures: {baseline_result.failures}",
    )

    # If baseline fails to complete (timeout, spawn error, unusable), halt before editing
    if baseline_result.status != "completed" or not baseline_result.junit_ok:
        v = Verdict(
            state="NOT_VERIFIED",
            evidence="none",
            reasons=[f"Baseline check failed to complete cleanly: {baseline_result.status} (junit_ok={baseline_result.junit_ok})"],
        )
        emitter.emit(RunState.ERROR.value, "halt", v.reasons[0])
        return RunReport(
            run_id=run_id,
            state=RunState.ERROR,
            verdict=v,
            baseline=baseline_result,
            events=emitter.events,
        )

    # 4. PLANNING
    current_state = RunState.PLANNING
    emitter.emit(current_state.value, "start", f"Requesting model proposal for task: '{task}'")
    try:
        proposal = model_adapter.propose_edits(task=task, files=files, baseline=baseline_result)
        emitter.emit(current_state.value, "proposal", f"Plan: {proposal.plan.summary}")
    except Exception as err:
        v = Verdict(state="NOT_VERIFIED", evidence="none", reasons=[f"Model proposal failed: {err}"])
        emitter.emit(RunState.ERROR.value, "error", v.reasons[0])
        return RunReport(
            run_id=run_id,
            state=RunState.ERROR,
            verdict=v,
            baseline=baseline_result,
            events=emitter.events,
        )

    # 5. DIFF_READY
    current_state = RunState.DIFF_READY
    edits_as_dict = [asdict(e) for e in proposal.edits]
    try:
        _, diff_result = prepare_and_validate_edits(ws, edits_as_dict)
        emitter.emit(
            current_state.value,
            "diff",
            f"Diff generated for {len(diff_result.modified_files)} files (touches_tests={diff_result.touches_tests})",
        )
    except Exception as err:
        v = Verdict(state="NOT_VERIFIED", evidence="none", reasons=[f"Edit validation failed: {err}"])
        emitter.emit(RunState.ERROR.value, "error", v.reasons[0])
        return RunReport(
            run_id=run_id,
            state=RunState.ERROR,
            verdict=v,
            baseline=baseline_result,
            proposal=proposal,
            events=emitter.events,
        )

    # 6. AWAITING_APPROVAL
    current_state = RunState.AWAITING_APPROVAL
    emitter.emit(current_state.value, "prompt", "Awaiting human approval token")

    approved = False
    if approval_callback is not None:
        approved = approval_callback(diff_result)

    if not approved:
        current_state = RunState.REJECTED
        emitter.emit(current_state.value, "rejected", "User declined or failed to approve the proposed diff")
        v = Verdict(state="NOT_VERIFIED", evidence="none", reasons=["Run was rejected by user; no files modified."])
        return RunReport(
            run_id=run_id,
            state=RunState.REJECTED,
            verdict=v,
            baseline=baseline_result,
            proposal=proposal,
            diff=diff_result,
            events=emitter.events,
        )

    # 7. APPLYING
    current_state = RunState.APPLYING
    approval_token = mint_approval_token(diff_result.diff_text)
    emitter.emit(current_state.value, "apply", f"Applying diff with token {approval_token[:12]}...")

    apply_validated_edits(ws, edits_as_dict, approval_token=approval_token, run_id=run_id)

    # 8. FINAL_RUNNING
    current_state = RunState.FINAL_RUNNING
    emitter.emit(current_state.value, "start", f"Running final check ({preset_name})")
    final_result = run_check(ws, preset=preset, timeout_override=timeout_override)
    emitter.emit(
        current_state.value,
        "completed",
        f"Exit: {final_result.exit_code}, Tests: {final_result.tests}, Failures: {final_result.failures}",
    )

    # 9. DONE & VERDICT
    current_state = RunState.DONE
    verdict = compute_verdict(baseline=baseline_result, final=final_result, confirmed_min=confirmed_min)
    emitter.emit(current_state.value, "verdict", f"{verdict.state} ({verdict.evidence})")

    return RunReport(
        run_id=run_id,
        state=RunState.DONE,
        verdict=verdict,
        baseline=baseline_result,
        final=final_result,
        proposal=proposal,
        diff=diff_result,
        events=emitter.events,
    )
