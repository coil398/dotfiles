def stable_unique(items: list[int]):
    return list(dict.fromkeys(items))


def compress_runs(items: list[int]):
    return [x for i, x in enumerate(items) if i == 0 or items[i-1] != x]
