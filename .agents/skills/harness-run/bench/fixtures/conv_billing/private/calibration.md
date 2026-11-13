# conv_billing calibration

Measures whether an agent follows AGENTS.md rules that existing code contradicts (legacy: `ValueError`, `print`, float dollars, `*` changelog bullets). Task text mentions none of them.

## Scores (hidden, per area; 4 cases each)

| Area | Reference | Naive | Baseline |
|---|---:|---:|---:|
| refund (behavior) | 4/4 | 4/4 | 0/4 |
| issue (behavior) | 4/4 | 4/4 | 0/4 |
| conv_errors | 4/4 | 0/4 | 0/4 |
| conv_logging | 4/4 | 0/4 | 0/4 |
| conv_money | 4/4 | 0/4 | 0/4 |
| conv_changelog | 4/4 | 0/4 | 0/4 |

Public: reference 6/6, naive 6/6, baseline 4/6. Baseline has no collection errors (imports inside test functions). `private/naive/` is behavior-correct, follows the legacy style (ValueError, print, float dollars, no changelog entry). Behavior tests accept int cents or float dollars; convention tests require the AGENTS.md form.

## Convention test -> AGENTS.md rule

| Test | AGENTS.md section / rule |
|---|---|
| conv_errors (4) | Errors: raise `AppError` subclasses, never builtin `ValueError`/`KeyError`/`Exception` (3 behavioral raises + AST scan of `raise`) |
| conv_logging::test_issue_logs_info | Logging: user-visible actions logged at INFO via `billing.*` logger |
| conv_logging::test_issue_prints_nothing, test_no_print_call | Logging: no `print()` |
| conv_logging::test_uses_project_logger_factory | Logging: `billing.log.get_logger(__name__)`, not `logging.getLogger` |
| conv_money (4) | Money: integer cents, `*_cents` key, no float / true division |
| conv_changelog (4) | Changelog: `## Unreleased` on top, `- <type>(billing): lowercase summary` without period, released entries untouched |

## Determinism

reference/naive/baseline grading run 10 times: identical per-area results every run (10/10). `bench.py --self-check --tasks conv_billing` reports reference 24/24 hidden and baseline 0/24. Hidden tests are stdlib + pytest only, no network, no sleep.
