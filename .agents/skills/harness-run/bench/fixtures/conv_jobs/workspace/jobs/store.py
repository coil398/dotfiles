class MemoryStore:
    def __init__(self, records=None):
        self._records = {r["id"]: r for r in (records or [])}

    def all(self):
        return list(self._records.values())

    def delete(self, ids):
        for i in ids:
            self._records.pop(i, None)
