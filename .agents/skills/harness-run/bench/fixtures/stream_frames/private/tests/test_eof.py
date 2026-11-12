import pytest
from framing import FrameDecoder, FrameError, TruncatedFrameError, encode_frame


def wire(text):
    payload = text.encode('utf-8')
    return len(payload).to_bytes(4, 'big') + payload


def replay(chunks, maximum=1048576):
    decoder = FrameDecoder(maximum)
    output = []
    for chunk in chunks:
        output.extend(decoder.feed(chunk))
    assert decoder.finish() == []
    return output


def test_clean_finish_idempotent():
    assert issubclass(FrameError, ValueError)
    assert issubclass(TruncatedFrameError, FrameError)
    for stream in (b'', wire(''), wire('hello') + wire('')):
        d = FrameDecoder()
        d.feed(stream)
        assert d.finish() == []
        assert d.finish() == []
        assert d.pending_bytes == 0


def test_feed_after_finish_rejected():
    for data in (b'', wire('new')):
        d = FrameDecoder()
        d.finish()
        with pytest.raises(FrameError):
            d.feed(data)
        assert d.finish() == []


def test_every_partial_body_including_no_bytes():
    stream = wire('é漢')
    for end in range(4, len(stream)):
        d = FrameDecoder()
        d.feed(stream[:end])
        with pytest.raises(TruncatedFrameError):
            d.finish()
        with pytest.raises(FrameError):
            d.finish()


def test_partial_header_after_completed_frame():
    for count in range(1, 4):
        d = FrameDecoder()
        assert d.feed(wire('ok') + b'\0' * count) == ['ok']
        with pytest.raises(TruncatedFrameError):
            d.finish()
        with pytest.raises(FrameError):
            d.feed(b'')
