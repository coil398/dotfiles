from datetime import datetime, timedelta

from jobs.errors import StoreUnavailable
from jobs.store import MemoryStore


class FlakyStore(MemoryStore):
    def __init__(self, records, fail_times):
        super().__init__(records)
        self.fail_times = fail_times
        self.delete_calls = []

    def delete(self, ids):
        self.delete_calls.append(list(ids))
        if len(self.delete_calls) <= self.fail_times:
            raise StoreUnavailable("down")
        super().delete(ids)


def rec(i, created_at):
    return {"id": i, "kind": "k", "created_at": created_at}


def aged(now, **delta):
    return now - timedelta(**delta)
