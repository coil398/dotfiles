"""File-backed sink: publish the candidate before changing in-memory state."""
from pathlib import Path
from .sink import MemorySink
from .events import validate_event
from .storage import atomic_json, read_json
from .codec import encode_state, decode_state


class JournalSink(MemorySink):
    def __init__(self, path):
        super().__init__()
        self.path = Path(path)
        if self.path.exists():
            self._state = decode_state(read_json(self.path))

    def apply(self, event):
        event = validate_event(event)
        candidate = self._state.clone()
        changed = candidate.apply(event)
        # Stale ids are durable too, even when changed is False.
        atomic_json(self.path, encode_state(candidate))
        self._state = candidate
        return changed
