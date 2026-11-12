# Calibration

## Source, dependency and construction record

This is a feature-restoration exercise with four deliberate reductions, not a reproduction of a historical bug. Source: referencing 0.37.0, copied from `/home/coil398/.cache/uv/archive-v0/kBnNMtxDik3AFlAwvSTKH/lib/python3.13/site-packages/referencing`. The adjacent distribution METADATA and MIT COPYING were read and retained under `private/upstream/referencing-0.37.0.dist-info/`; COPYING is also distributed in workspace. Distribution metadata identifies https://github.com/python-jsonschema/referencing as the upstream source. No upstream commit is claimed.

Production modules, typing stubs and `py.typed` are ordinary copies. The complete original package and its tests are retained in `private/upstream/referencing/`. Workspace contains the reduced production package, public tests and public documentation, with no original/private/cache copy, cache path, symlink or hardlink. All fixture files were checked for symlinks and link counts; none were links. Reference production files are byte-identical to the cached distribution. `private/degradation.patch` records the complete baseline reduction:

- Remove reference traversal history insertion in `Resolver._evolve`.
- Remove schema-subresource transition handling in `Resource.pointer`.
- Remove outward anchor search in `DynamicAnchor.resolve`.
- Remove recursive scope traversal in `lookup_recursive_ref`.

Signatures, docstrings and ordinary/static resolution remain intact. The baseline passes all 170 public regression cases.

Upstream `test_core.py` and `test_jsonschema.py` were split by AST, retaining module helpers, class structure and decorators. Pointer, subresource, dynamic scope, repeated lookup, dynamic anchor and recursive anchor tests are in hidden helper modules. Every extracted test is invoked by the area wrappers (parametrized bool/opaque tests are expanded explicitly). Remaining basic tests are public, together with upstream exception and retrieval tests. The test-suite integration module `test_referencing_suite.py`, which requires its external upstream suite, is retained only in the private original archive and is not a grading dependency. Production files are not AST rewritten.

Pinned `uv_with`: `attrs==26.1.0`, `rpds-py==2026.9.1`. These are the versions actually available in the local cache. This fixture follows Addendum v2.1 and the R1 native-rpds dependency exception; it is not a stdlib-only production package. No network access, installation from a registry, model call, sleep or performance timing gate is used.

## Reproduction and oracle

From the repository root:

```sh
uv run .agents/skills/harness-run/bench/fixtures/reference_scope/private/calibrate.py --out /home/coil398/.ai-pir-runs/benchv2/reference-scope-calibration-new
python3 .agents/skills/harness-run/bench/bench.py --self-check --tasks reference_scope --out /home/coil398/.ai-pir-runs/benchv2/reference-scope-self-check-new
```

Each calibration run uses a fresh ordinary copy of workspace, overlays private/reference only for reference/mutation runs, and copies private/tests to tests_hidden. It executes public and hidden tests separately from that grading root, exactly as bench does:

```sh
uv run --offline -q --no-project --with pytest --with attrs==26.1.0 --with rpds-py==2026.9.1 python -m pytest -q tests/ --junitxml=public.xml
uv run --offline -q --no-project --with pytest --with attrs==26.1.0 --with rpds-py==2026.9.1 python -m pytest -q tests_hidden --junitxml=hidden.xml
```

`generate_oracles.py` was executed with the pinned dependencies. It launches a separate Python subprocess, prepends only the copied `private/upstream/` package, asserts that the loaded referencing module comes from that directory, and runs `_graphs.py` against it. The resulting expected transcripts are frozen in `private/tests/_expected.json`. Hidden grading depends only on files copied to the grading root, not on the original package, host paths, cache contents, installed referencing or runtime network access. To regenerate the oracle:

```sh
uv run --offline -q --no-project --with attrs==26.1.0 --with rpds-py==2026.9.1 python .agents/skills/harness-run/bench/fixtures/reference_scope/private/generate_oracles.py
```

There are five areas, each with six pytest cases. Each case compares twelve graph variants, so the corpus contains 360 generated graphs plus the extracted upstream assertions. Randomness is local and seeded by `71031 + seed * 199 + variant * 13`, with seed 0–5 and variant 0–11. Graphs vary host/URI paths, escaped keys, anchor names, dialect, keyword family, nesting depth, missing/static/dynamic anchors, boolean recursive blockers, retrieval, repeated traversal and branch origins. Full transcripts compare contents, base URI, dynamic scope and exception class/ref/message; every operation also checks the immutability of prior resolver histories. Pointer/base areas omit history from equality so their scores are not automatically coupled to history restoration. Follow-up relative and local-fragment lookups check the returned resolver behavior.

