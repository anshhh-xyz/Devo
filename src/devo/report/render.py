"""Terminal rendering of headers, diff views, and honest verdict reports."""
import sys
from devo.controller.run import RunReport
from devo.report.sanitize import sanitize_terminal_output
from devo.workspace.diff import DiffResult


def print_banner(workspace: str, preset: str, backend: str, scenario: str | None = None) -> None:
    """Render the startup banner with clear mode identification."""
    print("=" * 70)
    print(" DEVO — EVIDENCE-FIRST CODING ASSISTANT")
    print("=" * 70)
    print(f" Workspace: {workspace}")
    print(f" Preset:    {preset}")
    if backend.lower() == "mock":
        print(f" Backend:   [MOCK MODE: replaying fixture '{scenario or 'default'}']")
    else:
        print(f" Backend:   {backend}")
    print("-" * 70)


def render_diff_view(diff_result: DiffResult) -> None:
    """Render unified diff with explicit notice if test files are modified."""
    print("\n" + "=" * 70)
    print(" PROPOSED UNIFIED DIFF")
    print("=" * 70)

    if diff_result.touches_tests:
        print(" [!] CAUTION: This change modifies test files:")
        for f in diff_result.modified_files:
            print(f"     * {f}")
        print("     Ensure this edit does not weaken or delete assertions.")
        print("-" * 70)

    sanitized_diff = sanitize_terminal_output(diff_result.diff_text)
    print(sanitized_diff if sanitized_diff.strip() else "(No diff lines produced)")
    print("=" * 70)


def render_final_report(report: RunReport) -> None:
    """Render the comprehensive, honest verdict report."""
    v = report.verdict
    print("\n" + "=" * 70)
    print(f" VERDICT: [{v.state}]")
    print(f" Evidence Category: {v.evidence}")
    print("=" * 70)

    if v.reasons:
        print("\nFindings:")
        for r in v.reasons:
            print(f"  * {r}")

    if v.caveats:
        print("\nCaveats & Notes:")
        for c in v.caveats:
            print(f"  ! {c}")

    if report.final:
        f = report.final
        print("\nFinal Check Details:")
        print(f"  * Status: {f.status} | Exit Code: {f.exit_code} | Duration: {f.duration_ms}ms")
        print(f"  * Tests Executed: {f.executed} (Total: {f.tests}, Failures: {f.failures}, Errors: {f.errors}, Skipped: {f.skipped})")
        if f.stdout and (f.failures > 0 or f.errors > 0 or v.state != "VERIFIED"):
            print("\nTest Output Summary:")
            clean_out = sanitize_terminal_output(f.stdout[-1500:])
            print("  " + "\n  ".join(clean_out.strip().splitlines()))

    if report.proposal and report.proposal.plan.approach:
        print("\nModel's Stated Approach (Informational — NOT Evidence):")
        clean_app = sanitize_terminal_output(report.proposal.plan.approach)
        print(f"  {clean_app}")

    print("\n" + "-" * 70)
    print(f"Run ID: {report.run_id}")
    if report.diff and report.state.value in ("DONE", "ERROR"):
        print(f"To undo this change at any time, run: python -m devo revert --run {report.run_id}")
    print("=" * 70 + "\n")
