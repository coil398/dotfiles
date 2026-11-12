# Incremental SAT

`incremental_sat.Solver(nvars=0)` stores a monotonically growing CNF. `api.py` owns validation and model normalization, `search.py` owns search. `dimacs.py` reads CNF text and `__main__.py` provides `python -m incremental_sat file.cnf [literal ...]`.

Read docs/SPEC.md for semantics and the required search envelope. The search engine receives immutable clause tuples, a declared variable count, and temporary assumptions. The workspace contains a complete exhaustive implementation; replace the search strategy to scale to the specified families. No particular model, branching order, counters, or persistent learned-clause representation is required.
