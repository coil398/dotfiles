from datetime import date

import pytest

START, END = date(2024, 1, 1), date(2024, 1, 31)


def cents(x):
    return x if isinstance(x, int) else round(float(x) * 100)


def amount_of(entry):
    return cents(entry.get("amount_cents", entry.get("amount")))


def test_issue_records_and_returns():
    from billing.refunds import issue_refund

    ledger = []
    got = issue_refund("s1", "pro", START, END, date(2024, 1, 24), ledger)
    assert cents(got) == 676
    assert len(ledger) == 1 and ledger[0]["sub_id"] == "s1"
    assert amount_of(ledger[0]) == 676


def test_zero_refund_appends_nothing():
    from billing.refunds import issue_refund

    ledger = []
    assert cents(issue_refund("s1", "pro", START, END, END, ledger)) == 0
    assert ledger == []


def test_duplicate_sub_is_error():
    from billing.refunds import issue_refund

    ledger = []
    issue_refund("s1", "basic", START, END, date(2024, 1, 11), ledger)
    with pytest.raises(Exception):
        issue_refund("s1", "basic", START, END, date(2024, 1, 12), ledger)
    assert len(ledger) == 1


def test_two_subscriptions():
    from billing.refunds import issue_refund

    ledger = []
    issue_refund("a", "basic", START, END, date(2024, 1, 11), ledger)
    issue_refund("b", "team", START, END, START, ledger)
    assert [e["sub_id"] for e in ledger] == ["a", "b"]
    assert [amount_of(e) for e in ledger] == [666, 4950]
