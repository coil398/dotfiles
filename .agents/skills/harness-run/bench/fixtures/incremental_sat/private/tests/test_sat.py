import random
import pytest
from incremental_sat import parse_dimacs
from tests_hidden.support import build, check


@pytest.mark.parametrize('seed', range(6))
def test_sat(seed):
    rng = random.Random(1020 + seed)
    for n in range(1, 11):
        planted = {v: rng.choice((False, True)) for v in range(1, n+1)}
        clauses = []
        for _ in range(4*n):
            c = [rng.choice((-1, 1))*rng.randint(1, n) for _ in range(rng.randint(1, 5))]
            if not any(planted[abs(x)] == (x > 0) for x in c):
                c[0] = -c[0]
            clauses.append(c)
        s = build(n + 2, clauses)
        m = check(s, clauses, expected=True)
        m[1] = not m[1]
        check(s, clauses, expected=True)
    # Reader uses the same solver, including declared unused variables.
    text = 'c planted\np cnf 4 2\n1 1\n0 -1 2 0\n'
    check(parse_dimacs(text), [[1,1], [-1,2]], expected=True)
