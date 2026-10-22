"""Integration tests executing the full verification lifecycle across all three scenarios."""
import tempfile
from pathlib import Path
from devo.controller.run import RunState, execute_run
from devo.model.mock import MockModelAdapter
from devo.workspace.backup import revert_backup
from devo.workspace.reset import reset_demo


def test_scenario_verified_end_to_end():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        reset_demo("demo/seed", ws)

        adapter = MockModelAdapter("scenario_verified", fixtures_dir="fixtures/model")
        report = execute_run(
            workspace=ws,
            task="Fix division in mathutils.py",
            model_adapter=adapter,
            approval_callback=lambda diff: True,
        )

        assert report.state == RunState.DONE
        assert report.verdict.state == "VERIFIED"
        assert report.verdict.evidence == "red_to_green"
        assert report.baseline.failures == 1
        assert report.final.failures == 0
        assert report.final.tests == 5


def test_scenario_failed_and_revert_end_to_end():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        reset_demo("demo/seed", ws)
        pristine_text = (ws / "mathutils.py").read_text()

        adapter = MockModelAdapter("scenario_failed", fixtures_dir="fixtures/model")
        report = execute_run(
            workspace=ws,
            task="Fix division with wrong operator",
            model_adapter=adapter,
            approval_callback=lambda diff: True,
            run_id="run-failed-01",
        )

        assert report.state == RunState.DONE
        assert report.verdict.state == "FAILED"
        assert report.final.failures >= 1

        # Now test revert
        revert_backup(ws, "run-failed-01")
        assert (ws / "mathutils.py").read_text() == pristine_text


def test_scenario_not_verified_timeout_end_to_end():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        reset_demo("demo/seed", ws)

        adapter = MockModelAdapter("scenario_not_verified", fixtures_dir="fixtures/model")
        report = execute_run(
            workspace=ws,
            task="Introduce infinite loop",
            model_adapter=adapter,
            approval_callback=lambda diff: True,
            timeout_override=0.5,
        )

        assert report.state == RunState.DONE
        assert report.verdict.state == "NOT_VERIFIED"
        assert report.final.status == "timeout"


def test_scenario_rejection_leaves_files_untouched():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        reset_demo("demo/seed", ws)
        original_content = (ws / "mathutils.py").read_text()

        adapter = MockModelAdapter("scenario_verified", fixtures_dir="fixtures/model")
        report = execute_run(
            workspace=ws,
            task="Fix division",
            model_adapter=adapter,
            approval_callback=lambda diff: False,  # User rejects
        )

        assert report.state == RunState.REJECTED
        assert report.verdict.state == "NOT_VERIFIED"
        assert (ws / "mathutils.py").read_text() == original_content
