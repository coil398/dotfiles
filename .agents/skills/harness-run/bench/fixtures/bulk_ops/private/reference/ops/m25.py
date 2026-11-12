def safe_get(items: list[int], index: int, default: int):
    return items[index] if -len(items) <= index < len(items) else default


def normalize_slice(length: int, start: int, stop: int):
    a, b, _ = slice(start, stop).indices(length)
    return [a,b]
