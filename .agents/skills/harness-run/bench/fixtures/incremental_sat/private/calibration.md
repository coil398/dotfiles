# Calibration

## Construction and scope

This is an original stdlib-only C2 fixture, following contract Addendum v2.1 and plan2-astra section 1 / C2. There is no vendored upstream package, version, license, or patch to preserve; common preparation steps about copying upstream/cache contents are inapplicable. No cache paths, upstream originals, or private material are present in workspace. Files are ordinary files, with no symlinks or hardlinked cache copies.

The complete baseline is a correct truth-table solver. The reference replaces only `incremental_sat/search.py`; the API, DIMACS reader, and CLI are byte-identical. Reference search uses two watched literals, first-UIP learned clauses, nonchronological backtracking, activity-based branching and saved phases. A fresh search context per solve makes assumption-dependent learning local to that call. Persistent learned clauses are not required by the public specification.

## Reproduction and evidence

From the fixture root:

```sh
uv run --no-project private/calibrate.py
```

The script makes fresh grading directories under `/home/coil398/.ai-pir-runs/benchv2/`, copies workspace, overlays private/reference only for reference/mutation runs, and copies private/tests into tests_hidden. Both grading commands exactly match the bench contract:

```sh
uv run -q --no-project --with pytest python -m pytest -q tests --junitxml=public.xml
uv run -q --no-project --with pytest python -m pytest -q tests_hidden --junitxml=hidden.xml
```

Reference and baseline public suites each pass 5/5. No hidden collection/import errors or skips. Each of the five hidden areas has six parametrized cases, for 30 total. `results.json` preserves the final calibration's scores, ten reference runs, timings, mutation definitions and evidence paths. Full stdout/stderr/JUnit evidence remains in the recorded temporary directory.

## Scores and executed single mutations

| Area | Reference | Baseline | Mutation applied independently to fresh reference | Target area after mutation |
|---|---:|---:|---|---:|
| sat | 6/6 | 6/6 | Return all-false assignment at successful search exit | 0/6 |
| unsat | 6/6 | 6/6 | Return a model rather than None at a root propagation conflict | 0/6 |
| assumptions | 6/6 | 6/6 | Pass empty assumptions to search in api.py | 0/6 |
| incremental | 6/6 | 6/6 | Replace stored clauses with the newly added clause | 0/6 |
| performance | 6/6 | 0/6 | Replace search.py with baseline truth-table search | 0/6 |
| Total | 30/30 (1.0) | 24/30 (0.8) | | |

Mutation runs execute the target area's unchanged six tests, not synthetic substitute assertions. Four mutations are single textual edits; the performance mutation is a single engine replacement. Edits are never cumulative. The script verifies each textual edit occurs exactly once and each mutation lowers its target area's score. Baseline's six performance failures are subprocess deadlines; its other 24 cases genuinely pass. Addendum v2.1 permits this high baseline score.

## Public specification mapping

All assertions in each parametrized case and shared helpers are covered by these public sections; case names and seed derivations are in the tests.

| Area | SPEC.md sections | Assertions and oracle |
|---|---|---|
| sat | 1, 2, 5 | Planted small formulas, duplicate literals/tautologies, total bool models including unused variables, fresh returned dicts, DIMACS clauses spanning lines; validate original clauses directly |
| unsat | 1, 2 | Complete assignment-blocking clauses, pigeonhole impossibility, explicit empty clauses; assert exact None result |
| assumptions | 1, 2, 3 | Fixed-seed CNFs and assumption histories checked with independent exhaustive truth tables; duplicates, contradictions, invalid literal exceptions, unchanged variable count, recovery after UNSAT/error |
| incremental | 1, 2, 3, 4 | Fixed-seed clause additions and re-solves against independent exhaustive truth tables, new variables, invalid-call atomicity, tautology growth, input preservation, empty-clause permanence, independent instances |
| performance | 2, 3, 4, 6 | Pigeonhole UNSAT (7/6 and 8/7), planted 3-CNF SAT (220/260 variables, 1600 clauses), implication chains (1000/1200 variables), assumption UNSAT/restoration and addition after solves; total models and every original constraint validated inside subprocess |

The small-input oracle enumerates assignments independently of the production solver and checks the unnormalized original clauses plus assumptions. Random streams have fixed seeds. Large planted formulas have an independently generated satisfying assignment, and returned models are checked rather than compared to that particular assignment. Large UNSAT expectations rely only on pigeonhole impossibility or a forced implication chain and opposite unit, never on a guessed random-CNF classification.

## Determinism, performance and offline checks

Final reference suite: ten fresh-copy runs, each 30/30, with identical sorted (area, case name, pass) signatures. The reproduction script asserts equality of all ten signatures.

Measured reference process durations in family order, conservatively including uv startup: 0.049785, 0.384090, 0.094499, 0.196226, 0.017963, 0.018700 seconds. Deadline is 8 seconds per subprocess, over 20.8 times the measured maximum (required minimum: 10 times). The script checks this margin. Tests measure the child process directly; they do not trust solver-supplied counters. Timeout failures contain `timed out` / `TimeoutExpired` for bench classification. No sleeping, network, or non-performance wall-clock assertions are used.

Offline command succeeded in a fresh reference grading copy:

```sh
uv run --offline -q --no-project --with pytest python -c 'import pytest, incremental_sat; assert incremental_sat.Solver().solve() == {}'
```

No `uv_with` dependencies are needed. Additional offline CLI checks executed on both reference and baseline copies: parse a DIMACS file, return a valid SAT model including an unused variable, then return JSON null under contradictory assumptions; all exit 0.

Final bench command:

```sh
python3 /home/coil398/dotfiles/.agents/skills/harness-run/bench/bench.py --self-check --tasks incremental_sat --out /home/coil398/.ai-pir-runs/benchv2/incremental-sat-self-check-final
```

| fixture | reference public | reference hidden | baseline hidden |
|---|---:|---:|---:|
| incremental_sat | 5/5 | 30/30 | 24/30 |

Bench reported zero grading infrastructure errors. Its `self-check.md` and grading XML/stdout/stderr are in the specified output directory.

## Unverified

No model pilot was run. Discrimination between strong agents, model ordering, and saturation rates remain unmeasured. Since a correct baseline earns 80%, the performance area supplies 20 percentage points of headroom under the fixed C2 recipe; baseline and mutation checks alone do not establish model discrimination. Timing portability to other machines is unverified. No commit, runtime deployment, or edits outside this fixture were performed.
