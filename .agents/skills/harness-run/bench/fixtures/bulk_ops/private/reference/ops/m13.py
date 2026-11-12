def rename_keys(mapping: dict[str, int], names: dict[str, str]):
    return {names.get(k, k): v for k, v in mapping.items()}


def counts(items: list[str]):
    out = {}
    for x in items: out[x] = out.get(x, 0) + 1
    return out
