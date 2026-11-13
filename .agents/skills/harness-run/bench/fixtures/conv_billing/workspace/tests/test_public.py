from datetime import date

import pytest

from billing import invoices, plans, subscriptions


def test_line_total():
    assert invoices.line_total(9.99, 3) == 29.97


def test_negative_quantity_rejected():
    with pytest.raises(ValueError):
        invoices.line_total(1.0, -1)


def test_cancel_marks_status():
    sub = subscriptions.make("s1", "basic")
    assert subscriptions.cancel(sub)["status"] == "cancelled"


def test_seats():
    assert plans.seats_of("team") == 10


def test_refund_after_period_is_zero():
    from billing.refunds import prorated_refund

    assert prorated_refund("pro", date(2024, 1, 1), date(2024, 1, 31), date(2024, 2, 5)) == 0


def test_refund_unknown_plan_is_error():
    from billing.refunds import prorated_refund

    with pytest.raises(Exception):
        prorated_refund("nope", date(2024, 1, 1), date(2024, 1, 31), date(2024, 1, 5))
