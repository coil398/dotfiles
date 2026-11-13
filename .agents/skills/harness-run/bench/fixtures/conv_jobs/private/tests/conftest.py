import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    from jobs import metrics, retry

    metrics.reset()
    sleeps = []
    monkeypatch.setattr(retry, "_sleep", sleeps.append)
    return sleeps
