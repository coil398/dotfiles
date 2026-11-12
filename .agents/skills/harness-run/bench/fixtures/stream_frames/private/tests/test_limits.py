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


def test_exact_multibyte_limit_and_multiple_frames():
    assert replay([wire('é') + wire('ab') + wire('')], 2) == ['é', 'ab', '']


def test_over_limit_on_fragmented_header():
    for maximum, length in ((0, 1), (2, 3), (255, 256), (1024, 0xffffffff)):
        d = FrameDecoder(maximum)
        header = length.to_bytes(4, 'big')
        assert d.feed(header[:3]) == []
        with pytest.raises(FrameError):
            d.feed(header[3:])
        with pytest.raises(FrameError):
            d.feed(b'')


def test_zero_maximum_and_constructor_validation():
    assert replay([wire('') * 4], 0) == [''] * 4
    for maximum in (-1, True, False, 1.5, '4', None):
        with pytest.raises(FrameError):
            FrameDecoder(maximum)
    assert FrameDecoder(2**40).feed(wire('ok')) == ['ok']


def test_limit_is_per_frame_and_reset_preserves_it():
    d = FrameDecoder(3)
    assert d.feed(wire('abc') * 3) == ['abc'] * 3
    with pytest.raises(FrameError):
        d.feed(wire('long'))
    d.reset()
    assert d.feed(wire('abc')) == ['abc']
    with pytest.raises(FrameError):
        d.feed((4).to_bytes(4, 'big'))
