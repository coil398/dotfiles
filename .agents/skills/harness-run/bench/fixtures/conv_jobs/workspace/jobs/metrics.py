_counters = {}


def incr(name, n=1):
    _counters[name] = _counters.get(name, 0) + n


def get(name):
    return _counters.get(name, 0)


def reset():
    _counters.clear()
