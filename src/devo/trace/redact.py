"""Secret redaction utility to ensure credentials never leak into traces or outputs."""
import re

SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password|bearer|auth)[\s:=]+['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?"),
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),  # OpenAI-style keys
    re.compile(r"ghp_[a-zA-Z0-9]{20,}"),  # GitHub personal access tokens
]

REDACTED_PLACEHOLDER = "[REDACTED_SECRET]"


def redact_secrets(text: str) -> str:
    """Sanitize text by replacing suspected API keys and secret values with a placeholder."""
    if not text:
        return text

    sanitized = text
    for pattern in SENSITIVE_PATTERNS:
        # If pattern has groups, redact the sensitive value group
        def _replace(match: re.Match) -> str:
            if match.groups() and len(match.groups()) >= 2:
                # Key=Value pattern
                return f"{match.group(1)}={REDACTED_PLACEHOLDER}"
            return REDACTED_PLACEHOLDER

        sanitized = pattern.sub(_replace, sanitized)

    return sanitized
