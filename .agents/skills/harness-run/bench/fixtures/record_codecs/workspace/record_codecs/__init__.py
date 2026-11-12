"""Lazy, complete format dispatch; no runtime schema registry."""
from importlib import import_module

FORMATS = tuple(f"r{n:03d}" for n in range(1, 193))


def encode(format_id: str, record: dict) -> dict:
    if format_id not in FORMATS:
        raise KeyError(format_id)
    module = import_module(f".group{(int(format_id[1:]) - 1) // 6:02d}", __name__)
    return getattr(module, "encode_" + format_id)(record)


def decode(format_id: str, payload: dict) -> dict:
    if format_id not in FORMATS:
        raise KeyError(format_id)
    module = import_module(f".group{(int(format_id[1:]) - 1) // 6:02d}", __name__)
    return getattr(module, "decode_" + format_id)(payload)
