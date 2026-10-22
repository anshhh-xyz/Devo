"""Safe parsing of untrusted JUnit XML using defusedxml."""
from dataclasses import dataclass
from pathlib import Path
import defusedxml.ElementTree as ET
from defusedxml.common import DefusedXmlException

# 5 MB cap on untrusted XML file size
MAX_JUNIT_XML_SIZE = 5 * 1024 * 1024


@dataclass
class JUnitCounts:
    ok: bool
    tests: int = 0
    failures: int = 0
    errors: int = 0
    skipped: int = 0
    reason: str = ""


def parse_junit_xml(xml_path: Path | str) -> JUnitCounts:
    """Parse a JUnit XML file produced by pytest.

    Treats the XML as completely untrusted input:
    - Enforces a strict file size cap.
    - Rejects XML entity expansions and DOCTYPE declarations via defusedxml.
    - Returns ok=False for missing, malformed, or hostile content without raising.
    """
    path = Path(xml_path)

    if not path.exists():
        return JUnitCounts(ok=False, reason="File not found")

    try:
        size = path.stat().st_size
        if size > MAX_JUNIT_XML_SIZE:
            return JUnitCounts(ok=False, reason=f"File exceeds maximum allowed size ({size} > {MAX_JUNIT_XML_SIZE})")

        content = path.read_bytes()
        if not content.strip():
            return JUnitCounts(ok=False, reason="Empty XML file")

        root = ET.fromstring(content)
    except (DefusedXmlException, ET.ParseError, OSError, ValueError) as err:
        return JUnitCounts(ok=False, reason=f"XML parsing error: {err}")

    # Root can be <testsuites> or <testsuite>
    suite_elements = []
    if root.tag == "testsuite":
        suite_elements = [root]
    elif root.tag == "testsuites":
        suite_elements = root.findall("testsuite")
        if not suite_elements:
            # If no child testsuite, check if root itself has counts
            suite_elements = [root]
    else:
        return JUnitCounts(ok=False, reason=f"Unexpected root element: {root.tag}")

    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0

    for suite in suite_elements:
        try:
            total_tests += int(suite.attrib.get("tests", 0))
            total_failures += int(suite.attrib.get("failures", 0))
            total_errors += int(suite.attrib.get("errors", 0))
            total_skipped += int(suite.attrib.get("skipped", 0))
        except (ValueError, TypeError):
            return JUnitCounts(ok=False, reason="Malformed count attribute in testsuite")

    return JUnitCounts(
        ok=True,
        tests=total_tests,
        failures=total_failures,
        errors=total_errors,
        skipped=total_skipped,
    )
