def interval_overlap(a: int, b: int, c: int, d: int):
    return max(0, min(b, d)-max(a, c))


def split_budget(total: int, count: int):
    q, r = divmod(total, count)
    return [q+1]*r + [q]*(count-r)
