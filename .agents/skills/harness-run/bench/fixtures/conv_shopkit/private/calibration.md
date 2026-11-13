# conv_shopkit calibration

Conventions: generated file only via generator, frozen vendor dir, settings only via `config.get`, typing/docstrings in new modules. Legacy code reads `os.environ` directly, is untyped, and the generated file carries no "do not edit" header. Task text mentions none of them.

## Scores (hidden, per area; 3 cases each)

| Area | Reference | Naive | Baseline |
|---|---:|---:|---:|
| validation (behavior) | 3/3 | 3/3 | 2/3 |
| discounts (behavior) | 3/3 | 3/3 | 0/3 |
| display (behavior) | 3/3 | 3/3 | 0/3 |
| conv_generated | 3/3 | 0/3 | 0/3 |
| conv_config | 3/3 | 0/3 | 0/3 |
| conv_typing | 3/3 | 0/3 | 0/3 |
| conv_vendor | 3/3 | 0/3 | 0/3 |

Public: reference 6/6, naive 6/6, baseline 5/6. Naive hand-edits `shopkit/generated/fields.py` (spec untouched), reads `os.environ` in `discounts.py`, is untyped/undocumented, and patches `vendor/moneyfmt.py`. Baseline validation 2/3 is the two "reject" cases that already raise ValueError (unknown field).

Caveat: an agent that writes its own price formatting without touching vendor passes conv_vendor; the area measures "vendor untouched and display works", not that the vendor helper is used.

## Convention test -> AGENTS.md rule

| Test | AGENTS.md section / rule |
|---|---|
| conv_generated (3) | Generated code: edit `schema/fields.json`, run `tools/gen_fields.py`; generated file equals generator output (render + CLI) and contains `discount_pct` |
| conv_config::test_cap_comes_from_config_get, test_string_setting_is_converted | Settings: read through `shopkit.config.get`, convert string values |
| conv_config::test_no_direct_environment_access | Settings: no `os.environ` / `os.getenv` outside config.py |
| conv_typing::test_fully_annotated | Typing: full annotations on public functions of new modules |
| conv_typing::test_docstring_summary_line, test_docstring_sections | Typing: Google-style docstring, summary ends with period, `Args:` / `Returns:` |
| conv_vendor (3) | Vendored code: frozen (sha256 of every file, helper behaviour), work around in `shopkit/`; each case also requires `display_price(505) == "$5.05"` |

## Determinism

10 repeated gradings of reference/naive/baseline: identical results (10/10). `bench.py --self-check --tasks conv_shopkit`: reference 21/21, baseline 2/21. Stdlib + pytest only, no network, no sleep.
