"""Unit tests for untrusted JUnit XML parsing."""
import tempfile
from pathlib import Path
import pytest
from devo.runner.parse_junit import MAX_JUNIT_XML_SIZE, parse_junit_xml


def test_parse_real_passing():
    counts = parse_junit_xml("fixtures/junit_passing.xml")
    assert counts.ok is True
    assert counts.tests == 5
    assert counts.failures == 0
    assert counts.errors == 0
    assert counts.skipped == 0


def test_parse_real_failing():
    counts = parse_junit_xml("fixtures/junit_failing.xml")
    assert counts.ok is True
    assert counts.tests == 5
    assert counts.failures == 1
    assert counts.errors == 0


def test_parse_real_zero():
    counts = parse_junit_xml("fixtures/junit_zero.xml")
    assert counts.ok is True
    assert counts.tests == 0
    assert counts.failures == 0
    assert counts.errors == 0


def test_parse_real_syntax_error():
    counts = parse_junit_xml("fixtures/junit_syntax.xml")
    assert counts.ok is True
    assert counts.tests == 1
    assert counts.errors == 1
    assert counts.failures == 0


def test_missing_file():
    counts = parse_junit_xml("fixtures/non_existent.xml")
    assert counts.ok is False
    assert "not found" in counts.reason.lower()


def test_empty_file():
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        f.write(b"   \n")
        f_path = f.name
    try:
        counts = parse_junit_xml(f_path)
        assert counts.ok is False
        assert "empty" in counts.reason.lower()
    finally:
        Path(f_path).unlink(missing_ok=True)


def test_oversized_file(monkeypatch):
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        f.write(b"<testsuites></testsuites>")
        f_path = f.name
    try:
        # Patch MAX_JUNIT_XML_SIZE to a tiny value to test rejection
        import devo.runner.parse_junit as m
        monkeypatch.setattr(m, "MAX_JUNIT_XML_SIZE", 10)
        counts = m.parse_junit_xml(f_path)
        assert counts.ok is False
        assert "maximum allowed size" in counts.reason.lower()
    finally:
        Path(f_path).unlink(missing_ok=True)


def test_hostile_entity_expansion():
    hostile_xml = """<?xml version="1.0"?>
    <!DOCTYPE lolz [
      <!ENTITY lol "lol">
      <!ELEMENT lolz (#PCDATA)>
      <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
    ]>
    <testsuites name="&lol1;"></testsuites>
    """
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        f.write(hostile_xml.encode("utf-8"))
        f_path = f.name
    try:
        counts = parse_junit_xml(f_path)
        # defusedxml will reject DTD / entities
        assert counts.ok is False
        assert "error" in counts.reason.lower()
    finally:
        Path(f_path).unlink(missing_ok=True)
