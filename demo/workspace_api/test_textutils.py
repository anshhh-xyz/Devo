"""Tests for textutils — five targeted tests, one will fail on the planted bug."""
import pytest
from textutils import word_count, truncate, reverse_words, title_case, count_vowels


def test_word_count_basic():
    assert word_count("hello world") == 2
    assert word_count("") == 0
    assert word_count("  ") == 0


def test_truncate_short_string():
    assert truncate("hi", 10) == "hi"
    assert truncate("hello world", 5) == "hello..."


def test_reverse_words():
    assert reverse_words("one two three") == "three two one"
    assert reverse_words("solo") == "solo"


def test_title_case():
    # This test FAILS because title_case() calls .upper() instead of .title()
    assert title_case("hello world") == "Hello World"
    assert title_case("the quick BROWN fox") == "The Quick Brown Fox"


def test_count_vowels():
    assert count_vowels("hello") == 2
    assert count_vowels("rhythm") == 0
    assert count_vowels("AEIOU") == 5
