"""Approval token generation and verification cryptographically bound to diff content."""
import hashlib


class ApprovalError(PermissionError):
    """Raised when an attempt to apply edits lacks a valid, diff-bound approval token."""
    pass


def compute_diff_hash(diff_text: str) -> str:
    """Compute deterministic SHA-256 hash of diff text."""
    return hashlib.sha256(diff_text.encode("utf-8")).hexdigest()


def mint_approval_token(diff_text: str) -> str:
    """Mint an approval token directly bound to the exact diff text."""
    return compute_diff_hash(diff_text)


def verify_approval_token(token: str | None, diff_text: str) -> bool:
    """Verify that the provided token strictly matches the diff hash."""
    if not token or not diff_text:
        return False
    expected = compute_diff_hash(diff_text)
    return token.strip() == expected
