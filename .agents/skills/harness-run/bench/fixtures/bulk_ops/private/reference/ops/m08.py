def interleave(left: list[int], right: list[int]):
    out = []
    for i in range(max(len(left), len(right))):
        if i < len(left): out.append(left[i])
        if i < len(right): out.append(right[i])
    return out


def flatten_once(rows: list[list[int]]):
    return [x for row in rows for x in row]
