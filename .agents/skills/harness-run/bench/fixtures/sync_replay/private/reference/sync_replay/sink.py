"""In-memory sink and a one-shot pre-write failure adapter."""
from copy import deepcopy
from .events import validate_event
from .state import ReplicaState


class MemorySink:
    def __init__(self):
        self._state = ReplicaState()

    @property
    def values(self):
        return deepcopy(self._state.values)

    @property
    def revisions(self):
        return dict(self._state.revisions)

    @property
    def applied_ids(self):
        return set(self._state.applied_ids)

    def apply(self, event):
        return self._state.apply(validate_event(event))

    def get(self, key):
        return deepcopy(self._state.values.get(key))

    def snapshot(self):
        return deepcopy(self._state.values)


class FailingSink:
    """Fail once, before call N reaches the underlying sink (1-based)."""
    def __init__(self, sink, fail_at):
        if type(fail_at) is not int or fail_at < 1:
            raise ValueError("fail_at must be positive")
        self.sink, self.fail_at, self.calls = sink, fail_at, 0

    def apply(self, event):
        self.calls += 1
        if self.calls == self.fail_at:
            raise OSError("injected sink failure")
        return self.sink.apply(event)
