"""An immutable snapshot of a cursor-addressed sequence of pages."""
from copy import deepcopy


class FakeSource:
    def __init__(self, pages):
        self.pages = deepcopy(list(pages))
        self.calls = []
        self._by_cursor = {}
        cursor = None
        for index, page in enumerate(self.pages):
            events, next_cursor = page
            if cursor in self._by_cursor:
                raise ValueError("ambiguous cursor chain")
            self._by_cursor[cursor] = index
            if next_cursor is None and index != len(self.pages) - 1:
                raise ValueError("terminal page must be last")
            if next_cursor is not None and not isinstance(next_cursor, str):
                raise ValueError("cursor must be a string or None")
            cursor = next_cursor
        if self.pages and self.pages[-1][1] is not None:
            raise ValueError("last page must be terminal")

    def fetch(self, cursor):
        self.calls.append(cursor)
        if not self.pages and cursor is None:
            return [], None
        if cursor not in self._by_cursor:
            raise KeyError(cursor)
        return deepcopy(self.pages[self._by_cursor[cursor]])
