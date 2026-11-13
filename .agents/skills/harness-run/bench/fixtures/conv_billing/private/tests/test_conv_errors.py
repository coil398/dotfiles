import ast
from datetime import date
from pathlib import Path

START, END = date(2024, 1, 1), date(2024, 1, 31)
BUILTINS = {"ValueError", "KeyError", "Exception", "TypeError", "RuntimeError", "LookupError"}


def _raises(call):
    from billing.errors import AppError

    try:
        call()
    except Exception as exc:
        return isinstance(exc, AppError)
    return False


def test_unknown_plan_is_app_error():
    from billing.refunds import prorated_refund

    assert _raises(lambda: prorated_refund("gold", START, END, START))


def test_bad_period_is_app_error():
    from billing.refunds import prorated_refund

    assert _raises(lambda: prorated_refund("pro", END, START, START))


def test_duplicate_is_app_error():
    from billing.refunds import issue_refund

    ledger = []
    issue_refund("s1", "basic", START, END, date(2024, 1, 11), ledger)
    assert _raises(lambda: issue_refund("s1", "basic", START, END, date(2024, 1, 12), ledger))


def test_no_builtin_raises_in_module():
    import billing.refunds as m

    tree = ast.parse(Path(m.__file__).read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and node.exc is not None:
            exc = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
            if isinstance(exc, ast.Name):
                names.add(exc.id)
    assert names and not names & BUILTINS
