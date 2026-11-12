def intersection(left: list[int], right: list[int]):
    return list(dict.fromkeys(x for x in left if x in right))


def difference(left: list[int], right: list[int]):
    return [x for x in left if x not in right]
