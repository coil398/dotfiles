def argmax_first(items: list[int]):
    return items.index(max(items)) if items else None


def nearest_zero(items: list[int]):
    return min(items, key=lambda x: (abs(x), x)) if items else None
