from datetime import date

import pytest

START, END = date(2024, 1, 1), date(2024, 1, 31)


def cents(x):
    return x if isinstance(x, int) else round(float(x) * 100)


def test_partial_basic():
    from billing.refunds import prorated_refund

    assert cents(prorated_refund("basic", START, END, date(2024, 1, 11))) == 666


def test_partial_pro_rounds_down():
    from billing.refunds import prorated_refund

    assert cents(prorated_refund("pro", START, END, date(2024, 1, 24))) == 676


def test_full_and_zero_boundaries():
    from billing.refunds import prorated_refund

    assert cents(prorated_refund("basic", START, END, date(2023, 12, 20))) == 999
    assert cents(prorated_refund("basic", START, END, START)) == 999
    assert cents(prorated_refund("team", START, END, END)) == 0
    assert cents(prorated_refund("team", START, END, date(2024, 3, 1))) == 0


def test_invalid_input_is_error():
    from billing.refunds import prorated_refund

    with pytest.raises(Exception):
        prorated_refund("gold", START, END, date(2024, 1, 5))
    with pytest.raises(Exception):
        prorated_refund("pro", END, START, date(2024, 1, 5))
    with pytest.raises(Exception):
        prorated_refund("pro", START, START, START)
