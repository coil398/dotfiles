import itertools
import random
from incremental_sat import Solver


def oracle(n, clauses, assumptions=()):
    for bits in itertools.product((False, True), repeat=n):
        if all(any(bits[abs(x)-1] == (x > 0) for x in c)
               for c in list(clauses) + [[a] for a in assumptions]):
            return True
    return False


def check(solver, clauses, assumptions=(), expected=None):
    assumptions = tuple(assumptions)
    model = solver.solve(iter(assumptions))
    if expected is None:
        expected = oracle(solver.nvars, clauses, assumptions)
    assert (model is not None) == expected
    if model is not None:
        assert type(model) is dict
        assert set(model) == set(range(1, solver.nvars + 1))
        assert all(type(k) is int and type(v) is bool for k, v in model.items())
        assert all(any(model[abs(x)] == (x > 0) for x in c)
                   for c in list(clauses) + [[a] for a in assumptions])
    return model


def build(n, clauses):
    s = Solver(n)
    for c in clauses:
        s.add_clause(iter(c))
    return s


def pigeon(holes):
    return (holes * (holes + 1),
            [[p * holes + h + 1 for h in range(holes)] for p in range(holes+1)] +
            [[-(p * holes + h + 1), -(q * holes + h + 1)]
             for h in range(holes) for p in range(holes+1) for q in range(p+1, holes+1)])


def workload(case):
    if case < 2:
        n, clauses = pigeon(6 + case)
        check(build(n, clauses), clauses, expected=False)
    elif case < 4:
        rng = random.Random(551 + case)
        n = 220 + 40 * (case - 2)
        planted = [rng.choice((False, True)) for _ in range(n)]
        clauses = []
        for _ in range(1600):
            variables = rng.sample(range(1, n+1), 3)
            c = [v * rng.choice((-1, 1)) for v in variables]
            if not any(planted[abs(x)-1] == (x > 0) for x in c):
                c[0] = -c[0]
            clauses.append(c)
        s = build(n, clauses)
        check(s, clauses, expected=True)
        a = [v if planted[v-1] else -v for v in range(1, n+1, 9)]
        check(s, clauses, a, expected=True)
        check(s, clauses, expected=True)
    else:
        n = 1000 + 200 * (case - 4)
        clauses = [[1]] + [[-v, v+1] for v in range(1, n)]
        s = build(n, clauses)
        check(s, clauses, expected=True)
        check(s, clauses, [-n], expected=False)
        check(s, clauses, expected=True)
        if case == 5:
            s.add_clause([-n])
            check(s, clauses + [[-n]], expected=False)
