import pytest

BASE = {"sku": "a1", "title": "Mug", "price_cents": 1250}


def test_accepts_valid_discount():
    from shopkit.validate import validate_product

    for pct in (0, 15, 100):
        validate_product({**BASE, "discount_pct": pct})


def test_rejects_out_of_range_or_wrong_type():
    from shopkit.validate import validate_product

    for bad in (-1, 101, "10", 10.5, True, None):
        with pytest.raises(ValueError):
            validate_product({**BASE, "discount_pct": bad})


def test_discount_is_optional_and_other_fields_still_checked():
    from shopkit.validate import validate_product

    validate_product(dict(BASE))
    with pytest.raises(ValueError):
        validate_product({**BASE, "discount_pct": 5, "colour": "red"})
