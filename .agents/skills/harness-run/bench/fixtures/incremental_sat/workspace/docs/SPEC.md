# Solver specification

## 1. API and literals

Export `Solver` and `parse_dimacs` from `incremental_sat`. `Solver(nvars=0)` accepts a nonnegative integer variable count. Variables are numbered 1..nvars; a positive literal means true and a negative literal false. Booleans are not integers for this API. Invalid counts raise ValueError (negative) or TypeError (not integer).

`add_clause(literals)` consumes a finite iterable once. Each literal must be a nonzero integer, excluding bool; invalid type raises TypeError, zero raises ValueError. The variable count grows to the maximum absolute literal, including literals in tautologies. Repeated literals are redundant. A clause containing opposite signs is always satisfied. An empty clause is false. Multiple copies of a clause are permitted. Invalid calls leave stored clauses and nvars unchanged.

`nvars` is readable. Clause storage is private. Solvers are independent. The search engine may assume that the API validated its arguments.

## 2. Results

`solve(assumptions=())` returns None exactly when no assignment satisfies every stored clause and all assumptions. Otherwise return a new dict mapping EVERY integer 1..nvars to a bool. Variables absent from clauses still appear; any satisfying assignment is acceptable. Modifying a returned model must not change later results. No clauses and zero variables gives {}. Solve must not mutate caller inputs. Do not invoke external solvers, subprocess solvers, or non-stdlib packages.

## 3. Assumptions and restoration

Assumptions are a single-use iterable with the same literal validation as clauses, but abs(literal) must be <=nvars (ValueError otherwise). Duplicate assumptions are harmless; opposite assumptions make that call UNSAT. They are temporary: later solve calls, including after UNSAT or invalid assumptions, see only stored clauses and their own assumptions. Neither nvars nor the permanent formula changes on solve. Learned clauses, if retained across calls, must remain valid for the permanent formula. There is no requirement to retain learned clauses between calls.

Example: Solver(2) with clause [1,2] has no model under [-1,-2], but has a model under [-1] and under no assumptions. A result from [-1] must set variable 2 true.

## 4. Incremental addition

Clauses may be added after any solve, including an UNSAT assumption call. All later results satisfy all permanent clauses. Adding an empty clause makes all later calls UNSAT. Adding a tautology changes no satisfiability result, but may grow nvars. Adding a variable after prior solves must extend subsequent total models. Search must not retain stale assignments or silently omit newly added constraints.

## 5. DIMACS and CLI

`parse_dimacs(text)` returns a Solver. Ignore blank lines and lines beginning with c after stripping whitespace. Require one `p cnf N M` header before literal tokens; N,M nonnegative. Clause terminator 0 may occur several times on a line and clauses may span lines. Require exactly M clauses, no unterminated clause, and literals bounded by N. Reject malformed text with ValueError. An empty clause is represented by 0. Declared but unused variables remain in total models.

CLI prints JSON: a model with stringified numeric keys, or null for UNSAT. Valid input exits 0. Reader and CLI behavior must continue to work with the new search engine.

## 6. Search envelope

Use a complete search algorithm. Exhaustive truth-table enumeration and recursive DPLL that rescans all clauses become impractical here. Suitable designs include watched-literal propagation, conflict-directed learning, backtracking and a branching heuristic. No particular internal algorithm is mandated.

The grading envelope includes planted 3-CNF (up to 260 variables / 1600 clauses), unit implication chains with up to 1200 variables, and pigeonhole CNF with up to 8 pigeons into 7 holes. Pigeonhole encoding uses one variable per pigeon/hole pair, an at-least-one clause per pigeon, and pairwise exclusions for pigeons sharing a hole. Repeated solve calls may change assumptions or append permanent clauses. Each family case executes in a fresh Python process with an 8-second deadline, excluding pytest startup. This exceeds ten times the reference's measured worst case. Tests validate every returned model against original clauses and assumptions; UNSAT is expected only for independently certified small formulas or structurally impossible families. No performance counters supplied by the implementation are trusted.
