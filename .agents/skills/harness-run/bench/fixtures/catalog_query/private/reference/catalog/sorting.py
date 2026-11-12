from collections.abc import Sequence
from .fields import lookup, MISSING, valid_field


def sort_fields(sort):
    if sort is None:
        return []
    if isinstance(sort, str):
        fields = sort.split(',')
    elif isinstance(sort, Sequence) and not isinstance(sort, (bytes, bytearray)):
        fields = list(sort)
    else:
        raise ValueError('sort must be text or a sequence')
    for field in fields:
        if not isinstance(field, str) or not valid_field(field[1:] if field.startswith('-') else field):
            raise ValueError('invalid sort field')
    return fields


def value_key(value):
    if value is MISSING:
        return (4, 0)
    if value is None:
        return (0, 0)
    if isinstance(value, bool):
        return (1, value)
    if type(value) in (int, float):
        return (2, value)
    if isinstance(value, str):
        return (3, value)
    raise ValueError('sort values must be scalar')


def ordered(rows, fields):
    rows = list(rows)
    for field in reversed(fields):
        descending = field.startswith('-')
        name = field[1:] if descending else field
        rows.sort(key=lambda row: value_key(lookup(row, name)), reverse=descending)
    return rows
