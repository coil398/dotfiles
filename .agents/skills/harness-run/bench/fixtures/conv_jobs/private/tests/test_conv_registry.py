import ast
import importlib
from pathlib import Path

JOBS = Path(__file__).resolve().parent.parent / "jobs"


def test_registered_via_handlers_module():
    importlib.import_module("jobs.runner")
    from jobs.registry import HANDLERS

    assert HANDLERS["purge_expired"].__module__ == "jobs.handlers.purge_expired"


def test_handler_module_uses_register_decorator():
    tree = ast.parse((JOBS / "handlers" / "purge_expired.py").read_text())
    ok = False
    for fn in (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "handle"):
        for d in fn.decorator_list:
            if (isinstance(d, ast.Call) and getattr(d.func, "id", getattr(d.func, "attr", "")) == "register"
                    and d.args and getattr(d.args[0], "value", None) == "purge_expired"):
                ok = True
    assert ok


def test_wired_in_package_init_not_in_runner():
    init = ast.parse((JOBS / "handlers" / "__init__.py").read_text())
    imported = set()
    for n in ast.walk(init):
        if isinstance(n, ast.ImportFrom):
            imported.add(n.module or "")
            imported.update(a.name for a in n.names)
        elif isinstance(n, ast.Import):
            imported.update(a.name for a in n.names)
    assert any("purge_expired" in x for x in imported)
    for name in ("runner.py", "legacy.py"):
        assert "purge_expired" not in (JOBS / name).read_text()
