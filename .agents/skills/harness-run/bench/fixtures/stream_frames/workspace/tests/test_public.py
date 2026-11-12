import pytest
from framing import FrameDecoder, FrameError, TruncatedFrameError, encode_frame


def test_ascii_frame():
    assert FrameDecoder().feed(b"\0\0\0\2ok") == ["ok"]


def test_split_header_and_unicode_body():
    d = FrameDecoder()
    assert d.feed(b"\0\0") == []
    assert d.feed(b"\0\2\xc3") == []
    assert d.feed(b"\xa9") == ["é"]


def test_multiple_frames():
    assert FrameDecoder().feed(b"\0\0\0\1a\0\0\0\1b") == ["a", "b"]


def test_empty_frame():
    assert FrameDecoder(0).feed(b"\0" * 4) == [""]


def test_truncated_header():
    d = FrameDecoder()
    d.feed(b"\0\0")
    with pytest.raises(TruncatedFrameError):
        d.finish()


def test_limit_before_body():
    with pytest.raises(FrameError):
        FrameDecoder(2).feed(b"\0\0\0\3")


def test_finish_then_reset():
    d = FrameDecoder()
    assert d.finish() == []
    d.reset()
    assert d.feed(b"\0\0\0\1x") == ["x"]


def test_encoder_uses_bytes():
    assert encode_frame("é") == b"\0\0\0\2\xc3\xa9"
