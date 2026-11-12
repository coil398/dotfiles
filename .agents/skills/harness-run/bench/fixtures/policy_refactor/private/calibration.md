# policy_refactor calibration

COVERAGE: complete. VERDICT: PASS for the six fixed fixture acceptance checks.

## Reproduction

Run `python3 private/calibrate.py` from this fixture directory. The script creates fresh grading directories only under `private/`, copies pristine `workspace/`, overlays `private/reference/` for reference/mutations, and copies `private/tests/` to `tests_hidden/`. It runs the exact uv/pytest commands from the fixed contract with JUnit output, captures logs, and removes temporary directories. There are no model calls. Package dependencies are stdlib only; test dependencies are pytest only.

Commands executed from each fresh grading root:

```sh
uv run -q --no-project --with pytest python -m pytest -q tests --junitxml=<file>
uv run -q --no-project --with pytest python -m pytest -q tests_hidden --junitxml=<file>
```

## Scores

Reference public: **12/12**, exit 0. Untouched baseline public: **5/12**, exit 1 (intentional incomplete refactor). Reference hidden: **40/40 (100%)**. Baseline hidden: **14/40 (35%)**, with 40 collected cases and no collection/import errors. Eight areas, exactly five test functions/cases each; loops combine interactions within a case and do not change weights.

| Area | Reference | Baseline | Single mutation: target area | Entire mutated suite |
|---|---:|---:|---:|---:|
| calls | 5/5 | 3/5 | 4/5 | 37/40 |
| compat | 5/5 | 1/5 | 3/5 | 38/40 |
| lexical | 5/5 | 3/5 | 4/5 | 39/40 |
| names | 5/5 | 3/5 | 4/5 | 34/40 |
| precedence | 5/5 | 2/5 | 3/5 | 31/40 |
| shortcircuit | 5/5 | 0/5 | 0/5 | 28/40 |
| trace | 5/5 | 0/5 | 1/5 | 34/40 |
| values | 5/5 | 2/5 | 4/5 | 39/40 |

## Mutation sensitivity

Each experiment begins from a fresh reference overlay and applies exactly one text replacement to one production file. All eight mutations were actually executed against all 40 hidden cases, not merely inspected. No test changes and no mutation combinations. Target failures are listed below; cross-area effects appear in the scores above.

- `calls`: Reverse argument evaluation order in evaluator.py. Fails: `test_nested_arguments_once_in_order`.
- `compat`: Coerce legacy.check return value to bool. Fails: `test_all_wrappers_route_dynamically`, `test_legacy_behavior_matches_expected`.
- `lexical`: Recognize ~ instead of # as the comment introducer. Fails: `test_comment_and_keyword_boundaries`.
- `names`: Raise NameError for a present None value. Fails: `test_present_null_across_inputs`.
- `precedence`: Parse the first or operand as a negation, bypassing and precedence. Fails: `test_logic_mix`, `test_parentheses_and_quoted_operators`.
- `shortcircuit`: Coerce selected or operands to bool. Fails: `test_skip_runtime_failures`, `test_selected_operand_identity`, `test_nested_callbacks_exactly_once`, `test_skipped_comparison_and_call`, `test_deterministic_independent_oracle`.
- `trace`: Insert the whole-expression result at the beginning of trace. Fails: `test_success_prefix_and_one_result`, `test_callback_sees_invocation_event`, `test_nonlist_trace_ignored_and_subclass_supported`, `test_shortcircuit_trace_and_reuse`.
- `values`: Reverse the operands of contains. Fails: `test_membership_directions`.

## Public specification mapping

All assertions in each listed function map to the public sections below, including expected exceptions, types, identity, trace prefixes, token/AST shape and instrumentation. Test function names are unique within an area. The only generated oracle uses independent tagged value trees, Python operators and a fixed local `random.Random(271828)`; it never imports the production parser/evaluator. Other cases use literal expected values, event sequences, and spy callbacks.

