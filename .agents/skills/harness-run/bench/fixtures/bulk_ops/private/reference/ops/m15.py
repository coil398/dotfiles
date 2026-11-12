def sort_values(mapping: dict[str, int]):
    return sorted(mapping, key=mapping.get)


def dict_delta(before: dict[str, int], after: dict[str, int]):
    return {k: v for k, v in after.items() if k not in before or before[k] != v}
