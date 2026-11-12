def integer(value, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")


def distance(value, name):
    integer(value, name)
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")


def side(value):
    if not isinstance(value, str) or value not in ("left", "right"):
        raise ValueError("side must be left or right")
