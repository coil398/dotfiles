import os

_overrides = {}


def get(key, default=None):
    if key in _overrides:
        return _overrides[key]
    return os.environ.get("SHOPKIT_" + key.upper(), default)
