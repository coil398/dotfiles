def sign_counts(items: list[int]):
    return [sum(x < 0 for x in items), items.count(0), sum(x > 0 for x in items)]


def sum_distinct(items: list[int]):
    return sum(set(items))
