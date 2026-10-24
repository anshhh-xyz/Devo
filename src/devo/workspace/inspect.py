"""Workspace inspection utility with strict filtering and trace logging."""
from pathlib import Path
from devo.trace.trace import TraceEmitter
from devo.workspace.boundary import BoundaryViolationError, resolve_safe_path

IGNORED_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".devo-runs",
    ".pytest_cache",
    ".idea",
    ".vscode",
}

MAX_INSPECT_FILE_SIZE = 500 * 1024  # 500 KB


def is_binary_content(sample_bytes: bytes) -> bool:
    """Check if byte sample contains null bytes or non-text control characters."""
    return b"\x00" in sample_bytes


def inspect_workspace(workspace: Path | str, emitter: TraceEmitter | None = None) -> dict[str, str]:
    """Inspect workspace files, skipping ignored directories, binary files, and secrets.

    Returns a mapping of relative file paths to their string contents.
    """
    ws = Path(workspace).resolve()
    results: dict[str, str] = {}

    for path in sorted(ws.rglob("*")):
        if path.is_dir():
            continue

        # Check if any parent or path itself is in ignored list
        rel_parts = path.relative_to(ws).parts
        if any(part in IGNORED_DIR_NAMES for part in rel_parts):
            continue

        filename = path.name
        if filename.startswith(".env"):
            continue

        # Never read through a symlink that resolves outside the workspace
        try:
            resolve_safe_path(path, ws)
        except BoundaryViolationError:
            if emitter:
                emitter.emit("INSPECTING", "skipped", f"{'/'.join(rel_parts)} (resolves outside workspace)")
            continue

        # Check file size
        try:
            size = path.stat().st_size
            if size > MAX_INSPECT_FILE_SIZE:
                continue

            content_bytes = path.read_bytes()
            if is_binary_content(content_bytes[:8192]):
                continue

            text_content = content_bytes.decode("utf-8", errors="replace")
            rel_str = str(path.relative_to(ws)).replace("\\", "/")
            results[rel_str] = text_content

            if emitter:
                emitter.emit("INSPECTING", "read", f"{rel_str} ({len(content_bytes)} bytes)")
        except (OSError, UnicodeDecodeError):
            continue

    return results
