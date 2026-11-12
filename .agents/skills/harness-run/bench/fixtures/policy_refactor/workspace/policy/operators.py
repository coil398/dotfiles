"""Value operators share Python semantics, including exception behavior."""
import operator

_OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "in": lambda left, right: left in right,
    "contains": lambda left, right: left in right,
}


def compare(symbol, left, right):
    return _OPERATORS[symbol](left, right)
