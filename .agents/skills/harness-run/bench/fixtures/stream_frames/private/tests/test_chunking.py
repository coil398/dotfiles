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


def test_every_byte():
    stream = wire('日本語🌍') + wire('') + wire('last')
    assert replay([bytes([byte]) for byte in stream]) == ['日本語🌍', '', 'last']


def test_all_two_way_splits():
    stream = wire('alpha') + wire('β')
    for split in range(len(stream) + 1):
        assert replay([stream[:split], b'', stream[split:]]) == ['alpha', 'β']


def test_header_body_and_next_header_splits():
    stream = wire('abcd') + wire('xyz')
    for left in range(1, 5):
        for right in range(8, 12):
            assert replay([stream[:left], stream[left:right], stream[right:]]) == ['abcd', 'xyz']


def test_immediate_emission_then_empty_feed():
    d = FrameDecoder()
    assert d.feed(b'') == []
    assert d.feed(wire('a')) == ['a']
    assert d.feed(b'') == []
    assert d.finish() == []
