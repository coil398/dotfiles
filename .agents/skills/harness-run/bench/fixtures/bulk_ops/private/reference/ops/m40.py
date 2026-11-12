def zip_fill(left: list[int], right: list[int], fill: int):
    return [[left[i] if i < len(left) else fill, right[i] if i < len(right) else fill] for i in range(max(len(left),len(right)))]


def split_on(items: list[int], delimiter: int):
    out = [[]]
    for x in items:
        if x == delimiter: out.append([])
        else: out[-1].append(x)
    return out
