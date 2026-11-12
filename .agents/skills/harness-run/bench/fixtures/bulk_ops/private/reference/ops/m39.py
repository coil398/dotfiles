def run_lengths(items: list[int]):
    out = []
    for x in items:
        if out and out[-1][0] == x: out[-1][1] += 1
        else: out.append([x,1])
    return out


def expand_runs(runs: list[list[int]]):
    return [value for value, count in runs for _ in range(count)]
