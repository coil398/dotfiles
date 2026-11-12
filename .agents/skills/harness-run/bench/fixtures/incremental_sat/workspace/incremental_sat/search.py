"""Complete truth-table search. Replace this engine to meet the search envelope."""
from itertools import product


def search(clauses, nvars, assumptions):
    constraints = clauses + tuple((lit,) for lit in assumptions)
    for values in product((False, True), repeat=nvars):
        if all(any(values[abs(lit) - 1] == (lit > 0) for lit in clause)
               for clause in constraints):
            return dict(enumerate(values, 1))
    return None
