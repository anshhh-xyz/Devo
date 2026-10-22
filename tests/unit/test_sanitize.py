"""Unit tests for terminal output sanitization."""
from devo.report.sanitize import sanitize_terminal_output


def test_sanitize_ansi_colors_and_cursor_codes():
    # Text injected with ANSI color codes and cursor movement
    malicious = "\x1b[31;1m[FAKED_FAILED]\x1b[0m \x1b[2J\x1b[HClear Screen"
    cleaned = sanitize_terminal_output(malicious)
    assert "\x1b" not in cleaned
    assert "[FAKED_FAILED] Clear Screen" in cleaned


def test_sanitize_control_characters():
    # Null bytes, bells, backspaces
    dirty = "Valid Text\x00\x07\x08With Hidden Chars"
    cleaned = sanitize_terminal_output(dirty)
    assert "\x00" not in cleaned
    assert "\x07" not in cleaned
    assert "\x08" not in cleaned
    assert "Valid TextWith Hidden Chars" == cleaned


def test_preserve_normal_newlines_and_tabs():
    clean_original = "Line 1\nLine 2\tTabbed\r\nLine 3"
    assert sanitize_terminal_output(clean_original) == clean_original
