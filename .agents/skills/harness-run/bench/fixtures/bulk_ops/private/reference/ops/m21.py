def clamp(value: int, low: int, high: int):
    return min(high, max(low, value))


def wrap(value: int, low: int, high: int):
    return low + (value-low) % (high-low)
