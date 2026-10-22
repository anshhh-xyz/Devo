"""Text utility functions — demo seed for live API scenario."""


def word_count(text: str) -> int:
    """Return the number of words in *text*."""
    if not text or not text.strip():
        return 0
    return len(text.split())


def truncate(text: str, max_len: int, suffix: str = "...") -> str:
    """Truncate *text* to *max_len* characters, appending *suffix* if cut."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + suffix


def reverse_words(text: str) -> str:
    """Return *text* with its words in reversed order."""
    return " ".join(text.split()[::-1])


def title_case(text: str) -> str:
    """Return *text* converted to Title Case.

    PLANTED BUG: uses .upper() on the whole string instead of .title()
    so 'hello world' becomes 'HELLO WORLD' instead of 'Hello World'.
    """
    return text.upper()        # BUG: should be text.title()


def count_vowels(text: str) -> int:
    """Return the number of vowel characters (a e i o u) in *text* (case-insensitive)."""
    return sum(1 for ch in text.lower() if ch in "aeiou")
