import json
import logging
from pathlib import Path
import sys
from .dimacs import parse_dimacs


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    path = Path(sys.argv[1])
    solver = parse_dimacs(path.read_text())
    assumptions = list(map(int, sys.argv[2:]))
    logging.info('solve path=%s nvars=%s assumptions=%s', path, solver.nvars, len(assumptions))
    model = solver.solve(assumptions)
    logging.info('done status=%s', 'UNSAT' if model is None else 'SAT')
    print(json.dumps(model, sort_keys=True))


if __name__ == '__main__':
    main()
