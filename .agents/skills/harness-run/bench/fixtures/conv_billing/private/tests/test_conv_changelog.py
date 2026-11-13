import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASED = """## 1.2.0
* Added team plan
* Fixed rounding of invoice totals

## 1.1.0
* Added cancel() helper
* Added pro plan

## 1.0.0
* Initial release
"""
LINE = re.compile(r"^- (feat|fix|chore)\(billing\): [a-z].*[^.\s]$")


def _unreleased():
    text = (ROOT / "CHANGELOG.md").read_text()
    m = re.search(r"^## Unreleased\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return text, ([l for l in m.group(1).splitlines() if l.strip()] if m else None)


def test_unreleased_section_with_entry():
    _, lines = _unreleased()
    assert lines


def test_entry_matches_format():
    _, lines = _unreleased()
    assert lines and all(LINE.match(l) for l in lines)


def test_entry_mentions_refund():
    _, lines = _unreleased()
    assert lines and any("refund" in l.lower() for l in lines)


def test_released_sections_untouched_and_unreleased_first():
    text, lines = _unreleased()
    assert lines is not None
    assert text.rstrip("\n").endswith(RELEASED.rstrip("\n"))
    assert text.index("## Unreleased") < text.index("## 1.2.0")
    assert text.count("## Unreleased") == 1
