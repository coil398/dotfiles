def take_until(items: list[int], stop: int):
    return items[:items.index(stop)] if stop in items else items[:]


def drop_until(items: list[int], start: int):
    return items[items.index(start):] if start in items else []
