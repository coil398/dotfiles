import random
import pytest
from incremental_sat import Solver
from tests_hidden.support import check


@pytest.mark.parametrize('seed', range(6))
def test_incremental(seed):
    rng = random.Random(4020 + seed)
    s = Solver(3)
    clauses = []
    for step in range(28):
        n = 3 + step // 7
        c = [rng.choice((-1,1))*rng.randint(1,n) for _ in range(rng.randint(1,4))]
        original = c[:]
        s.add_clause(iter(c))
        clauses.append(c[:])
        assert c == original
        check(s, clauses)
        check(s, clauses, [rng.choice((-1,1))*rng.randint(1,s.nvars)])
    s = Solver(1)
    check(s, [], [1], expected=True)
    s.add_clause([-1])
    check(s, [[-1]], expected=True)
    s.add_clause([7,-7,7])
    assert s.nvars == 7
    check(s, [[-1]], expected=True)
    for bad, error in [([9,0],ValueError), ([9,False],TypeError), ([9,'x'],TypeError)]:
        with pytest.raises(error):
            s.add_clause(iter(bad))
        assert s.nvars == 7
        check(s, [[-1]], expected=True)
    s.add_clause([])
    check(s, [[]], expected=False)
    s.add_clause([9])
    check(s, [[],[9]], expected=False)
    assert Solver(2).solve() is not None
