# Stream framing protocol

## 1. Wire format and API

Import `FrameDecoder`, `FrameError`, `TruncatedFrameError`, and `encode_frame`
from `framing`. A frame is four unsigned big-endian length bytes followed by
exactly that many payload bytes. Length counts bytes, not Unicode characters.
Payloads are strict UTF-8. Zero-byte payloads represent the empty string.
There is no delimiter or padding. The default maximum is 1,048,576 bytes.

`FrameDecoder(max_frame_size=1048576)` constructs an independent decoder.
`encode_frame(text, max_frame_size=1048576)` returns immutable header+payload
bytes. Both maximum arguments must be nonnegative integers, excluding bool;
other values raise `FrameError`. A maximum above the 32-bit wire ceiling is
allowed, but encoded lengths still cannot exceed 4,294,967,295.

## 2. Incremental delivery

`feed(data)` accepts bytes, bytearray, or memoryview (converted to bytes in
logical view order). Other types raise `FrameError` and fail the decoder.
The input is snapshotted before returning; later caller mutations cannot
change retained data. Empty input has no effect on an accepting decoder.
Headers and bodies may be split at any byte, including inside UTF-8 sequences.
No payload decoding takes place until the complete body is available.

Each call returns a list of all newly completed strings, in wire order,
including empty strings. A call may complete an earlier partial frame and
several new frames and leave a partial next header or body. Chunk boundaries
do not change the result. Input must neither be dropped nor emitted twice.
A completed frame is emitted immediately, without waiting for the next call.

## 3. Limits and protocol errors

As soon as all four header bytes arrive, a length strictly greater than the
configured maximum raises `FrameError`, even if no body bytes have arrived.
The bound is inclusive and applies to each frame separately. A zero maximum
accepts empty frames only. Invalid complete UTF-8 bodies raise `FrameError`;
overlong sequences, surrogates, isolated continuation bytes, and incomplete
sequences at the end of a complete body are invalid. Sequences cannot span
frames. Frame length limits are checked before body decoding.

`FrameError` subclasses ValueError. `TruncatedFrameError` subclasses FrameError.
Any invalid input type, oversized header, or malformed payload puts the decoder
in a failed state. Subsequent feed and finish calls raise FrameError until
reset, including empty feed. A failing feed raises rather than returning a
partial result, even if valid frames preceded the error in that same call.
Do not depend on pending_bytes after failure. Encoder errors do not affect any
decoder. Exception messages are not part of the API.

## 4. End of stream

`finish()` returns [] and closes an accepting decoder if no frame is pending.
Calling finish again after success also returns []. Feed after successful
finish raises FrameError, even for empty input. A partial header (1–3 bytes)
or a parsed header with an incomplete nonempty body causes finish to raise
TruncatedFrameError and fail the decoder. A complete empty frame is never
truncation. finish does not silently discard input or emit a partial string.

## 5. Reset and independent instances

`reset()` returns None, discards all pending bytes and any remembered body
length, and returns a failed, closed, or accepting decoder to accepting state.
It preserves the configured maximum. Repeated resets are harmless. Resetting
one instance cannot affect another. Subsequent input starts a new wire stream.

## 6. Buffered byte accounting

`pending_bytes` is a read-only property. While accepting, it is the number of
stored unconsumed bytes: a partial header counts 1–3; after a complete header
has been parsed, only the received partial body counts (the four consumed
header bytes do not count). A parsed nonempty header with no body therefore
has pending_bytes == 0 but finish still reports truncation. Completed frames
contribute nothing. It is zero initially, after successful finish, and reset.

## 7. Encoder validation

The encoder accepts str only and uses strict UTF-8, so lone surrogate code
points raise FrameError. Invalid text types, invalid maximum arguments, and
payloads above either length bound raise FrameError. The header records the
encoded byte length. The encoder has no mutable shared state. Tests may build
wire bytes independently of the encoder; repairing one path must not rely on
matching errors in the other path.

## 8. Local reproduction

The package entry point in framing/__init__.py exports the APIs through
framing/codec.py. codec connects the encoder and decoder; decoder uses the
wire, storage, and limits modules. logs/incident.log records a transport's
hex-encoded chunks and the observed output. Replay those exact chunks via
feed; successful completion yields the expected list and finish returns [].
Run `uv run -q --no-project --with pytest python -m pytest -q tests`.
