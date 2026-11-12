def rotate_list(items: list[int], offset: int):
    if not items: return []
    k = offset % len(items)
    return items[k:] + items[:k]


def explicit_order(items: list[str], priority: list[str]):
    rank = {x: i for i, x in enumerate(priority)}
    return sorted(items, key=lambda x: rank.get(x, len(rank)))
