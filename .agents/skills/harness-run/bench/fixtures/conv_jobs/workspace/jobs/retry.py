import functools
import time

from jobs.errors import TransientError

_sleep = time.sleep


def retry(attempts=3, delay=0.1, on=(TransientError,)):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for i in range(attempts):
                try:
                    return fn(*args, **kwargs)
                except on:
                    if i == attempts - 1:
                        raise
                    _sleep(delay * 2 ** i)

        return wrapper

    return decorator
