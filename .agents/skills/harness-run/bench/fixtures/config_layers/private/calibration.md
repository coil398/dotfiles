# Calibration: config_layers

## Acceptance results

- Reference overlay: public tests **3/3 passed**; hidden tests **24/24 passed**.
- Untouched agent workspace: hidden tests **11/24 passed (45.8%)**, no import/collection error. This is above the requested approximate 10–40% range; the floor was not reached without making the baseline excessively broken, so this remains a calibration limitation.
- Reference determinism: ran the 24 hidden cases repeatedly in isolated temporary grading copies. The collected result was identical: 24 passed each run. (Repeated-run command was executed during calibration; no timing assertions or nondeterministic inputs are used.)

## Areas, mutations, and public specification mapping

Each file has four test functions (24 total), so area weights are equal.

| Area | Spec section | Single reference mutation and expected failing assertion |
|---|---|---|
| includes | `docs/NOTES.md` — Includes | Resolve children from cwd instead of declaring file; `test_nested_relative_to_declaring_file` fails. |
| merge | `docs/NOTES.md` — Merge | Replace recursive merge with shallow replacement; `test_delete_nested_key` fails. |
| cli | `docs/NOTES.md` — Overrides and CLI | Split assignment on every `=`; `test_set_splits_at_first_equals` fails. |
| validation | `docs/NOTES.md` — Includes (root document and include metadata rules) | Accept non-object roots; `test_non_object_root_rejected` fails. |
| overrides | `docs/NOTES.md` — Overrides and CLI (final layer) | Replace nested mappings instead of recursively merging; `test_nested_override_keeps_siblings` fails. |
| metadata | `docs/NOTES.md` — Includes (`$include` metadata) and Merge (reserved delete marker) | Keep `$include` in returned data; `test_include_metadata_never_leaks` fails. |

## Baseline injected defects

The starting workspace includes five interacting defects: include paths resolve against process cwd; nested mappings replace rather than merge; `--set` splits on all equals signs; null values are skipped; arrays concatenate; and deletion markers are treated as ordinary values. Together these affect loader, merge, and CLI flows. The workspace remains importable, and unaffected cases still pass.

## Scope

The package uses only Python stdlib. Tests use pytest. No network, sleep, or wall-clock behavior is involved. Hidden tests import only the package from the grading directory.
