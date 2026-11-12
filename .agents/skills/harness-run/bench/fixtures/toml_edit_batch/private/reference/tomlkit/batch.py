"""Transactional, style-preserving edits over TOMLKit's object graph."""
from copy import deepcopy

from tomlkit.container import Container, OutOfOrderTableProxy
from tomlkit.items import AbstractTable, Array, AoT, SingleKey, Table
from tomlkit.toml_document import TOMLDocument
from tomlkit.api import parse


def _mapping(node):
    return isinstance(node, (Container, AbstractTable, OutOfOrderTableProxy))


def _get(node, segment):
    if isinstance(segment, str):
        if not _mapping(node):
            raise TypeError("string segment requires mapping")
    else:
        if not isinstance(node, (Array, AoT)):
            raise TypeError("index requires array")
        if segment >= len(node):
            raise IndexError(segment)
    return node[segment]


def _rename_physical(node, path, new_key):
    """Visit physical fragments, retaining the body's original order and trivia."""
    if isinstance(node, (Array, AoT)):
        _rename_physical(node[path[0]], path[1:], new_key)
        return
    body = node.value if isinstance(node, AbstractTable) else node
    for index, (key, value) in enumerate(body._body):
        if key is None or key.key != path[0]:
            continue
        if len(path) > 1:
            _rename_physical(value, path[1:], new_key)
        else:
            replacement = SingleKey(new_key, sep=key.sep)
            spelling = key.as_string()
            leading = spelling[:len(spelling) - len(spelling.lstrip())]
            trailing = spelling[len(spelling.rstrip()):]
            replacement._original = leading + replacement.as_string() + trailing
            replacement._dotted = key.is_dotted()
            body._body[index] = (replacement, value)
            if hasattr(value, "invalidate_display_name"):
                value.invalidate_display_name()
    # Rendering follows physical bodies; reparse at the transaction boundary
    # rebuilds all mapping/proxy caches from the renamed bodies.


def apply_edits(document, edits) -> TOMLDocument:
    if not isinstance(document, TOMLDocument):
        raise TypeError("document must be TOMLDocument")
    result = deepcopy(document)
    for edit in edits:
        if not isinstance(edit, dict):
            raise TypeError("edit must be dict")
        op = edit.get("op")
        if not isinstance(op, str) or op not in ("set", "delete", "rename"):
            raise ValueError("unknown op")
        fields = {"op", "path"} | ({"value"} if op == "set" else {"new_key"} if op == "rename" else set())
        if set(edit) != fields:
            raise ValueError("edit fields")
        path = edit["path"]
        if not isinstance(path, (list, tuple)):
            raise TypeError("path must be list or tuple")
        if not path:
            raise ValueError("empty path")
        for part in path:
            if isinstance(part, bool) or not isinstance(part, (str, int)):
                raise TypeError("invalid path segment")
            if isinstance(part, int) and part < 0:
                raise ValueError("negative index")
        parent = result
        for part in path[:-1]:
            parent = _get(parent, part)
        target = path[-1]
        if op == "rename":
            if not isinstance(target, str):
                raise ValueError("rename requires key")
            if not isinstance(edit["new_key"], str):
                raise TypeError("new_key must be string")
            _get(parent, target)
            if edit["new_key"] in parent:
                raise ValueError("destination exists")
            _rename_physical(result, path, edit["new_key"])
            result = parse(result.as_string())
        else:
            if op == "delete" or isinstance(target, int):
                _get(parent, target)
            elif not _mapping(parent):
                raise TypeError("set key requires mapping")
            if op == "set":
                parent[target] = deepcopy(edit["value"])
            else:
                del parent[target]
    return result
