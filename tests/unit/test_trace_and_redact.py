"""Unit tests for trace logging, secret redaction, and workspace inspection."""
import tempfile
from pathlib import Path
from devo.trace.redact import redact_secrets
from devo.trace.trace import TraceEmitter
from devo.workspace.inspect import inspect_workspace


def test_redact_secrets():
    text = "Connecting with OPENAI_API_KEY=sk-1234567890abcdef123456 and token: ghp_abcdef1234567890123456"
    redacted = redact_secrets(text)
    assert "sk-1234567890abcdef123456" not in redacted
    assert "ghp_abcdef1234567890123456" not in redacted
    assert "[REDACTED_SECRET]" in redacted


def test_trace_emitter():
    with tempfile.TemporaryDirectory() as td:
        log_file = Path(td) / "trace.jsonl"
        emitter = TraceEmitter(log_file)
        emitter.emit("INSPECTING", "read", "Found token=secret12345678 in file.py")

        assert len(emitter.events) == 1
        assert "secret12345678" not in emitter.events[0].detail
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "INSPECTING" in content


def test_inspect_workspace_filtering():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        # Normal python file
        (ws / "app.py").write_text("print('hello')")
        # Ignored venv directory
        (ws / ".venv").mkdir()
        (ws / ".venv" / "pip.py").write_text("dummy")
        # Ignored .git directory
        (ws / ".git").mkdir()
        (ws / ".git" / "config").write_text("dummy")
        # Ignored .env secret file
        (ws / ".env.local").write_text("SECRET_KEY=12345")
        # Binary file
        (ws / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00")

        inspected = inspect_workspace(ws)
        assert "app.py" in inspected
        assert any(".venv" in k for k in inspected.keys()) is False
        assert any(".git" in k for k in inspected.keys()) is False
        assert any(".env" in k for k in inspected.keys()) is False
        assert "image.png" not in inspected
