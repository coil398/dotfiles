# Calibration

## Construction and provenance

This is the C1 synthetic compiler/VM task from plan2-astra.md, not a modified
upstream library or a historical bug reproduction. Parser, API, literal-only
baseline and ordered tagged VM are original fixture code. No vendor package,
upstream originals, cache paths, dist-info or license-bearing third-party source
is needed for C1. Common preparation's upstream-copy/license steps therefore do
not apply. No third-party source or private material is present in workspace/.
All fixture files are ordinary independent files, with no symlinks or hardlinks.
Only engine.py is overlaid by the reference; parser and API remain the same as
in the agent workspace. The package uses stdlib only; tests use pytest only.
No uv_with is needed. The oracle runs solely inside the grading process.

## Reproduction and grading flow

Run from this fixture: `uv run --no-project private/calibrate.py`.
The script copies pristine workspace/, overlays private/reference/ for reference
and each independent mutation, copies private/tests/ to tests_hidden/, then runs
from that grading root:

```sh
uv run -q --no-project --with pytest python -m pytest -q tests --junitxml=<grading-dir>/tests.xml
uv run -q --no-project --with pytest python -m pytest -q tests_hidden --junitxml=<grading-dir>/tests_hidden.xml
```

Reference/baseline use separate public and hidden commands exactly as bench does.
Full case signatures, per-area scores, command, timing and offline result are
recorded in results.json; disposable grading copies retain stdout/stderr and XML.
The additional backtracking mutation combines both suites only for its small-case
semantic probe, followed by the same direct interpreter subprocess/8s limit as
the hidden scale workload.

Latest disposable run: `/home/coil398/.ai-pir-runs/benchv2/tagged-calibration-xhobhz4m`. Oracle interpreter: **Python 3.13.6** (Python stdlib `re`, no flags).

## Scores and mutations

| Area | Reference | Baseline | Single independent mutation | Mutated area | Mutated hidden total |
|---|---:|---:|---|---:|---:|
| atoms | 10/10 | 0/10 | dot also matches newline | 3/10 | 37/60 |
| priority | 10/10 | 0/10 | reverse split thread priority | 0/10 | 19/60 |
| captures | 10/10 | 0/10 | omit capture-end save | 0/10 | 20/60 |
| nullable | 10/10 | 0/10 | invert nullable-loop progress comparison | 0/10 | 18/60 |
| differential | 10/10 | 0/10 | invert character-class negation | 0/10 | 40/60 |
| performance | 10/10 | 7/10 | inject search start only at position zero | 9/10 | 19/60 |

Reference public **8/8**, hidden **60/60** (1.0). Baseline public **3/8**,
hidden **7/60** (0.1167); all 60 hidden cases collect and execute, with zero
import/collection errors or skips. Returning no match happens to satisfy seven
scale cases in the intentionally limited baseline; the semantic areas remain
implement-from-scratch. No score target was forced by injecting unrelated bugs.
Each of the six areas contains exactly ten parametrized cases. The five semantic
areas use fixed seeds 40000–40009 and compare 35 generated patterns × eight input
strings × search/fullmatch within each case, including groups, all spans, group
values, unmatched defaults, group count and Match.string. Cases need no network,
clock, sleep, external source or persisted oracle answers.

Every mutation is applied once, independently, to a fresh reference. Exact source
edits are in calibrate.py and asserted to have one occurrence before replacement.
The additional **algorithm mutation** replaces only execute with explicit ordered
backtracking (backtracking_mutant.py). It passes **58/58** public and semantic
hidden cases, but performance case 0 `(a|aa)*b` on 12,000 `a` characters times out
at **8 seconds**. This checks that small-case correctness alone does not satisfy
the scale requirement. The subprocess is the interpreter itself and is killed
and reaped on timeout; no worker process is left running.

## Specification mapping

All hidden assertions, including oracle helper and scale result assertions, map
to the following public SPEC.md sections. No private choice order, capture policy
or edge-case rule is added by the tests.

| Area (all ten cases) | Public sections / assertions |
|---|---|
| atoms | §1 spans, groups, string and unmatched defaults; §2 literal/dot/class/concatenation grammar and code-point semantics; §3 search/fullmatch and empty pattern |
| priority | §1 complete Match observations; §2 alternation/concatenation; §3 earliest start, alternative order, greedy/lazy choice and fullmatch reconsideration |
| captures | §1 capture count/spans/values/defaults; §2 opening-parenthesis numbering; §3 ordered selection; §4 repeated captures, retained skipped captures and abandoned alternatives |
| nullable | §1 empty versus unmatched capture observations; §3 empty matches and lazy selection; §4 nested empty repetition, capture updates and termination |
| differential | §1 complete API result observations; §2 all supported generated AST constructs; §3 choice priority and search/fullmatch; §4 nested and repeated capture histories |
| performance | §1 no-match/result span; §3 earliest start and whole-string acceptance; §5 explicit required families, long success/failure and bounded-state scale |

## Determinism, offline execution and performance

Ten fresh grading copies each score 60/60; sorted (area, case-name, status)
signatures are identical. Reference public passes 8/8. Offline dependency
resolution **and real imports/execution** succeed with exit 0:

```sh
uv run --offline -q --no-project --with pytest python -c 'import tagged_regex, pytest; assert tagged_regex.fullmatch("(a?)*", "aa").groups() == ("",)'
```

Performance cases use analytic expected results, never the potentially
exponential CPython oracle. Each runs the candidate in its own interpreter
subprocess with an 8-second timeout, not a candidate-reported counter.
Measured times include subprocess startup and match work, one per workload:

| Case | Reference seconds | Limit seconds |
|---|---:|---:|
| 0 | 0.064077 | 8 |
| 1 | 0.056081 | 8 |
| 2 | 0.061656 | 8 |
| 3 | 0.055332 | 8 |
| 4 | 0.052312 | 8 |
| 5 | 0.093882 | 8 |
| 6 | 0.019357 | 8 |
| 7 | 0.044992 | 8 |
| 8 | 0.089081 | 8 |
| 9 | 0.027423 | 8 |

Maximum 0.093882s; limit/reference maximum ratio **85.2×**, exceeding the required 10× margin.

## Bench self-check

Executed the requested command against the actual bench.py without modifying it:

```sh
python3 /home/coil398/dotfiles/.agents/skills/harness-run/bench/bench.py --self-check --tasks tagged_regex --out /home/coil398/.ai-pir-runs/benchv2/tagged-regex-self-check
```

| fixture | reference public | reference hidden | baseline hidden |
|---|---:|---:|---:|
| tagged_regex | 8/8 | 60/60 | 7/60 |

Exit 0; no infrastructure failures. Baseline public 3/8. Logs and self-check.md
are in the named output directory.

Unverified: discrimination among actual coding models and their score/running
time distributions. No model pilot or external long-running job was launched.
The bounded grammar is covered by deterministic differential tests, not a formal
proof over all patterns. Performance timings are machine-specific.
