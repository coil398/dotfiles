def prefix_sums(items: list[int]):
    out = []
    total = 0
    for x in items:
        total += x
        out.append(total)
    return out


def differences(items: list[int]):
    return [b-a for a, b in zip(items, items[1:])]
