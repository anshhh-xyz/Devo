"""Unified diff generation and test-file edit detection."""
from dataclasses import dataclass, field
import difflib
from pathlib import Path


@dataclass
class DiffResult:
    diff_text: str
    touches_tests: bool
    modified_files: list[str] = field(default_factory=list)


def is_test_file(rel_path: str) -> bool:
    """Check if relative path corresponds to a test file or directory."""
    path_str = rel_path.replace("\\", "/").lower()
    name = Path(path_str).name
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or "/tests/" in f"/{path_str}/"
        or path_str.startswith("tests/")
    )


def generate_diff(file_changes: dict[str, tuple[str, str]]) -> DiffResult:
    """Generate a unified diff from a map of relative path -> (original_content, new_content)."""
    diff_lines: list[str] = []
    touches_tests = False
    modified_files = []

    for rel_path, (old_text, new_text) in sorted(file_changes.items()):
        if old_text == new_text:
            continue

        modified_files.append(rel_path)
        if is_test_file(rel_path):
            touches_tests = True

        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)

        file_diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{rel_path}",
            tofile=f"b/{rel_path}",
        )
        diff_lines.extend(file_diff)

    return DiffResult(
        diff_text="".join(diff_lines),
        touches_tests=touches_tests,
        modified_files=modified_files,
    )
