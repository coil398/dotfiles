from incremental_sat import Solver, parse_dimacs


def test_sat_model():
    s = Solver(3)
    s.add_clause([1, 2])
    s.add_clause([-1, 2])
    assert s.solve()[2] is True


def test_empty_clause():
    s = Solver()
    assert s.solve() == {}
    s.add_clause([])
    assert s.solve() is None


def test_assumptions_are_temporary():
    s = Solver(2)
    s.add_clause([1, 2])
    assert s.solve([-1, -2]) is None
    assert s.solve([-1])[2]
    assert s.solve() is not None


def test_add_after_solve():
    s = Solver(1)
    assert s.solve() is not None
    s.add_clause([1])
    assert s.solve() == {1: True}
    s.add_clause([-1])
    assert s.solve() is None


def test_reader():
    s = parse_dimacs('c example\np cnf 3 2\n1 -2 0\n2 0\n')
    assert s.solve()[1]
    assert len(s.solve()) == 3
