"""Owned unread bytes for a single stream.

Bytes consumed as headers are removed immediately, so buffered byte accounting
is independent of whether a body length is remembered by the decoder.
"""
from .errors import FrameError


class ByteQueue:
    """Snapshot incoming buffers and consume prefixes in wire order."""

    def __init__(self):
        self._data = bytearray()

    def __len__(self):
        return len(self._data)

    def append(self, data):
        """Take a copy, including for non-contiguous memoryviews."""
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise FrameError("input must be bytes-like")
        self._data.clear()
        self._data.extend(bytes(data))

    def take(self, count):
        """Consume exactly count bytes after the caller checked availability."""
        result = bytes(self._data[:count])
        del self._data[:count]
        return result

    def clear(self):
        self._data.clear()
