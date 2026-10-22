"""Unit tests for edits, approval token enforcement, and revert rollback."""
import tempfile
from pathlib import Path
import pytest
from devo.controller.approval import ApprovalError, mint_approval_token
from devo.workspace.backup import revert_backup
from devo.workspace.boundary import BoundaryViolationError
from devo.workspace.edits import (
    EditValidationError,
    apply_validated_edits,
    prepare_and_validate_edits,
)


def test_edit_validation_missing_old_str():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        (ws / "app.py").write_text("x = 10\n")
        edits = [{"path": "app.py", "old_str": "x = 99", "new_str": "x = 20"}]
        with pytest.raises(EditValidationError) as exc:
            prepare_and_validate_edits(ws, edits)
        assert "not found" in str(exc.value)


def test_edit_validation_duplicate_old_str():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        (ws / "app.py").write_text("x = 10\nx = 10\n")
        edits = [{"path": "app.py", "old_str": "x = 10", "new_str": "x = 20"}]
        with pytest.raises(EditValidationError) as exc:
            prepare_and_validate_edits(ws, edits)
        assert "ambiguous" in str(exc.value).lower()


def test_edit_outside_boundary():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        edits = [{"path": "../outside.py", "old_str": "a", "new_str": "b"}]
        with pytest.raises(BoundaryViolationError):
            prepare_and_validate_edits(ws, edits)


def test_full_safe_lifecycle_approval_and_revert():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        target = ws / "mathutils.py"
        original_text = "def divide(a, b):\n    return a * b\n"
        target.write_text(original_text)

        edits = [{"path": "mathutils.py", "old_str": "return a * b", "new_str": "return a / b"}]

        # 1. Prepare and generate diff
        file_changes, diff_res = prepare_and_validate_edits(ws, edits)
        assert "-    return a * b" in diff_res.diff_text
        assert "+    return a / b" in diff_res.diff_text

        # 2. Attempt apply with no token -> must fail
        with pytest.raises(ApprovalError):
            apply_validated_edits(ws, edits, approval_token=None)

        # 3. Attempt apply with wrong token -> must fail
        with pytest.raises(ApprovalError):
            apply_validated_edits(ws, edits, approval_token="bad_token_12345")

        # 4. Mint correct token and apply
        token = mint_approval_token(diff_res.diff_text)
        apply_validated_edits(ws, edits, approval_token=token, run_id="run-001")

        # Verify modification
        assert target.read_text() == "def divide(a, b):\n    return a / b\n"

        # 5. Revert and verify byte-for-byte restoration
        restored = revert_backup(ws, run_id="run-001")
        assert "mathutils.py" in restored
        assert target.read_text() == original_text
