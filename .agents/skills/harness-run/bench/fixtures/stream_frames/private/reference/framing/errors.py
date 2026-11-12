"""Public error hierarchy shared by the encoder and incremental decoder."""


class FrameError(ValueError):
    """An invalid argument, wire frame, or decoder state."""


class TruncatedFrameError(FrameError):
    """EOF arrived while a header or body was incomplete."""
