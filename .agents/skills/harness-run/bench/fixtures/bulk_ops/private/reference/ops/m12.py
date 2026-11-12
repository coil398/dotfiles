def omit_keys(mapping: dict[str, int], keys: list[str]):
    return {k: v for k, v in mapping.items() if k not in keys}


def merge_sums(left: dict[str, int], right: dict[str, int]):
    out = left.copy()
    for k, v in right.items(): out[k] = out.get(k, 0) + v
    return out
