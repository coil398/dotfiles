from .fields import lookup, MISSING


def compare(record, node):
    _, field, op, right = node
    left = lookup(record, field)
    if left is MISSING:
        left = None
    numeric = type(left) in (int, float) and type(right) in (int, float)
    strings = isinstance(left, str) and isinstance(right, str)
    if op in (':', '=', '!='):
        if strings:
            equal = left.casefold() == right.casefold()
        else:
            equal = (numeric or type(left) is type(right)) and left == right
        return not equal if op == '!=' else equal
    if not (numeric or strings):
        return False
    if op == '>':
        return left > right
    if op == '>=':
        return left >= right
    if op == '<':
        return left < right
    return left <= right


def matches(record, node):
    if node is None:
        return True
    if node[0] == 'CMP':
        return compare(record, node)
    if node[0] == 'AND':
        return all(matches(record, child) for child in node[1])
    return any(matches(record, child) for child in node[1])
