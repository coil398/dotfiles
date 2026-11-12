from .api import Solver


def parse_dimacs(text):
    solver = None
    count = 0
    pending = []
    expected = 0
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('c'):
            continue
        parts = line.split()
        if parts[0] == 'p':
            if solver is not None or len(parts) != 4 or parts[1] != 'cnf':
                raise ValueError('invalid header')
            n, expected = map(int, parts[2:])
            if n < 0 or expected < 0:
                raise ValueError('negative header')
            solver = Solver(n)
            continue
        if solver is None:
            raise ValueError('missing header')
        for token in parts:
            lit = int(token)
            if abs(lit) > solver.nvars:
                raise ValueError('literal exceeds header')
            if lit == 0:
                solver.add_clause(pending)
                count += 1
                pending = []
            else:
                pending.append(lit)
    if solver is None or pending or count != expected:
        raise ValueError('clause count or termination')
    return solver
