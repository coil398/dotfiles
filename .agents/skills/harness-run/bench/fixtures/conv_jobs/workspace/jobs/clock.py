from datetime import datetime, timezone

_override = None


def now():
    if _override is not None:
        return _override
    return datetime.now(timezone.utc).replace(tzinfo=None)
