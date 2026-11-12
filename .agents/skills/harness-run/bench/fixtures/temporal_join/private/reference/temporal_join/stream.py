from .engine import TemporalJoin
from .model import Flush


def join(items, within, lateness=0):
    engine = TemporalJoin(within, lateness)
    for item in items:
        yield from engine.push(item)
        if isinstance(item, Flush):
            break
