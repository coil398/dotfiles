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


def test_partial_headers_and_consumed_header():
    d = FrameDecoder()
    for count in (1, 2, 3):
        assert d.feed(b'\0') == []
        assert d.pending_bytes == count
    assert d.feed(b'\5') == []
    assert d.pending_bytes == 0
    with pytest.raises(TruncatedFrameError):
        d.finish()


def test_partial_body_accounting_through_completion():
    d = FrameDecoder()
    assert d.feed(b'\0\0\0\4ab') == []
    assert d.pending_bytes == 2
    assert d.feed(b'c') == []
    assert d.pending_bytes == 3
    assert d.feed(b'd') == ['abcd']
    assert d.pending_bytes == 0


def test_completed_bytes_excluded_with_next_partial():
    d = FrameDecoder()
    assert d.feed(wire('one') + wire('two') + wire('next')[:6]) == ['one', 'two']
    assert d.pending_bytes == 2
    d.reset()
    assert d.pending_bytes == 0


def test_snapshot_mutable_and_noncontiguous_view():
    source = bytearray(wire('hello')[:-1])
    d = FrameDecoder()
    assert d.feed(memoryview(source)) == []
    source[:] = b'x' * len(source)
    assert d.feed(b'o') == ['hello']
    interleaved = bytearray()
    for byte in wire('é'):
        interleaved.extend((byte, 99))
    assert d.feed(memoryview(interleaved)[::2]) == ['é']
    assert d.pending_bytes == 0
