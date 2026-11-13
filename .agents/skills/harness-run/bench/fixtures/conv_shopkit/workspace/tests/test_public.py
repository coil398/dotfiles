import pytest

from shopkit import catalog, config, pricing, validate

P = {"sku": "a1", "title": "Mug", "price_cents": 1250}


def test_validate_ok():
    assert validate.validate_product(dict(P)) == P


def test_validate_missing_title():
    with pytest.raises(ValueError):
        validate.validate_product({"sku": "a1", "price_cents": 5})


def test_with_tax(monkeypatch):
    monkeypatch.setenv("SHOPKIT_TAX_RATE", "0.1")
    assert pricing.with_tax(1000) == 1100


def test_config_default():
    assert config.get("definitely_unset_key", 7) == 7


def test_catalog_sorted():
    rows = [dict(P, sku="b"), dict(P, sku="a")]
    assert [r["sku"] for r in catalog.list_products(rows)] == ["a", "b"]


def test_discount_example():
    from shopkit.discounts import discounted_price_cents

    assert discounted_price_cents({**P, "price_cents": 2000, "discount_pct": 10}) == 1800
