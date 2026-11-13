HANDLERS = {}


def register(name):
    def decorator(fn):
        HANDLERS[name] = fn
        return fn

    return decorator
