"""Unit tests for the CLI interface and commands."""
import tempfile
from pathlib import Path
import pytest
from devo.cli import main
from devo.workspace.diff import DiffResult


def test_cli_help(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "Evidence-first coding assistant" in captured.out


def test_cli_demo_reset():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td) / "workspace"
        res = main(["demo-reset", "--seed", "demo/seed", "--workspace", str(ws)])
        assert res == 0
        assert (ws / "mathutils.py").exists()
        assert (ws / "test_mathutils.py").exists()


def test_cli_non_interactive_refusal(capsys, monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        from devo.workspace.reset import reset_demo
        reset_demo("demo/seed", ws)

        # Force sys.stdin.isatty to False
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)

        code = main([
            "run",
            "--workspace", str(ws),
            "--task", "Fix division",
            "--backend", "mock",
            "--scenario", "scenario_verified",
        ])
        assert code == 3  # rejected code
        captured = capsys.readouterr()
        assert "Refusing to apply: Standard input is non-interactive" in captured.out


def test_cli_interactive_approve(capsys, monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        from devo.workspace.reset import reset_demo
        reset_demo("demo/seed", ws)

        # Force sys.stdin.isatty to True and mock input to "approve"
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr("builtins.input", lambda prompt="": "approve")

        code = main([
            "run",
            "--workspace", str(ws),
            "--task", "Fix division",
            "--backend", "mock",
            "--scenario", "scenario_verified",
        ])
        assert code == 0  # Verified code
        captured = capsys.readouterr()
        assert "[VERIFIED]" in captured.out
