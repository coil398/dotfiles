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


def test_encoder_byte_count_and_independent_wire():
    for text in ('', 'ascii', 'é漢🙂', '\0'):
        assert encode_frame(text) == wire(text)
        assert replay([encode_frame(text)]) == [text]


def test_encoder_rejects_invalid_types_and_surrogates():
    for text in (b'x', 7, None, ['x'], '\ud800', 'a\udfff'):
        with pytest.raises(FrameError):
            encode_frame(text)


def test_input_types_fail_state_and_valid_views():
    for bad in ('x', None, [0, 0, 0, 0], 4):
        d = FrameDecoder()
        with pytest.raises(FrameError):
            d.feed(bad)
        with pytest.raises(FrameError):
            d.feed(b'')
        d.reset()
        assert d.feed(bytearray(wire('ok'))) == ['ok']


def test_encoder_maximum_validation_and_encoded_limit():
    for maximum in (True, False, -1, 2.5, None, '2'):
        with pytest.raises(FrameError):
            encode_frame('x', maximum)
    assert encode_frame('', 0) == b'\0' * 4
    assert encode_frame('é', 2) == wire('é')
    with pytest.raises(FrameError):
        encode_frame('é', 1)
