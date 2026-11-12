from copy import deepcopy


def merge(base, layer):
    result = deepcopy(base)
    for key, value in layer.items():
        if isinstance(value, dict) and value == {"$delete": True}:
            result.pop(key, None)
        elif isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result
