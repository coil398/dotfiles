def product_nonzero(items: list[int]):
    total = 1
    for x in items:
        if x: total *= x
    return total


def weighted_sum(values: list[int], weights: list[int]):
    return sum(v*w for v, w in zip(values, weights))
