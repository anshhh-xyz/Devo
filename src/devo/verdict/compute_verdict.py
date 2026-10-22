"""Pure function verdict engine."""
from dataclasses import dataclass, field


@dataclass
class CheckResult:
    status: str  # "completed", "timeout", "spawn_error"
    exit_code: int = 0
    duration_ms: int = 0
    stdout: str = ""
    stderr: str = ""
    truncated: bool = False
    junit_ok: bool = False
    tests: int = 0
    failures: int = 0
    errors: int = 0
    skipped: int = 0
    reason: str = ""

    @property
    def executed(self) -> int:
        return max(0, self.tests - self.skipped)


@dataclass
class Verdict:
    state: str  # "VERIFIED", "FAILED", "NOT_VERIFIED"
    evidence: str  # "red_to_green", "no_regression_only", "none"
    reasons: list[str] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)


def compute_verdict(baseline: CheckResult, final: CheckResult, confirmed_min: int = 0) -> Verdict:
    """Compute the verification verdict purely from baseline and final process results.

    Rule: The model prose never influences the verdict.
    """
    reasons: list[str] = []
    caveats: list[str] = []

    # 1. Check if the final run aborted due to timeout or spawn failure
    if final.status in ("timeout", "spawn_error"):
        return Verdict(
            state="NOT_VERIFIED",
            evidence="none",
            reasons=[f"Process did not complete cleanly ({final.status})"],
            caveats=caveats,
        )

    # 2. Check for missing or invalid junit XML
    if not final.junit_ok:
        return Verdict(
            state="NOT_VERIFIED",
            evidence="none",
            reasons=["JUnit XML was missing, unparseable, or invalid"],
            caveats=caveats,
        )

    # 3. Check for zero tests or pytest configuration/internal error exit codes
    # pytest exit codes: 0=all pass, 1=tests failed, 2=interrupted/syntax/collection error, 3=internal error, 4=command line usage error, 5=no tests collected
    if final.exit_code == 5 or final.tests == 0:
        return Verdict(
            state="NOT_VERIFIED",
            evidence="none",
            reasons=["No tests were collected or executed"],
            caveats=caveats,
        )

    if final.exit_code in (3, 4):
        return Verdict(
            state="NOT_VERIFIED",
            evidence="none",
            reasons=[f"Pytest exited with error code {final.exit_code}"],
            caveats=caveats,
        )

    # 4. Check for test failures or errors
    has_test_failures = final.failures > 0 or final.errors > 0
    has_failure_exit = final.exit_code in (1, 2)

    if has_test_failures or has_failure_exit:
        if final.exit_code == 0 and has_test_failures:
            caveats.append("Process exited with code 0 but JUnit XML recorded failures/errors")
        if not has_test_failures and has_failure_exit:
            caveats.append(f"Process exited with non-zero code {final.exit_code} but JUnit XML reported no test failures")

        return Verdict(
            state="FAILED",
            evidence="none",
            reasons=[f"Test run failed: {final.failures} failures, {final.errors} errors (exit code {final.exit_code})"],
            caveats=caveats,
        )

    # 5. Check executed test count against baseline and confirmed_min
    expected = max(baseline.executed, confirmed_min, 1)
    if final.executed < expected:
        return Verdict(
            state="NOT_VERIFIED",
            evidence="none",
            reasons=[f"Executed test count regressed: ran {final.executed} tests, expected at least {expected}"],
            caveats=caveats,
        )

    # 6. Check for increases in skipped tests
    if final.skipped > baseline.skipped:
        caveats.append(f"Skipped tests increased from {baseline.skipped} to {final.skipped}")

    # 7. Compute evidence category
    baseline_failed = (baseline.failures > 0 or baseline.errors > 0 or baseline.exit_code != 0)
    if baseline_failed:
        evidence = "red_to_green"
        reasons.append("Tests transitioned from failing to passing (red to green)")
    else:
        evidence = "no_regression_only"
        reasons.append(f"All {final.executed} existing tests passed (no regression)")
        caveats.append("Baseline tests were already passing; evidence demonstrates no regression")

    return Verdict(
        state="VERIFIED",
        evidence=evidence,
        reasons=reasons,
        caveats=caveats,
    )
