# conv_jobs calibration

Conventions: handler registry layout, clock source, retry decorator, metrics naming. Legacy handlers use `datetime.utcnow()`, `print`, and an `if/elif` chain in `runner.py`; `handlers/` is empty. Task text mentions none of them.

## Scores (hidden, per area; 3 cases each)

| Area | Reference | Naive | Baseline |
|---|---:|---:|---:|
| purge (behavior) | 3/3 | 3/3 | 1/3 |
| resilience (behavior) | 3/3 | 3/3 | 0/3 |
| conv_registry | 3/3 | 0/3 | 0/3 |
| conv_clock | 3/3 | 0/3 | 1/3 |
| conv_retry | 3/3 | 0/3 | 0/3 |
| conv_metrics | 3/3 | 0/3 | 0/3 |

Public: reference 6/6, naive 6/6, baseline 5/6. Naive adds an `elif` in `runner.py` and a function in `legacy.py` using `datetime.utcnow()`, a hand-written retry loop with `time.sleep`, `print`, and no metrics. Baseline residuals: purge 1/3 (invalid ttl raises on unknown type) and conv_clock 1/3 (the "at most one pre-existing direct time call" AST case passes trivially).

Hidden `conftest.py` patches `jobs.retry._sleep` (recorded sleeps list) and resets metrics; `helpers.py` holds the flaky store. Neither is collected as an area.

## Convention test -> AGENTS.md rule

| Test | AGENTS.md section / rule |
|---|---|
| conv_registry (3) | Job handlers: `jobs/handlers/<type>.py`, `@register("<type>")` on `handle`, imported in `handlers/__init__.py`, no new branch in runner/legacy |
| conv_clock::test_boundary_follows_clock, test_far_past_clock_expires_nothing | Time: current time only from `jobs.clock.now()` (frozen via `clock._override`) |
| conv_clock::test_no_direct_time_calls_added | Time: no `datetime.now/utcnow/today`, `time.time` outside clock.py (legacy's single pre-existing call tolerated) |
| conv_retry::test_transient_failures_go_through_retry_module, test_exhaustion_go... | Retries: `@retry` from `jobs.retry` (patched `_sleep` records 2 sleeps for 3 attempts) |
| conv_retry::test_no_handwritten_retry_or_sleep | Retries: no own `sleep` calls; handler imports `jobs.retry` |
| conv_metrics (3) | Metrics: `jobs.<type>.runs` per invocation, `.items`, `.failures` once on raise |

## Determinism

10 repeated gradings of reference/naive/baseline: identical results (10/10). `bench.py --self-check --tasks conv_jobs`: reference 18/18, baseline 2/18. Stdlib + pytest only, no network, no real sleeping in the reference path.
