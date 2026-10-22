"""Unit tests for check runner limits and isolation."""
import tempfile
from pathlib import Path
import pytest
from devo.runner.presets import CheckPreset
from devo.runner.run_check import run_check, scrub_environment


def test_scrub_environment():
    dirty_env = {
        "PATH": "C:\\Windows\\System32",
        "OPENAI_API_KEY": "sk-secret-12345",
        "ANTHROPIC_KEY": "ant-secret",
        "DEVO_SECRET_TOKEN": "token-xyz",
        "MY_DATABASE_PASSWORD": "supersecretpassword",
        "USER_NAME": "developer",
    }
    scrubbed = scrub_environment(dirty_env)
    assert "PATH" in scrubbed
    assert "USER_NAME" in scrubbed
    assert "OPENAI_API_KEY" not in scrubbed
    assert "ANTHROPIC_KEY" not in scrubbed
    assert "DEVO_SECRET_TOKEN" not in scrubbed
    assert "MY_DATABASE_PASSWORD" not in scrubbed


def test_missing_workspace():
    res = run_check("non/existent/path/here")
    assert res.status == "spawn_error"


def test_runner_on_demo_workspace():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        from devo.workspace.reset import reset_demo
        reset_demo("demo/seed", ws)
        res = run_check(ws)
        assert res.status == "completed"
        assert res.exit_code == 1
        assert res.junit_ok is True
        assert res.tests == 5
        assert res.failures == 1
        assert res.errors == 0


def test_runner_timeout_kill():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        (ws / "test_hang.py").write_text("import time\ndef test_hanging():\n    time.sleep(10)\n")
        res = run_check(ws, timeout_override=0.5)
        assert res.status == "timeout"
        assert "timeout" in res.reason.lower()


def test_runner_output_capping():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        (ws / "test_flood.py").write_text(
            "def test_flood():\n    for _ in range(5000):\n        print('A' * 100)\n    assert False\n"
        )
        custom_preset = CheckPreset(name="test", output_cap_bytes=1000)
        res = run_check(ws, preset=custom_preset)
        assert res.status == "completed"
        assert res.truncated is True
        assert len(res.stdout) <= 1200  # 1000 + truncation note
