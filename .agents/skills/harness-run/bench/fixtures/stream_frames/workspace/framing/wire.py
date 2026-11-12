"""Stateless operations on complete headers and payloads.

The decoder supplies a complete payload. UTF-8 validation must not depend on
transport chunk boundaries, and must not join bytes from adjacent frames.
"""
from .errors import FrameError
from .limits import DEFAULT_MAXIMUM, check_size, validate_maximum

HEADER_SIZE = 4


def read_length(header):
    """Read the four-byte unsigned network-order payload size."""
    return int.from_bytes(header, "big")


def decode_payload(payload):
    """Normalize strict Unicode errors into the package's public hierarchy."""
    try:
        return payload.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise FrameError("invalid UTF-8 payload") from exc


def encode_frame(text, max_frame_size=DEFAULT_MAXIMUM):
    """Serialize one text frame, checking the encoded byte count."""
    maximum = validate_maximum(max_frame_size)
    if not isinstance(text, str):
        raise FrameError("text must be str")
    try:
        payload = text.encode("utf-8", "strict")
    except UnicodeEncodeError as exc:
        raise FrameError("invalid text") from exc
    check_size(len(payload), maximum)
    return len(payload).to_bytes(HEADER_SIZE, "big") + payload
