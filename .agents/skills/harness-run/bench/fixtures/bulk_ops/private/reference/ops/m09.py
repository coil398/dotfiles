def partition_even(items: list[int]):
    return [[x for x in items if x % 2 == 0], [x for x in items if x % 2 != 0]]


def move_zeros(items: list[int]):
    return [x for x in items if x != 0] + [0] * items.count(0)
