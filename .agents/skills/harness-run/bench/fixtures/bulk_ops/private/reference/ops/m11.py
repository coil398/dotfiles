def invert_groups(mapping: dict[str, str]):
    out = {}
    for k, v in mapping.items(): out.setdefault(v, []).append(k)
    return out


def select_keys(mapping: dict[str, int], keys: list[str]):
    return {k: mapping[k] for k in keys if k in mapping}
