# Calibration

All runs use disposable copies of workspace/, overlay reference only for reference/mutation runs, then copy private/tests to tests_hidden/. Commands execute from that copy's root. No benchmark/model trials were run.

Commands:

```sh
uv run -q --no-project --with pytest python -m pytest -q tests --junitxml=results.xml
uv run -q --no-project --with pytest python -m pytest -q tests_hidden --junitxml=results.xml
```

Reproduce: `uv run --no-project private/calibrate.py` from this fixture directory.

## Scores and mutations

| Area | Reference | Baseline | Single mutation | Mutated area | Full hidden score |
|---|---:|---:|---|---:|---:|
| interval | 5/5 | 1/5 | index.py: `stop = self.boundary(rows, upper, upper=True)` → `stop = self.boundary(rows, upper, upper=False)` | 2/5 | 24/40 |
| duplicates | 5/5 | 1/5 | index.py: `insort(self.buckets.setdefault(event.key, []), (event.timestamp, ordinal, event))` → `if any(row[2] == event for row in self.buckets.get(event.key, ())):` | 3/5 | 37/40 |
| ordering | 5/5 | 0/5 | engine.py: `for peer in peers:` → `for peer in reversed(peers):` | 1/5 | 31/40 |
| watermarks | 5/5 | 1/5 | index.py: `self.expiry[0][0] < frontier` → `self.expiry[0][0] <= frontier` | 1/5 | 34/40 |
| late_events | 5/5 | 1/5 | engine.py: `item.timestamp < own - self.lateness` → `item.timestamp <= own - self.lateness` | 3/5 | 36/40 |
| flush | 5/5 | 1/5 | stream.py: `if isinstance(item, Flush):` → `remove stop at Flush` | 4/5 | 39/40 |
| validation | 5/5 | 4/5 | validation.py: `isinstance(value, bool) or not isinstance(value, int)` → `not isinstance(value, int)` | 3/5 | 38/40 |
| performance | 5/5 | 1/5 | index.py: `start = self.boundary(rows, lower)` → `for timestamp, _, event in rows:` | 2/5 | 37/40 |

Reference: public 10/10, hidden 40/40 (1.0). Baseline: public 5/10, hidden 10/40 (0.250); all 40 cases collected without import failures.

The starting package derives from the reference with four local faults: strict interval scan instead of indexed lookup; reversed peer emission; expiration delayed until both watermarks using their minimum; and a zero-lateness inclusive rejection rule. Its iterator also continues after Flush. See workspace source for the exact implementation; public docs do not disclose these faults.

## Specification mapping

Every assertion, including helper/oracle equality, maps to the public SPEC.md sections below. Metric/state assertions use sections 5 and 8. Case names and full pass/fail signatures are preserved in results.json.

| Area (all five cases) | SPEC.md sections and assertions |
|---|---|
| interval | 2 (closed range, keys, identity, negative/large times), 3 (oracle sequence), 7 (adapter parity) |
| duplicates | 2–3 (occurrence Cartesian product, original identities, no deferred emission), 4 (equal watermarks), 6 (Flush) |
| ordering | 2–3 (timestamp and arrival tie order, payload opacity, batch order), 5 (expiration), 7 (adapter parity) |
| watermarks | 1 (atomic error), 4 (monotonicity), 5 (opposite-side frontier, exact counts, match before discard), 8 (evicted) |
| late_events | 4 (own watermark, strict threshold, lateness, unknown), 5 (no late retention), 8 (no work for dropped event) |
| flush | 1 (closed precedence), 5–6 (clear state, independent instances), 7 (single pass, no read-ahead, stop and propagate) |
| validation | 1 (types, errors, atomicity, frozen messages, payload identity), 5 (read-only retained), 8 (read-only counters) |
| performance | 2–3 (known pair counts), 5 (exact retained/key counts), 8 (actual probes, visits, expiration, sparse and dense bounds) |

## Determinism and limits

Reference hidden suite: 10/10 fresh grading copies, each 40 passed; identical sorted (area, case name, pass) signatures. Small-input oracle scans all accepted history independently of reference indexes/eviction. Random case uses fixed seed 921. Large inputs use analytically known outputs; no sleep, network, clock or timing thresholds. Package uses only stdlib; tests use pytest.

Each mutation is independently applied to a fresh reference, never cumulatively. Each of the eight mutations lowers its target area's score. The mutation harness asserts the original edit occurs exactly once. It does not change public/hidden tests or use model calls.

Unverified: model discrimination and predicted model score ranges require parent-run trials; reference/baseline/mutations cannot establish model ordering. Size targets are approximate; this fixture keeps a compact seven-module production implementation rather than padding unrelated files.
