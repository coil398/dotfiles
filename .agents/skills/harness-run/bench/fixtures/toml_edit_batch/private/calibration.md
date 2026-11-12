# Calibration

Fixture: `toml_edit_batch`. Acceptance: complete / PASS. No model trials, commits, delegation or memory recall were performed.

## Source and construction

TOMLKit 0.15.2 was copied from the local uv archive `sSye80tU1haxhlzqJDMb_` under `/home/coil398/.cache/uv/archive-v0`. Adjacent METADATA declares version 0.15.2, MIT, Python >=3.9, no runtime requirements. METADATA and MIT license were read and retained in `private/upstream/`; the candidate workspace includes LICENSE. The entire package, including `py.typed`, is copied normally into both `private/upstream/tomlkit/` and `workspace/tomlkit/`. Final filesystem inspection confirms zero symlinks, every file link count is one, and no host/cache path appears in workspace files. Container and items are the complete upstream implementation, not substitutes. The package's cached distribution contains no upstream tests; fixture tests are authored here rather than claimed as upstream extractions.

`private/scaffold.patch` records the only candidate-source changes from upstream: export `apply_edits` in `tomlkit/__init__.py` and add the unimplemented `tomlkit/batch.py`. The reference overlay contains those same two paths, with a working batch implementation. All original parser/container/item APIs remain available. Candidate workspace contains no original snapshot, cache paths or private grading assets.

The API/operation record format and exception classes are fully public in `workspace/docs/SPEC.md`. This is an implement-from-scaffold feature task, not a historical bug reproduction. Baseline 0 is explicitly permitted by Addendum v2.1; all cases import and collect, then fail at the unimplemented API.

## Commands and grading flow

Run from the fixture directory:

```sh
uv run --offline --no-project private/calibrate.py
```

Each run creates a fresh directory under `/home/coil398/.ai-pir-runs/benchv2/`, copies workspace, overlays reference only for reference/mutation trials, and copies private/tests into tests_hidden. Only the two allowed reference files are overlaid. Commands execute from that directory's root:

```sh
uv run -q --no-project --with pytest python -m pytest -q tests/ --junitxml=result.xml
uv run -q --no-project --with pytest python -m pytest -q tests_hidden --junitxml=result.xml
```

No `uv_with` dependencies are needed. Runtime uses stdlib only; tests use pytest. Offline public grading uses the same command with `--offline`. A separate baseline offline command imports local tomlkit and pytest and verifies version 0.15.2 and the callable export. Both succeed using cached dependencies. No network, sleeping, external services or clock-based assertions. No performance scoring area.

## Scores and independent mutations

Each mutation starts from a fresh reference; no cumulative mutations. Mutations change exactly one source expression/statement in `tomlkit/batch.py`; the harness checks the replaced text occurs exactly once. Target-area and whole-suite results are from executed tests.

| Area | Reference | Baseline | Single reference mutation | Mutated target | Whole hidden |
|---|---:|---:|---|---:|---:|
| semantics | 8/8 | 0/8 | replace set's copied value with `0` | 0/8 | 22/48 |
| rename | 8/8 | 0/8 | omit original key's surrounding whitespace | 3/8 | 43/48 |
| fragments | 8/8 | 0/8 | visit only the first physical body slot | 3/8 | 30/48 |
| layout | 8/8 | 0/8 | return parse(dumps(result.unwrap())) | 0/8 | 22/48 |
| isolation | 8/8 | 0/8 | use original document rather than deepcopy | 1/8 | 1/48 |
| validation | 8/8 | 0/8 | remove negative-index rejection | 7/8 | 47/48 |

Public: reference 5/5, baseline 1/5. Hidden: reference 48/48, baseline 0/48. Baseline: 48 failed, 0 errors, 0 skips; no import or collection errors.

Reference hidden suite: ten fresh grading copies, each 48/48, with identical sorted (area, case, outcome) signatures. `private/results.json` preserves every per-area count and signature, plus mutation and offline results. `private/calibrate.py` reproduces these checks.

## Oracle and public specification mapping

All hidden cases call only APIs declared in the public specification. Every value assertion is checked against a separate native dict/list editor starting from stdlib tomllib; it does not call reference internals. Every successful result is checked both via unwrap and by reparsing rendered TOML with tomllib. Source preservation, distinct document type/identity and unchanged native source values are checked alongside these comparisons.

| Hidden area (8 cases each) | Public SPEC sections | Assertions covered |
|---|---|---|
| semantics | 1, 2, 3, 4 | Fixed seeds 61/98/181/293/409/587/661/809, 40 documents per case; literal Unicode/empty/dotted/quoted keys, ordered rename/set/delete, array shifts, nested inline tables, AoT indices, new mapping keys, inserted table arrays; native value oracle, rendered round trip, source isolation |
| rename | 1, 3, 4 | Eight hand-written byte goldens: original position, bare/basic spelling, literal dotted destinations, raw scalar text, separator whitespace, inline/standalone comments, dotted prefixes/leaves, inline table slots, empty/Unicode keys, CRLF and nested table headers; source and round-trip values |
| fragments | 2, 3, 4 | Eight hand-written byte goldens: split parent and child renames, AoT parent and one-element subtree headers, quoted destination, dotted plus explicit fragments, CRLF header comments, split tables containing AoT; chained renames and subsequent set through final name checked against independent value oracle |
| layout | 2, 3, 4 | Eight expected renderings produced by pristine upstream's sequential single edits: scalar trivia, CRLF, inline deletion, multiline arrays with comments, scalar-to-table and table-to-scalar placement, out-of-order writes/deletion, AoT deletion/index shift; values independently checked with tomllib/native editor |
| isolation | 1, 2, 4 | Eight scenarios: empty batch byte preservation/deep copy, native inserted value isolation both ways, Item insertion isolation both ways, mid-batch failure after rename/write, producer exception identity, stop consumption at first error, independent calls, unchanged edits/values; all preserve original bytes and values |
| validation | 1, 2, 3, 4 | Eight grouped cases: empty/negative paths, bool/invalid segment/path types, scalar/array/mapping mismatches, integer-slot rename/nonstring new key, collision including same-name rename, missing intermediate/final keys, array bounds/no append, malformed operations/fields/non-dict edits/document type; original remains unchanged after earlier successful edit |

The layout oracle is the immutable pristine snapshot; `private/build_tests.py` reproduces the golden data using that snapshot, not the reference. Rename and fragment goldens are hand-written constants. Seeds are fixed; no randomized hash order influences outcomes.

## Bench self-check

Executed:

```sh
python3 /home/coil398/dotfiles/.agents/skills/harness-run/bench/bench.py --self-check --tasks toml_edit_batch --out /home/coil398/.ai-pir-runs/benchv2/toml-edit-self-check-accepted
```

| Fixture | Reference public | Reference hidden | Baseline hidden |
|---|---:|---:|---:|
| toml_edit_batch | 5/5 | 48/48 | 0/48 |

Bench exits 0 with no grading infrastructure errors. The initial construction run exposed lost trailing key whitespace in the reference and invalid test construction paths; the final version passes after those were corrected. One draft layout input triggered an existing upstream dotted scalar-to-table serialization defect; the final case exercises valid root scalar-to-table placement. This fixture does not require repairing that unrelated upstream defect.

## Limits

Model discrimination, model ordering and trial budget completion are unverified and require parent-run pilots. No full upstream test suite was available in the cached wheel or run; existing API coverage is the public parser/export check plus the pristine single-operation layout oracle. Broad TOMLKit correctness beyond fixture requirements is not established. All named fixture acceptance checks were executed.
