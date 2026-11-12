"""Size policy: argument validation and per-frame byte limits."""
from .errors import FrameError

DEFAULT_MAXIMUM = 1024 * 1024
WIRE_MAXIMUM = 0xFFFFFFFF


def validate_maximum(value):
    """Accept an inclusive, nonnegative integer byte bound, excluding bool."""
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise FrameError("invalid maximum")
    return value


def check_size(length, maximum):
    """Check a decoded or encoded payload length before accepting the body."""
    if length > maximum or length > WIRE_MAXIMUM:
        raise FrameError("frame exceeds configured maximum")
