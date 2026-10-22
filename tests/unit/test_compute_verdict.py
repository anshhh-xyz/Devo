"""Table-driven unit tests for compute_verdict."""
import pytest
from devo.verdict.compute_verdict import CheckResult, Verdict, compute_verdict


@pytest.mark.parametrize(
    "name,baseline,final,confirmed_min,expected_state,expected_evidence",
    [
        (
            "red_to_green_success",
            CheckResult(status="completed", exit_code=1, junit_ok=True, tests=5, failures=1, errors=0),
            CheckResult(status="completed", exit_code=0, junit_ok=True, tests=5, failures=0, errors=0),
            0,
            "VERIFIED",
            "red_to_green",
        ),
        (
            "no_regression_only_success",
            CheckResult(status="completed", exit_code=0, junit_ok=True, tests=5, failures=0, errors=0),
            CheckResult(status="completed", exit_code=0, junit_ok=True, tests=5, failures=0, errors=0),
            0,
            "VERIFIED",
            "no_regression_only",
        ),
        (
            "final_timeout",
            CheckResult(status="completed", exit_code=1, junit_ok=True, tests=5, failures=1),
            CheckResult(status="timeout", exit_code=-1, junit_ok=False),
            0,
            "NOT_VERIFIED",
            "none",
        ),
        (
            "final_spawn_error",
            CheckResult(status="completed", exit_code=1, junit_ok=True, tests=5, failures=1),
            CheckResult(status="spawn_error", exit_code=-1, junit_ok=False),
            0,
            "NOT_VERIFIED",
            "none",
        ),
        (
            "final_exit_code_5_no_tests",
            CheckResult(status="completed", exit_code=1, junit_ok=True, tests=5, failures=1),
            CheckResult(status="completed", exit_code=5, junit_ok=True, tests=0, failures=0),
            0,
            "NOT_VERIFIED",
            "none",
        ),
        (
            "final_unparseable_junit",
            CheckResult(status="completed", exit_code=1, junit_ok=True, tests=5, failures=1),
            CheckResult(status="completed", exit_code=0, junit_ok=False),
            0,
            "NOT_VERIFIED",
            "none",
        ),
        (
            "final_failed_with_failures",
            CheckResult(status="completed", exit_code=1, junit_ok=True, tests=5, failures=1),
            CheckResult(status="completed", exit_code=1, junit_ok=True, tests=5, failures=1),
            0,
            "FAILED",
            "none",
        ),
        (
            "final_failed_with_collection_error",
            CheckResult(status="completed", exit_code=1, junit_ok=True, tests=5, failures=1),
            CheckResult(status="completed", exit_code=2, junit_ok=True, tests=1, errors=1),
            0,
            "FAILED",
            "none",
        ),
        (
            "final_fewer_tests_than_baseline",
            CheckResult(status="completed", exit_code=1, junit_ok=True, tests=5, failures=1),
            CheckResult(status="completed", exit_code=0, junit_ok=True, tests=3, failures=0),
            0,
            "NOT_VERIFIED",
            "none",
        ),
        (
            "final_fewer_tests_than_confirmed_min",
            CheckResult(status="completed", exit_code=1, junit_ok=True, tests=2, failures=1),
            CheckResult(status="completed", exit_code=0, junit_ok=True, tests=3, failures=0),
            5,
            "NOT_VERIFIED",
            "none",
        ),
        (
            "exit_0_but_failures_recorded",
            CheckResult(status="completed", exit_code=1, junit_ok=True, tests=5, failures=1),
            CheckResult(status="completed", exit_code=0, junit_ok=True, tests=5, failures=1),
            0,
            "FAILED",
            "none",
        ),
    ],
)
def test_verdict_table(name, baseline, final, confirmed_min, expected_state, expected_evidence):
    verdict = compute_verdict(baseline, final, confirmed_min)
    assert verdict.state == expected_state, f"Failed on {name}: expected {expected_state}, got {verdict.state}"
    assert verdict.evidence == expected_evidence, f"Failed on {name}: expected {expected_evidence}, got {verdict.evidence}"


def test_skipped_tests_caveat():
    baseline = CheckResult(status="completed", exit_code=1, junit_ok=True, tests=6, failures=1, skipped=0)
    final = CheckResult(status="completed", exit_code=0, junit_ok=True, tests=7, failures=0, skipped=1)
    verdict = compute_verdict(baseline, final, 0)
    assert verdict.state == "VERIFIED"
    assert any("skipped" in c.lower() for c in verdict.caveats)
