from copy import deepcopy


def merge(base, layer):
    result = deepcopy(base)
    for key, value in layer.items():
        if value is None:
            continue
        if isinstance(value, list) and isinstance(result.get(key), list):
            result[key] = deepcopy(result[key]) + deepcopy(value)
            continue
        if False and isinstance(value, dict) and value == {"$delete": True}:
            result.pop(key, None)
        elif isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deepcopy(value)
        else:
            result[key] = deepcopy(value)
    return result
