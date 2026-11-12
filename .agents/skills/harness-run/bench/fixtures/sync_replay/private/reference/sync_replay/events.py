"""Validate events at the sink boundary, before changing any state."""
from copy import deepcopy


def validate_event(event):
    """Return an owned event dictionary; invalid input raises ValueError."""
    if not isinstance(event, dict):
        raise ValueError("event must be a dictionary")
    if not isinstance(event.get("id"), str) or not event["id"]:
        raise ValueError("id must be a nonempty string")
    if not isinstance(event.get("key"), str):
        raise ValueError("key must be a string")
    revision = event.get("revision")
    if type(revision) is not int or revision < 0:
        raise ValueError("revision must be a nonnegative integer")
    if event.get("op") not in ("put", "delete"):
        raise ValueError("unknown operation")
    if event["op"] == "put" and "value" not in event:
        raise ValueError("put requires value")
    return deepcopy(event)
