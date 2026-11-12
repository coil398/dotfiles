def union(left: list[int], right: list[int]):
    return list(dict.fromkeys(left + right))


def frequencies_sorted(items: list[int]):
    counts = {}
    for x in items: counts[x] = counts.get(x, 0)+1
    return [[x, counts[x]] for x in sorted(counts, key=lambda x: (-counts[x], x))]
