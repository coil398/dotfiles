"""Legacy value dispatch, using the host language's native operators."""


def compare(symbol, a, b):
    if symbol == '==':
        return a == b
    if symbol == '!=':
        return a != b
    if symbol == '<':
        return a < b
    if symbol == '<=':
        return a <= b
    if symbol == '>':
        return a > b
    if symbol == '>=':
        return a >= b
    if symbol == 'in':
        return a in b
    if symbol == 'contains':
        return b in a
    raise ValueError(symbol)
