# stream_frames calibration

## Reproduction

Run `python3 private/calibrate.py` then `python3 private/report.py` from the fixture root.
The calibrator creates fresh grading trees inside private/: copy pristine workspace/,
overlay private/reference/ where appropriate, then copy private/tests/ to tests_hidden/.
Public tests always come from the pristine workspace. Each command has a 300-second timeout.
Raw outputs are in results/*.log; exact per-case outcomes are in results/summary.json.

Commands executed from each grading root:

```sh
uv run -q --no-project --with pytest python -m pytest -q tests --junitxml=report.xml
uv run -q --no-project --with pytest python -m pytest -q tests_hidden --junitxml=report.xml
```

## Scores

Reference public **8/8**, hidden **32/32 (1.0)**. Untouched workspace public **3/8**,
hidden **6/32 (0.1875)**. All 32 identical case identities collected; no import/collection
errors, skips, or missing cases. Baseline exit 1 reflects behavior/assertion failures.

| Area | Reference | Baseline | Single-mutant area passes | Mutant suite passes |
|---|---:|---:|---:|---:|
| buffering | 4/4 | 0/4 | 1/4 | 29/32 |
| chunking | 4/4 | 1/4 | 1/4 | 19/32 |
| eof | 4/4 | 2/4 | 3/4 | 31/32 |
| limits | 4/4 | 0/4 | 1/4 | 27/32 |
| multiframe | 4/4 | 0/4 | 1/4 | 21/32 |
| reset | 4/4 | 0/4 | 0/4 | 25/32 |
| types_encoding | 4/4 | 3/4 | 2/4 | 30/32 |
| utf8 | 4/4 | 0/4 | 2/4 | 29/32 |

Every area has four cases and weight 1/8. Within-case loops do not alter scoring weights.

## Executed single mutations

Each mutant starts from a fresh reference, changes one operation, and runs all 32 cases.
Each mutant exits 1 and loses at least one case in its designated area.

### buffering

File: `framing/decoder.py`.

```diff
-return len(self._queue)
+return len(self._queue) + (4 if self._expected is not None else 0)
```

### chunking

File: `framing/storage.py`.

```diff
-self._data.extend(bytes(data))
+self._data.clear()
+        self._data.extend(bytes(data))
```

### eof

File: `framing/decoder.py`.

```diff
-if self._expected is not None or len(self._queue):
+if self._expected is not None:
```

### limits

File: `framing/limits.py`.

```diff
-if length > maximum or length > WIRE_MAXIMUM:
+if length >= maximum or length > WIRE_MAXIMUM:
```

### multiframe

File: `framing/decoder.py`.

```diff
-output.append(decode_payload(payload))
+output.append(decode_payload(payload))
+                break
```

### reset

File: `framing/decoder.py`.

```diff
-self._queue.clear()
-        self._expected = None
-        self._failed = False
-        self._finished = False
+self._queue.clear()
```

### types_encoding

File: `framing/wire.py`.

```diff
-return len(payload).to_bytes(HEADER_SIZE, "big") + payload
+return len(text).to_bytes(HEADER_SIZE, "big") + payload
```

### utf8

File: `framing/wire.py`.

```diff
-payload.decode("utf-8", "strict")
+payload.decode("utf-8", "replace")
```

## Public specification mapping

The table lists all four cases per area and covers their output, exception, type,
lifecycle, and accounting assertions. Sections refer to workspace/docs/NOTES.md.
The shared wire helper implements §1/§7 independently of the production encoder;
replay checks clean EOF under §4. Hidden tests import no private reference code.

| Area and cases | Public sections |
|---|---|
| buffering: `test_completed_bytes_excluded_with_next_partial`, `test_partial_body_accounting_through_completion`, `test_partial_headers_and_consumed_header`, `test_snapshot_mutable_and_noncontiguous_view` | §2, §4–6: snapshots, partial bytes, consumed header accounting |
| chunking: `test_all_two_way_splits`, `test_every_byte`, `test_header_body_and_next_header_splits`, `test_immediate_emission_then_empty_feed` | §1–2, §4: arbitrary partitions, immediate emission, clean EOF |
| eof: `test_clean_finish_idempotent`, `test_every_partial_body_including_no_bytes`, `test_feed_after_finish_rejected`, `test_partial_header_after_completed_frame` | §1, §3–4, §6: hierarchy, idempotence, closed state, truncation |
| limits: `test_exact_multibyte_limit_and_multiple_frames`, `test_limit_is_per_frame_and_reset_preserves_it`, `test_over_limit_on_fragmented_header`, `test_zero_maximum_and_constructor_validation` | §1, §3, §5: maximum validation, inclusive byte bound, early rejection, reset |
| multiframe: `test_complete_then_partial_body`, `test_complete_then_partial_header`, `test_many_frames_one_call`, `test_zero_frames_at_boundaries` | §1–2, §4, §6: wire order, empty frames, partial following frames |
| reset: `test_reset_after_each_failure_kind`, `test_reset_after_successful_eof`, `test_reset_after_truncation_and_instance_independence`, `test_reset_drops_header_body_and_expected_length` | §2–6: all lifecycle states, discard partial bytes/length, preserve bound, independence |
| types_encoding: `test_encoder_byte_count_and_independent_wire`, `test_encoder_maximum_validation_and_encoded_limit`, `test_encoder_rejects_invalid_types_and_surrogates`, `test_input_types_fail_state_and_valid_views` | §1–3, §5, §7: types, byte length, strict encoding, failed state, reset |
| utf8: `test_incomplete_unicode_waits_for_body_not_chunk`, `test_multibyte_all_body_splits`, `test_sequence_cannot_cross_frames`, `test_strict_invalid_complete_bodies` | §1–5: complete-body validation, strict errors, no cross-frame sequences, reset |

## Determinism and structural checks

- Ten additional fresh reference grading trees: every run 32/32, exit 0.
- All ten sorted (area, case name, pass/fail) vectors match the initial reference vector.
- Exhaustive fixed input partitions, no randomness, network, real sleep, clock dependency, or performance thresholds.
- Package imports are local only; tests use pytest and stdlib only.
- Fixed manifest validated, reference files exclusively in allowed framing/.
- Parsed production/hidden Python sources and checked identical collected case identities.
- Literal incident chunks reproduce baseline [] (finish raises TruncatedFrameError) and reference ["hello🌍", "ok"]; reference finish returns [].
- Additional evidence: results/structural.json.

## Scope and limitations

The visible workspace has ten files: seven production modules, docs, incident log, public tests.
Production Python has 175 lines including comments/docstrings, below the approximate 650-LOC
planning guide. No unrelated APIs or filler code are added to reach a line count.
Baseline faults interact across queue replacement on feed, stopping after one frame, deferred
size validation, partial-header EOF handling, incomplete reset, and pending byte accounting.

Model trials were not run. Strong/weak-agent score bands and model discrimination remain
unmeasured design targets. All six fixture acceptance checks were executed. No commits.
