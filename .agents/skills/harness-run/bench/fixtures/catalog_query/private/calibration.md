# catalog_query calibration

## Outcome

All six fixed-contract acceptance checks pass. Tests use stdlib plus pytest only; subprocess CLI checks invoke the same isolated Python interpreter. No model calls, networking, sleeping or clock-based assertions are used. Expected results are explicit record IDs and literal page objects, not calls into a reference oracle.

Reference public: **10/10**. Reference hidden: **40/40 (1.0)**. Baseline public: **5/10**. Baseline hidden: **16/40 (0.40)**. There are exactly eight hidden files with five collected cases each. Baseline failures are behavior failures, not import/collection errors.

| Area | Reference | Baseline | Mutated reference (target area) | Mutation |
|---|---:|---:|---:|---|
| boolean | 5/5 | 0/5 | 0/5 | `matching.py`: `return all(matches(record, child) for child in node[1])` → `return any(matches(record, child) for child in node[1])` |
| integration | 5/5 | 1/5 | 3/5 | `cli.py`: `result = method(args.query,` → `result = method('',` |
| missing | 5/5 | 2/5 | 2/5 | `matching.py`: `if left is MISSING: /         return False` → `if left is MISSING: /         left = None` |
| pagination | 5/5 | 2/5 | 0/5 | `engine.py`: `'total': len(rows)` → `'total': len(rows[offset:offset + limit])` |
| quotes | 5/5 | 5/5 | 2/5 | `tokens.py`: `''.join(chars)` → `''.join(chars).replace(' ', '')` |
| sorting | 5/5 | 0/5 | 4/5 | `sorting.py`: `for field in reversed(fields):` → `for field in fields:` |
| types | 5/5 | 2/5 | 3/5 | `literals.py`: `return float(text) if any(c in text for c in '.eE') else int(text)` → `return text` |
| validation | 5/5 | 4/5 | 4/5 | `pagination.py`: `type(offset) is not int` → `not isinstance(offset, int)` |

Each mutation is applied alone to a fresh reference overlay. It is scored against all 40 cases; the column reports its own area only. Cross-area effects are retained in `results/summary.json`. All eight mutations cause at least one failure in their own area. In the first trial, reversing key-pass order survived because the test data accidentally produced the same order; the multi-key dataset was corrected to distinguish the orders before final acceptance.

## Public specification mapping

| Hidden file and all five cases | Public spec / assertion coverage |
|---|---|
| `tests/test_boolean.py` | `workspace/docs/query.md`: §1 (parsed-query reuse and insertion order), §2 (AND/OR precedence, grouping and case-insensitive keywords), §3–4 (numeric equality). Every case checks IDs, text/parsed parity and reverse-catalog reuse. |
| `tests/test_integration.py` | `workspace/docs/query.md`: cli_page: §1,3–4,6–8; cli_plain: §2,5–8; cli_errors: §2,6–8; ownership: §1,4; reuse: §1–5,7. Checks process status/stdout/stderr, decoded payloads, input/result/records/page isolation, duplicate preservation and parsed query reuse. |
| `tests/test_missing.py` | `workspace/docs/query.md`: §1, §4 (nested traversal, missing versus null, quoted null, typed inequality), §7 (total before zero-limit slice). Every case checks selected IDs and page total. |
| `tests/test_pagination.py` | `workspace/docs/query.md`: §1 (Query and page shape), §4 (filtering), §6–7 (filter→sort→offset→limit, zero/beyond-end/oversized limits, total, metadata and stateless calls). Every case compares full page, search parity and subsequent unsorted query. |
| `tests/test_quotes.py` | `workspace/docs/query.md`: §2 (parentheses and OR), §3 (quoted keywords/operators, escaped quotes/backslashes, Unicode and empty strings), §4 (exact equality). Every case checks direct and composed-expression matches. |
| `tests/test_sorting.py` | `workspace/docs/query.md`: §1 (insertion order and nonmutation), §2 (dotted fields), §6 (key priority, stable descending ties, scalar type/missing order, sequence keys). Every case checks ordering, unchanged records and repeated-call equality. |
| `tests/test_types.py` | `workspace/docs/query.md`: §3 (numeric, boolean and quoted literals), §4 (numeric equality, boolean separation, casefold/string typing and inequality), §5 (numeric and case-sensitive string ordering). IDs include incompatible operands; numeric equality case also checks complement over present values. |
| `tests/test_validation.py` | `workspace/docs/query.md`: syntax: §2; quotes: §2–3; fields: §2,6; pagination: §7; query_sort: §1,6–7. Each raises assertion checks the documented error class, including empty-catalog/zero-limit validation. |

## Starting workspace

The starting workspace keeps the full parser and CLI wiring so imports and normal execution work. Literal conversion handles strings/null only, lookup conflates missing with null during comparison, sorting is unfinished, constructor storage shares nested inputs, and boolean offsets pass validation. These limitations are recorded only here and in the private derivation script, not in the agent prompt. `derive_baseline.py` reconstructs this scaffold from the reference; it must not run after an agent changes its workspace.

Workspace: **16 files / 487 text lines**, including **13 package modules / 316 Python lines**. This is smaller than the plan’s approximate 1,100-LOC estimate; no unrelated code or line padding was added. The eight behavioral areas and CLI integration are retained. Model difficulty bands remain hypotheses until the parent runs actual agent trials; reference/baseline/mutation calibration does not establish model discrimination.

## Reproduction and determinism

Run from any directory:

```sh
uv run -q --no-project /home/coil398/dotfiles/.agents/skills/harness-run/bench/fixtures/catalog_query/private/calibrate.py
```

For each evaluation, `calibrate.py` copies pristine `workspace/` to a fresh temporary directory under `private/`, optionally overlays `private/reference/`, copies hidden tests to `tests_hidden/`, and runs the contract commands from that directory:

```sh
uv run -q --no-project --with pytest python -m pytest -q tests --junitxml=RESULT.xml
uv run -q --no-project --with pytest python -m pytest -q tests_hidden --junitxml=RESULT.xml
```

All ten final reference repetitions return exit 0 and **40/40**, with identical case identities and passing outcomes. Fixed datasets and literal expected outputs require no random seed. The reference public run also returns exit 0. Baseline and all eight mutants return exit 1 as expected. Per-run stdout/stderr and JUnit XML are saved under `results/`; `summary.json` contains every per-area count and exact mutation. Temporary grading copies are removed.

An initial exploratory invocation from the repository root failed to import the workspace package; it is not a grading result. All reported acceptance runs use the required isolated grading-directory cwd.

## Scope and remaining limits

Only this fixture directory is owned. No bench.py, sibling fixture, global runtime configuration or commit is changed. `fixture.json` uses the fixed contract keys; all reference files are under allowed `catalog/`, public tests live under immutable `tests/`, and hidden tests do not import private files or access host-specific paths. All six fixture checks are verified. Actual model trials and model score bands are unverified and are outside this fixture job.
