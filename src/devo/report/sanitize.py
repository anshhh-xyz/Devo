"""Output hygiene stripping ANSI escape codes and terminal control sequences."""
import re

# Regex matching ANSI escape sequences (CSI, OSC, etc.)
ANSI_ESCAPE_PATTERN = re.compile(
    r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
)

# Control characters except newline (\n), carriage return (\r), and tab (\t)
CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


def sanitize_terminal_output(text: str) -> str:
    """Strip ANSI escape sequences and dangerous terminal control characters from untrusted text."""
    if not text:
        return text

    # Remove ANSI escapes
    cleaned = ANSI_ESCAPE_PATTERN.sub("", text)
    # Remove control characters
    cleaned = CONTROL_CHAR_PATTERN.sub("", cleaned)
    return cleaned
