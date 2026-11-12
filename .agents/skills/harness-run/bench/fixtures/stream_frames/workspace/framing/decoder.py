"""Stateful framing across arbitrary transport chunks.

There are two independent dimensions of state: the stream can be accepting,
closed, or failed; an accepting stream can be waiting for a header or body.
A remembered zero length is a real frame, not a sentinel for header mode.
"""
from .errors import FrameError, TruncatedFrameError
from .limits import DEFAULT_MAXIMUM, check_size, validate_maximum
from .storage import ByteQueue
from .wire import HEADER_SIZE, decode_payload, read_length


class FrameDecoder:
    """Incremental decoder whose mutable state belongs to one instance."""

    def __init__(self, max_frame_size=DEFAULT_MAXIMUM):
        self.max_frame_size = validate_maximum(max_frame_size)
        self._queue = ByteQueue()
        self._expected = None
        self._failed = False
        self._finished = False

    @property
    def pending_bytes(self):
        """Unread header/body bytes, excluding consumed header bytes."""
        return len(self._queue) + (4 if self._expected is not None else 0)

    def reset(self):
        """Start a fresh stream with the same inclusive byte limit."""
        self._queue.clear()

    def feed(self, data):
        """Return every newly completed frame, or fail the entire call.

        Partial payloads remain raw bytes. This is necessary both for UTF-8
        split across chunks and for reporting truncation precisely at EOF.
        """
        if self._failed or self._finished:
            raise FrameError("decoder is not accepting data")
        output = []
        try:
            self._queue.append(data)
            while True:
                if self._expected is None:
                    if len(self._queue) < HEADER_SIZE:
                        break
                    header = self._queue.take(HEADER_SIZE)
                    self._expected = read_length(header)
                if len(self._queue) < self._expected:
                    break
                check_size(self._expected, self.max_frame_size)
                payload = self._queue.take(self._expected)
                self._expected = None
                output.append(decode_payload(payload))
                break
        except FrameError:
            self._failed = True
            raise
        return output

    def finish(self):
        """Close a clean stream; fail if even one frame is incomplete."""
        if self._failed:
            raise FrameError("decoder is failed")
        if self._finished:
            return []
        if self._expected is not None:
            self._failed = True
            raise TruncatedFrameError("stream ended inside a frame")
        self._finished = True
        return []
