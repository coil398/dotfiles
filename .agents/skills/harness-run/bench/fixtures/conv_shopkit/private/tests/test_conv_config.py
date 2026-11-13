import ast
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("SHOPKIT_MAX_DISCOUNT_PCT", raising=False)


def test_cap_comes_from_config_get(monkeypatch):
    from shopkit import config
    from shopkit.discounts import discounted_price_cents

    monkeypatch.setitem(config._overrides, "max_discount_pct", 5)
    assert discounted_price_cents({"price_cents": 1000, "discount_pct": 40}) == 950


def test_string_setting_is_converted(monkeypatch):
    from shopkit import config
    from shopkit.discounts import discounted_price_cents

    monkeypatch.setitem(config._overrides, "max_discount_pct", "100")
    assert discounted_price_cents({"price_cents": 1000, "discount_pct": 40}) == 600


def test_no_direct_environment_access():
    import shopkit.discounts as m

    tree = ast.parse(Path(m.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in ("environ", "getenv"):
            pytest.fail("direct environment access")
        if isinstance(node, ast.ImportFrom) and node.module == "os":
            pytest.fail("imports from os")
