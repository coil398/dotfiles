import json
from pathlib import Path
from .merge import merge


def _read(path, active):
    path = Path(path).resolve()
    if path in active:
        raise ValueError("include cycle: " + " -> ".join(map(str, (*active, path))))
    active = (*active, path)
    with path.open(encoding="utf-8") as stream:
        doc = json.load(stream)
    if not isinstance(doc, dict):
        raise ValueError(f"configuration root must be an object: {path}")
    includes = doc.pop("$include", [])
    if isinstance(includes, str):
        includes = [includes]
    if not isinstance(includes, list) or any(not isinstance(p, str) for p in includes):
        raise ValueError(f"$include must be a path or list of paths: {path}")
    result = {}
    for include in includes:
        result = merge(result, _read(Path(include), active))
    return merge(result, doc)


def load(path, *, overrides=None):
    result = _read(path, ())
    if overrides is not None:
        if not isinstance(overrides, dict):
            raise ValueError("overrides must be an object")
        result = merge(result, overrides)
    return result
