import ast
import logging
from datetime import date
from pathlib import Path

START, END = date(2024, 1, 1), date(2024, 1, 31)


def test_issue_logs_info(caplog):
    from billing.refunds import issue_refund

    caplog.set_level(logging.DEBUG)
    issue_refund("s1", "pro", START, END, date(2024, 1, 24), [])
    assert any(r.name.startswith("billing") and r.levelno == logging.INFO for r in caplog.records)


def test_issue_prints_nothing(capsys):
    from billing.refunds import issue_refund

    issue_refund("s1", "pro", START, END, date(2024, 1, 24), [])
    out = capsys.readouterr()
    assert out.out == "" and out.err == ""


def _tree():
    import billing.refunds as m

    return ast.parse(Path(m.__file__).read_text())


def test_no_print_call():
    calls = [n for n in ast.walk(_tree()) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id == "print"]
    assert not calls


def test_uses_project_logger_factory():
    names = set()
    for n in ast.walk(_tree()):
        if isinstance(n, ast.Call):
            f = n.func
            names.add(f.id if isinstance(f, ast.Name) else getattr(f, "attr", ""))
    assert "get_logger" in names and "getLogger" not in names