## Measured scores and independent mutations

All rows use fresh grading directories. Mutations are applied individually to the reference, not cumulatively, and the calibration runner asserts that each source edit matches exactly once. No test is edited by a mutation.

| Area | Cases | Reference | Baseline | Single reference mutation | Target area after mutation | Full hidden after mutation | Public after mutation |
|---|---:|---:|---:|---|---:|---:|---:|
| pointer | 6 | 6/6 | 0/6 | Remove pointer subresource transition block | 0/6 | 12/30 | 170/170 |
| base_uri | 6 | 6/6 | 0/6 | In `in_subresource`, replace joined base with raw identifier | 0/6 | 12/30 | 170/170 |
| dynamic | 6 | 6/6 | 0/6 | Remove DynamicAnchor outward search | 0/6 | 18/30 | 170/170 |
| recursive | 6 | 6/6 | 0/6 | Remove recursive outward search | 0/6 | 24/30 | 170/170 |
| sequential | 6 | 6/6 | 0/6 | Remove `_evolve` history insertion | 0/6 | 12/30 | 170/170 |

Reference: public 170/170, hidden 30/30 (1.0). Baseline: public 170/170, hidden 0/30 (0.0), with 30 assertion failures, zero collection/import errors and zero skips. Addendum v2.1 permits this baseline: its zero score comes from the deliberately missing semantics, not import or collection failure. Equal-sized composite cases require all generated variants in that case to pass; partial repair is measured between the five areas, not per internal assertion.

Existing-behavior regression is reported separately through public results: 0/170 failures for reference, baseline and every mutation. Upstream currently emits one pytest deprecation warning about an itertools iterable in parametrize; no test is skipped or altered to suppress it.

## Acceptance and determinism

Executed calibration output: `/home/coil398/.ai-pir-runs/benchv2/reference-scope-calibration/`. `private/results.json` records each command, full sorted case signatures, area counts and mutations; external run directories retain stdout/stderr and JUnit XML.

Reference ran in ten independent fresh grading copies: every run public 170/170 and hidden 30/30. All ten sorted `(area, case name, passed)` signatures are identical. Each area has exactly six cases according to JUnit, not a source-code function count. All five independent mutations reduce their target area, as shown above.

Offline acceptance: every public/hidden calibration command used `--offline`. An additional offline command imported attrs, native rpds and the local referencing package in a grading copy, asserted referencing was loaded beneath cwd, and printed `offline local import OK` with exit 0. `bench.py` had `uv_with` support when self-check was run, so no manual fallback was needed.

Executed bench self-check output: `/home/coil398/.ai-pir-runs/benchv2/reference-scope-self-check/`.

| fixture | reference public | reference hidden | baseline hidden |
|---|---:|---:|---:|
| reference_scope | 170/170 | 30/30 | 0/30 |

## Public specification mapping

Every hidden assertion is covered below. The frozen oracle is an independent source of expected values, not an additional contract; `workspace/docs/SPEC.md` and existing API documentation supply the contract visible to the agent.

| Area | SPEC.md sections | Assertion coverage |
|---|---|---|
| pointer | 1, 2, 3, 6 | Contents, escaped mapping keys, array paths, empty pointers/keys, missing-path error type/ref/message, nested schema boundaries, custom callbacks, final base/relative lookup and immutable parents. History equality is excluded from this area. |
| base_uri | 1, 2, 3, 6 | Joined relative/absolute identifiers, dialect-specific identifier/keyword rules, no-ID schemas, data with identifier-shaped keys, subresource discovery/crawl, custom specification/dialect transitions, booleans/opaque values, follow-up contents/errors and immutable parents. History equality is excluded. |
| dynamic | 1, 3, 4, 6 | Outermost dynamic match, skipped missing/static anchors, nested anchor resource, returned base and relative lookup, exact dynamic history, contents/errors and immutability. Extracted upstream dynamic tests use the same contract. |
| recursive | 1, 3, 5, 6 | Initial nonrecursive/boolean results, true chains, false/boolean blockers, outermost permitted match, returned resolver and later lookup, exact history, exceptions and immutable parents. |
| sequential | 1, 2, 3, 4, 6 | Interleaved/repeated and branched lookups, failed operations, retrieval/registry propagation, reused anchor/resource results, newest-first history, same-base suppression and empty starting scope in extracted upstream coverage. |

Unverified: actual model discrimination, pilot score distributions and model ranking. No model pilot, external pipeline or long-lived process was launched. No performance area or timing claim is made. Offline dependency resolution has been verified on the current machine/runtime, not every Python/platform combination. Only reference_scope fixture files were authored; no commit was created.
