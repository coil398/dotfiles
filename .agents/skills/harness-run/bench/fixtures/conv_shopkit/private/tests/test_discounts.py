import pytest


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("SHOPKIT_MAX_DISCOUNT_PCT", raising=False)


def test_basic_discount_rounds_down():
    from shopkit.discounts import discounted_price_cents

    assert discounted_price_cents({"price_cents": 999, "discount_pct": 15}) == 849
    assert discounted_price_cents({"price_cents": 1250, "discount_pct": 20}) == 1000
    assert discounted_price_cents({"price_cents": 1250}) == 1250


def test_default_cap_is_30():
    from shopkit.discounts import discounted_price_cents

    assert discounted_price_cents({"price_cents": 1000, "discount_pct": 80}) == 700


def test_cap_from_setting(monkeypatch):
    from shopkit.discounts import discounted_price_cents

    monkeypatch.setenv("SHOPKIT_MAX_DISCOUNT_PCT", "50")
    assert discounted_price_cents({"price_cents": 1000, "discount_pct": 80}) == 500
    assert discounted_price_cents({"price_cents": 1000, "discount_pct": 10}) == 900
