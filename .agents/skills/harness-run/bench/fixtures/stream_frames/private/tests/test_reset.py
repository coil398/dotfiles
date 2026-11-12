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


def test_reset_drops_header_body_and_expected_length():
    for prefix in (b'\0', b'\0\0\0', b'\0\0\0\7', b'\0\0\0\7ab'):
        d = FrameDecoder()
        d.feed(prefix)
        assert d.reset() is None
        assert d.pending_bytes == 0
        assert d.feed(wire('new') + wire('')) == ['new', '']
        assert d.finish() == []


def test_reset_after_successful_eof():
    d = FrameDecoder(2)
    for _ in range(3):
        assert d.feed(wire('é')) == ['é']
        assert d.finish() == []
        d.reset()
        d.reset()


def test_reset_after_each_failure_kind():
    for bad in ('text', b'\0\0\0\1\xff', b'\0\0\0\4'):
        d = FrameDecoder(3)
        with pytest.raises(FrameError):
            d.feed(bad)
        d.reset()
        assert d.feed(wire('ok')) == ['ok']
        with pytest.raises(FrameError):
            d.feed(b'\0\0\0\4')


def test_reset_after_truncation_and_instance_independence():
    left, right = FrameDecoder(), FrameDecoder()
    right.feed(wire('right')[:-1])
    left.feed(wire('left')[:4])
    with pytest.raises(TruncatedFrameError):
        left.finish()
    left.reset()
    assert left.feed(wire('x')) == ['x']
    assert right.feed(b't') == ['right']
