Repository: the current working directory, a Python incremental CNF solver.
Implement the scalable search engine described in docs/SPEC.md. The existing exhaustive solver is correct on small inputs; keep the API, DIMACS reader and CLI working. Support clause addition and repeated solves under temporary assumptions. Read README.md for the module map. Large SAT and constructed UNSAT instances must finish within the documented performance envelope.
Allowed changes: incremental_sat/ only. Do not edit tests or the public specification. Use Python stdlib only; do not delegate SAT solving to an external program or library.
Run from workspace root: `uv run -q --no-project --with pytest python -m pytest -q tests`
Do not commit.
Return: changed files, test results, anything unverified.
