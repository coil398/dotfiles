from decimal import Decimal

import pytest

from ledger.parse import parse_rows
from ledger.report import monthly_totals, top_accounts

CSV = """date,account,amount,currency
2026-01-05,food,0.01,USD
2026-01-06,food,0.01,USD
2026-01-31,rent,1000,JPY
2026-02-01,rent,1000,JPY
2026-02-03,travel,2.5,EUR
2026-02-04,food, 1.10 ,USD
"""


def test_amount_is_decimal_and_trimmed():
    rows = parse_rows(CSV)
    assert rows[-1]["amount"] == Decimal("1.10")
    assert isinstance(rows[0]["amount"], Decimal)


def test_unknown_currency_raises_value_error():
    with pytest.raises(ValueError, match="XXX"):
        parse_rows("date,account,amount,currency\n2026-01-01,a,1,XXX\n")


def test_monthly_totals_sum_before_rounding():
    t = monthly_totals(parse_rows(CSV))
    # 0.01 USD * 150 = 1.5 JPY each; summed per month = 3.0 -> 3 (round per month, not per row)
    assert t[("2026-01", "food")] == 3
    assert t[("2026-01", "rent")] == 1000
    assert t[("2026-02", "rent")] == 1000
    # 2.5 EUR * 160 = 400
    assert t[("2026-02", "travel")] == 400
    # 1.10 USD * 150 = 165
    assert t[("2026-02", "food")] == 165


def test_half_up_rounding():
    t = monthly_totals(parse_rows("date,account,amount,currency\n2026-03-01,x,0.01,USD\n"))
    assert t[("2026-03", "x")] == 2  # 1.5 rounds half-up to 2, not banker's 2? use 0.03 too
    t = monthly_totals(parse_rows("date,account,amount,currency\n2026-03-01,x,0.0166666666666666666666666667,USD\n2026-03-02,y,0.01666666666666666666666666667,EUR\n"))
    assert t[("2026-03", "x")] == 3  # 2.5 -> 3 half-up


def test_top_accounts_descending_ties_by_name():
    rows = parse_rows(CSV)
    assert top_accounts(rows, 2) == ["rent", "travel"]
    rows2 = parse_rows("date,account,amount,currency\n2026-01-01,b,5,JPY\n2026-01-01,a,5,JPY\n2026-01-01,c,1,JPY\n")
    assert top_accounts(rows2, 2) == ["a", "b"]
