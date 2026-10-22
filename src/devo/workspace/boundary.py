"""Path boundary validation ensuring all operations remain strictly within the workspace."""
from pathlib import Path


class BoundaryViolationError(ValueError):
    """Raised when an operation attempts to access or modify a path outside the workspace."""
    pass


def resolve_safe_path(target_path: Path | str, workspace: Path | str) -> Path:
    """Resolve and validate that target_path is strictly inside workspace.

    Raises BoundaryViolationError if target_path resolves outside workspace.
    """
    ws_resolved = Path(workspace).resolve()
    if not ws_resolved.is_dir():
        raise BoundaryViolationError(f"Workspace directory does not exist or is not a directory: {ws_resolved}")

    # Combine workspace with relative target path if relative
    target = Path(target_path)
    if not target.is_absolute():
        target = ws_resolved / target

    target_resolved = target.resolve()

    try:
        target_resolved.relative_to(ws_resolved)
    except ValueError:
        raise BoundaryViolationError(
            f"Path traversal detected: '{target_path}' resolves to '{target_resolved}' which is outside workspace '{ws_resolved}'"
        )

    return target_resolved
