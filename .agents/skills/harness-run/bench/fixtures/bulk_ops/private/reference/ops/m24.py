def pad_right(items: list[int], size: int, fill: int):
    return items[:] + [fill]*max(0, size-len(items))


def trim_edges(items: list[int], value: int):
    a, b = 0, len(items)
    while a < b and items[a] == value: a += 1
    while b > a and items[b-1] == value: b -= 1
    return items[a:b]
