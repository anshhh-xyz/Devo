"""Unit tests for workspace path boundary resolution."""
import tempfile
from pathlib import Path
import pytest
from devo.workspace.boundary import BoundaryViolationError, resolve_safe_path


def test_boundary_valid_relative():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        (ws / "nested").mkdir()
        (ws / "nested" / "file.py").write_text("hello")
        res = resolve_safe_path("nested/file.py", ws)
        assert res == (ws / "nested" / "file.py").resolve()


def test_boundary_traversal_rejection():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        with pytest.raises(BoundaryViolationError):
            resolve_safe_path("../outside.py", ws)


def test_boundary_absolute_outside_rejection():
    with tempfile.TemporaryDirectory() as td1, tempfile.TemporaryDirectory() as td2:
        ws = Path(td1)
        outside = Path(td2) / "secret.txt"
        outside.write_text("shh")
        with pytest.raises(BoundaryViolationError):
            resolve_safe_path(str(outside), ws)


def test_boundary_symlink_escape():
    with tempfile.TemporaryDirectory() as td1, tempfile.TemporaryDirectory() as td2:
        ws = Path(td1)
        outside_target = Path(td2) / "target.txt"
        outside_target.write_text("target")
        symlink = ws / "symlink_out"
        try:
            symlink.symlink_to(outside_target)
            with pytest.raises(BoundaryViolationError):
                resolve_safe_path("symlink_out", ws)
        except OSError:
            # On Windows without developer mode/admin rights, symlink creation might fail
            pytest.skip("Symlink creation not permitted by OS")
