def group_lengths(items: list[str]):
    out = {}
    for x in items: out.setdefault(len(x), []).append(x)
    return out


def pairs_last(pairs: list[list]):
    return dict(pairs)
