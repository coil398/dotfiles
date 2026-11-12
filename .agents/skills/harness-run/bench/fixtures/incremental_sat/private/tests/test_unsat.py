import random
import pytest
from tests_hidden.support import build, check, pigeon


@pytest.mark.parametrize('seed', range(6))
def test_unsat(seed):
    rng = random.Random(2020 + seed)
    # Complete blocking set: each assignment is forbidden by its own clause.
    n = 3 + seed % 3
    clauses = [[v if mask & (1 << (v-1)) else -v for v in range(1,n+1)]
               for mask in range(1 << n)]
    rng.shuffle(clauses)
    check(build(n, clauses), clauses, expected=False)
    # A branching conflict without explicit opposite units.
    n, clauses = pigeon(2 + seed % 2)
    check(build(n, clauses), clauses, expected=False)
    check(build(4, [[]]), [[]], expected=False)