| Area / all five case functions | Public docs/NOTES.md sections covering every assertion |
|---|---|
| `calls`: `test_nested_arguments_once_in_order`, `test_resolution_before_arguments`, `test_callback_error_identity_and_trace`, `test_noncallable_after_arguments`, `test_function_map_and_return_identity` | §5 (resolution, argument order, invocation, exception identity), §6 (failure prefix), §7 (mapping and result identity) |
| `compat`: `test_all_wrappers_route_dynamically`, `test_new_api_pipeline_hooks`, `test_compilation_parses_once_and_compiler_hook`, `test_legacy_behavior_matches_expected`, `test_frozen_ast_and_compiled_no_state` | §1 (dynamic API wiring), §3 (AST), §7 (frozen objects, compilation and reuse), §§4–6 (compatibility behavior) |
| `lexical`: `test_escape_values_and_offsets`, `test_comment_and_keyword_boundaries`, `test_literal_operator_words`, `test_symbols_commas_and_tokens_immutable`, `test_lexical_error_positions` | §2 (escapes, offsets, token kinds, comments, boundaries, punctuation, errors), §3 (quoted syntax literals) |
| `names`: `test_present_null_across_inputs`, `test_missing_and_successful_prefix`, `test_membership_before_get_and_no_mutation`, `test_truthy_and_falsy_names`, `test_shared_nested_values_not_changed` | §4 (membership, lookup, null, missing, identity), §6 (name/failure trace), §7 (non-mutation) |
| `precedence`: `test_logic_mix`, `test_not_comparison_and_repeated_not`, `test_parentheses_and_quoted_operators`, `test_invalid_grammar_is_eager`, `test_ast_shape_and_token_input` | §3 (grammar, precedence, eager syntax validation, AST shape), §6 (no trace before syntax success), §7 (tokens unchanged) |
| `shortcircuit`: `test_skip_runtime_failures`, `test_selected_operand_identity`, `test_nested_callbacks_exactly_once`, `test_skipped_comparison_and_call`, `test_deterministic_independent_oracle` | §§3–4 (precedence, short circuit, operand values/types), §5 (skipped runtime work and callback order) |
| `trace`: `test_success_prefix_and_one_result`, `test_callback_sees_invocation_event`, `test_failed_argument_prefix`, `test_nonlist_trace_ignored_and_subclass_supported`, `test_shortcircuit_trace_and_reuse` | §6 (every event and timing rule), §5 (failure prefix), §7 (reuse, no state leakage) |
| `values`: `test_membership_directions`, `test_type_errors_keep_trace_prefix`, `test_equality_and_ordering_python_values`, `test_operand_types_preserved`, `test_comparison_operand_order` | §4 (Python operations, direction, types, identity), §5 (operand/callback order), §6 (exception prefixes) |

## Determinism and legacy validation

**10/10** separately prepared reference grading roots produced **40 passed, 0 failed, 0 errors, 0 skipped**. The script compared all 40 `(area, test name, status)` records to the reference run, not just process exit codes. Timing and JUnit timestamps are not compared. No network, real sleeping or wall-clock-dependent assertions occur in package or tests.

The source-only legacy implementation uses its own character scanner and stack-bytecode compiler/interpreter. It is structurally different from the new immutable AST pipeline. A separate legacy audit passed 64 fixed-seed generated expressions against the independent value-tree oracle, five eager syntax failures, argument order, trace timing and resolved noncallables. The reference overlay retires the four old implementation modules and routes the compatibility functions through the public API; the hidden tests instrument the documented API seams to reject a wrapper that simply calls the old engine.

## Artifacts and scope

`evidence/results.json` stores all per-case outcomes and per-area counts. `evidence/{reference,baseline}-*.{log,xml}`, `evidence/mutation-*.{log,xml}`, `evidence/determinism-*.{log,xml}` and `evidence/legacy-audit.log` contain actual execution evidence. `calibrate.py` contains the exact single mutations. All generated grading roots were removed.

Only `fixtures/policy_refactor/**` was modified; no commits, delegation, memory recall, or edits to bench.py / other fixtures.

## Limits and differences from the design estimate

The starting package has **14 Python files / 527 lines**, plus the public specification and twelve public tests. The plan's ~1,200 production LOC was an estimate; this fixture is smaller. No unrelated modules or line padding were added to reach that estimate. The language and behavior-preserving refactor scope follow row 5.

The requested baseline range, equal case counts, full reference passes, mutation sensitivity, public assertion mapping and ten-run determinism are verified. Real coding-agent score separation (strong ~50–90%, weak ~10–60%) remains **unmeasured**; passing fixture acceptance does not establish that model-level calibration. Host-level private-file access is not sandboxed by this fixture; the harness must provide workspace-only isolation for a strict blind benchmark.
