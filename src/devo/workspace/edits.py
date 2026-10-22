"""Edit validation, diffing, approval enforcement, and application."""
from dataclasses import dataclass
from pathlib import Path
from devo.controller.approval import ApprovalError, verify_approval_token
from devo.workspace.backup import create_backup
from devo.workspace.boundary import resolve_safe_path
from devo.workspace.diff import DiffResult, generate_diff


class EditValidationError(ValueError):
    """Raised when an edit proposal fails validation."""
    pass


@dataclass
class EditProposal:
    path: str
    old_str: str
    new_str: str


def normalize_line_endings(text: str) -> str:
    """Normalize line endings to standard LF for matching."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def prepare_and_validate_edits(
    workspace: Path | str,
    edits: list[dict],
) -> tuple[dict[str, tuple[str, str]], DiffResult]:
    """Validate all proposed edits and compute real before/after states.

    Raises EditValidationError if any edit is invalid:
    - Path resolves outside boundary
    - File does not exist
    - old_str does not occur exactly once
    """
    ws = Path(workspace).resolve()
    if not edits:
        raise EditValidationError("No edits were proposed")

    # Group edits by resolved relative path
    file_changes: dict[str, tuple[str, str]] = {}
    current_contents: dict[str, str] = {}
    line_ending_is_crlf: dict[str, bool] = {}

    for idx, edit in enumerate(edits):
        raw_path = edit.get("path")
        old_str = edit.get("old_str")
        new_str = edit.get("new_str")

        if not raw_path or old_str is None or new_str is None:
            raise EditValidationError(f"Edit #{idx + 1} missing required keys (path, old_str, new_str)")

        target_file = resolve_safe_path(raw_path, ws)
        if not target_file.is_file():
            raise EditValidationError(f"Target file does not exist: {raw_path}")

        rel_key = str(target_file.relative_to(ws)).replace("\\", "/")

        if rel_key not in current_contents:
            raw_text = target_file.read_text(encoding="utf-8", errors="replace")
            current_contents[rel_key] = raw_text
            line_ending_is_crlf[rel_key] = "\r\n" in raw_text

        text = current_contents[rel_key]
        normalized_text = normalize_line_endings(text)
        normalized_old = normalize_line_endings(old_str)
        normalized_new = normalize_line_endings(new_str)

        count = normalized_text.count(normalized_old)
        if count == 0:
            raise EditValidationError(f"Search block ('old_str') not found in '{rel_key}'")
        if count > 1:
            raise EditValidationError(f"Ambiguous edit: 'old_str' matches {count} times in '{rel_key}'. Must match exactly once.")

        updated_text = normalized_text.replace(normalized_old, normalized_new, 1)

        # Restore original CRLF if detected
        if line_ending_is_crlf[rel_key]:
            updated_text = updated_text.replace("\n", "\r\n")

        current_contents[rel_key] = updated_text
        original_text = target_file.read_text(encoding="utf-8", errors="replace")
        file_changes[rel_key] = (original_text, updated_text)

    diff_result = generate_diff(file_changes)
    return file_changes, diff_result


def apply_validated_edits(
    workspace: Path | str,
    edits: list[dict],
    approval_token: str | None,
    run_id: str | None = None,
) -> DiffResult:
    """Apply validated edits to workspace files strictly guarded by the approval token."""
    ws = Path(workspace).resolve()
    file_changes, diff_result = prepare_and_validate_edits(ws, edits)

    if not verify_approval_token(approval_token, diff_result.diff_text):
        raise ApprovalError("Approval token is invalid, expired, or does not match the diff hash")

    # Create backup before any modifications
    if run_id:
        create_backup(ws, list(file_changes.keys()), run_id)

    # Write modifications
    for rel_path, (_, new_text) in file_changes.items():
        file_path = resolve_safe_path(rel_path, ws)
        file_path.write_text(new_text, encoding="utf-8")

    return diff_result
