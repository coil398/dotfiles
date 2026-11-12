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


def test_multibyte_all_body_splits():
    stream = wire('é漢🙂')
    for split in range(4, len(stream)):
        assert replay([stream[:split], stream[split:]]) == ['é漢🙂']


def test_strict_invalid_complete_bodies():
    for payload in (b'\xff', b'\xc0\xaf', b'\xed\xa0\x80', b'\x80', b'\xe2\x82'):
        for prefix in (b'', wire('valid')):
            d = FrameDecoder()
            with pytest.raises(FrameError):
                d.feed(prefix + len(payload).to_bytes(4, 'big') + payload)
            with pytest.raises(FrameError):
                d.feed(b'')


def test_sequence_cannot_cross_frames():
    d = FrameDecoder()
    with pytest.raises(FrameError):
        d.feed(b'\0\0\0\1\xc3' + b'\0\0\0\1\xa9')
    with pytest.raises(FrameError):
        d.finish()
    d.reset()
    assert d.feed(wire('é')) == ['é']


def test_incomplete_unicode_waits_for_body_not_chunk():
    d = FrameDecoder()
    assert d.feed(b'\0\0\0\3\xe2') == []
    assert d.feed(b'\x82') == []
    assert d.feed(b'\xac') == ['€']
    assert d.finish() == []
