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


def test_many_frames_one_call():
    values = ['a', '', 'β', '', 'end'] * 7
    assert replay([b''.join(wire(v) for v in values)]) == values


def test_complete_then_partial_body():
    d = FrameDecoder()
    assert d.feed(wire('first') + wire('second')[:-2]) == ['first']
    assert d.feed(b'nd' + wire('third')) == ['second', 'third']
    assert d.finish() == []


def test_complete_then_partial_header():
    for count in range(1, 4):
        d = FrameDecoder()
        assert d.feed(wire('a') + wire('b')[:count]) == ['a']
        assert d.pending_bytes == count
        assert d.feed(wire('b')[count:]) == ['b']


def test_zero_frames_at_boundaries():
    stream = wire('') * 6 + wire('x') + wire('') * 3
    for step in (1, 3, 4, 5, 8, len(stream)):
        assert replay([stream[i:i+step] for i in range(0, len(stream), step)]) == ['']*6 + ['x'] + ['']*3
