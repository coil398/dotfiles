import random
import pytest
from incremental_sat import Solver
from tests_hidden.support import build, check


@pytest.mark.parametrize('seed', range(6))
def test_assumptions(seed):
    rng = random.Random(3020 + seed)
    n = 6 + seed % 3
    clauses = [[rng.choice((-1,1))*rng.randint(1,n) for _ in range(3)] for _ in range(18)]
    s = build(n, clauses)
    for _ in range(24):
        a = [rng.choice((-1,1))*rng.randint(1,n) for _ in range(rng.randint(0,5))]
        check(s, clauses, a)
        check(s, clauses)
    s = build(3, [[1,2], [-2,3]])
    check(s, [[1,2],[-2,3]], [1,-1], expected=False)
    check(s, [[1,2],[-2,3]], [-1,-3], expected=False)
    check(s, [[1,2],[-2,3]], [-1], expected=True)
    for a, error in [([0], ValueError), ([4], ValueError), ([True], TypeError), (['1'], TypeError)]:
        with pytest.raises(error):
            s.solve(iter(a))
        check(s, [[1,2],[-2,3]], expected=True)
        assert s.nvars == 3
    assert Solver().solve() == {}
