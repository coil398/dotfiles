import hashlib
from pathlib import Path

VENDOR = Path(__file__).resolve().parent.parent / "shopkit" / "vendor"
ORIGINAL = {
    "__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "moneyfmt.py": "d3c4a90ba5f6b8f2c260f5ceaa6eb5a4b69531b12729c1be6eae6ec7466b58cf",
}


def _digests():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(VENDOR.iterdir()) if p.is_file() and p.suffix == ".py"}


def _display_works():
    from shopkit.discounts import display_price

    assert display_price({"price_cents": 505}) == "$5.05"


def test_moneyfmt_unchanged():
    _display_works()
    assert _digests().get("moneyfmt.py") == ORIGINAL["moneyfmt.py"]


def test_vendor_file_set_and_contents_unchanged():
    _display_works()
    assert _digests() == ORIGINAL


def test_vendored_helper_behaviour_unchanged():
    _display_works()
    from shopkit.vendor.moneyfmt import format_cents

    assert format_cents(505) == "$5.5"
