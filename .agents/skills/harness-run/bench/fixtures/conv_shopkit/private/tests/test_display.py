import pytest


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("SHOPKIT_MAX_DISCOUNT_PCT", raising=False)


def test_two_decimals():
    from shopkit.discounts import display_price

    assert display_price({"price_cents": 1250}) == "$12.50"
    assert display_price({"price_cents": 505}) == "$5.05"


def test_discounted_display():
    from shopkit.discounts import display_price

    assert display_price({"price_cents": 1000, "discount_pct": 10}) == "$9.00"
    assert display_price({"price_cents": 999, "discount_pct": 15}) == "$8.49"


def test_cap_applies_to_display():
    from shopkit.discounts import display_price

    assert display_price({"price_cents": 1000, "discount_pct": 90}) == "$7.00"
