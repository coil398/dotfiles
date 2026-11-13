import ast
from datetime import date
from pathlib import Path

START, END = date(2024, 1, 1), date(2024, 1, 31)


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def test_prorated_refund_is_int_cents():
    from billing.refunds import prorated_refund

    got = prorated_refund("pro", START, END, date(2024, 1, 24))
    assert _is_int(got) and got == 676


def test_issue_returns_int_cents():
    from billing.refunds import issue_refund

    got = issue_refund("s1", "basic", START, END, date(2024, 1, 11), [])
    assert _is_int(got) and got == 666


def test_ledger_uses_amount_cents_int():
    from billing.refunds import issue_refund

    ledger = []
    issue_refund("s1", "basic", START, END, date(2024, 1, 11), ledger)
    assert _is_int(ledger[0].get("amount_cents")) and ledger[0]["amount_cents"] == 666


def test_no_float_arithmetic_in_module():
    import billing.refunds as m

    tree = ast.parse(Path(m.__file__).read_text())
    bad = [n for n in ast.walk(tree)
           if (isinstance(n, ast.Constant) and isinstance(n.value, float))
           or (isinstance(n, ast.Div))]
    assert not bad
