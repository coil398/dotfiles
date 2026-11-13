from jobs import handlers  # noqa: F401
from jobs import legacy
from jobs.registry import HANDLERS


def run(job, store):
    kind = job["type"]
    if kind in HANDLERS:
        return HANDLERS[kind](job, store)
    if kind == "email":
        return legacy.handle_email(job, store)
    elif kind == "report":
        return legacy.handle_report(job, store)
    elif kind == "purge_expired":
        return legacy.handle_purge_expired(job, store)
    raise ValueError("unknown job type: %s" % kind)
