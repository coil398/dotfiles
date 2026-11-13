import ast
from pathlib import Path

JOBS = Path(__file__).resolve().parent.parent / "jobs"


def _old(n=2):
    from helpers import aged, rec
    from jobs import clock

    return [rec(i, aged(clock.now(), days=60)) for i in range(1, n + 1)]


def test_transient_failures_go_through_retry_module(_isolate):
    from helpers import FlakyStore
    from jobs.runner import run

    store = FlakyStore(_old(), fail_times=2)
    assert run({"type": "purge_expired", "ttl_days": 30}, store) == {"removed": 2}
    assert len(_isolate) == 2


def test_exhaustion_goes_through_retry_module(_isolate):
    import pytest
    from helpers import FlakyStore
    from jobs.errors import StoreUnavailable
    from jobs.runner import run

    store = FlakyStore(_old(), fail_times=10)
    with pytest.raises(StoreUnavailable):
        run({"type": "purge_expired", "ttl_days": 30}, store)
    assert len(_isolate) == 2


def test_no_handwritten_retry_or_sleep():
    uses_retry = False
    for path in JOBS.rglob("*.py"):
        if path.name == "retry.py":
            continue
        tree = ast.parse(path.read_text())
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                f = n.func
                assert getattr(f, "attr", getattr(f, "id", "")) != "sleep", path
            if path.parent.name == "handlers":
                if isinstance(n, ast.ImportFrom) and (n.module == "jobs.retry" or (
                        n.module == "jobs" and any(a.name == "retry" for a in n.names))):
                    uses_retry = True
                if isinstance(n, ast.Import) and any(a.name == "jobs.retry" for a in n.names):
                    uses_retry = True
    assert uses_retry
