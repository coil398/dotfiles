import re
from collections.abc import Mapping

FIELD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")
MISSING = object()


def valid_field(field):
    return isinstance(field, str) and FIELD.fullmatch(field) is not None


def lookup(record, field):
    value = record
    for part in field.split('.'):
        if not isinstance(value, Mapping) or part not in value:
            return MISSING
        value = value[part]
    return value
