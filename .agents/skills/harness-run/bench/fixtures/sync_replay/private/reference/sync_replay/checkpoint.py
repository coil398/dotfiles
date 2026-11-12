"""Checkpoint stores; None is both the initial and terminal cursor."""
from pathlib import Path
from .storage import atomic_json, read_json


class MemoryCheckpoint:
    def __init__(self, cursor=None):
        self.cursor = cursor
        self.history = []

    def load(self):
        return self.cursor

    def save(self, cursor):
        self.cursor = cursor
        self.history.append(cursor)


class FileCheckpoint:
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        if not self.path.exists():
            return None
        return read_json(self.path)["cursor"]

    def save(self, cursor):
        atomic_json(self.path, {"cursor": cursor})
