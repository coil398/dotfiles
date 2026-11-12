from copy import deepcopy


class RecordStore:
    def __init__(self, records=()):
        self._records = [dict(record) for record in records]

    @property
    def records(self):
        return tuple(deepcopy(self._records))

