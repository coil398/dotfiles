def gcd_all(items: list[int]):
    import math
    return math.gcd(*items)


def parity_runs(items: list[int]):
    return sum(i == 0 or x % 2 != items[i-1] % 2 for i, x in enumerate(items))
