from .search import search


def _literals(values):
    result = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError('literals must be integers')
        if value == 0:
            raise ValueError('zero is not a literal')
        result.append(value)
    return tuple(dict.fromkeys(result))


class Solver:
    def __init__(self, nvars=0):
        if isinstance(nvars, bool) or not isinstance(nvars, int):
            raise TypeError('nvars must be an integer')
        if nvars < 0:
            raise ValueError('negative variable count')
        self.nvars = nvars
        self._clauses = []

    def add_clause(self, literals):
        clause = _literals(literals)
        self.nvars = max((self.nvars, *(abs(x) for x in clause)))
        if not any(-x in clause for x in clause):
            self._clauses.append(clause)

    def solve(self, assumptions=()):
        assumptions = _literals(assumptions)
        if any(abs(x) > self.nvars for x in assumptions):
            raise ValueError('assumption outside variable range')
        result = search(tuple(self._clauses), self.nvars, assumptions)
        if result is None:
            return None
        return {v: bool(result[v]) for v in range(1, self.nvars + 1)}
