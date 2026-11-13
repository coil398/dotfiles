# jobs - project rules

Background job runner. Python 3.11, standard library only.

## Layout

- `jobs/runner.py` entry point: `run(job, store)`
- `jobs/legacy.py` the original job handlers (email, report)
- `jobs/handlers/` one module per new job type
- `jobs/registry.py` handler registry
- `jobs/clock.py` time source
- `jobs/retry.py` retry decorator
- `jobs/metrics.py` in-process counters
- `jobs/errors.py`, `jobs/store.py` shared types
- `tests/` public tests (maintained by the QA team, do not edit)

## Job handlers

- Every new job type is one module `jobs/handlers/<job_type>.py` exposing a
  function `handle(job, store)` decorated with `@register("<job_type>")` from
  `jobs.registry`.
- Import the module in `jobs/handlers/__init__.py` so that importing
  `jobs.runner` registers it. Do not add new branches to `jobs/runner.py` or
  `jobs/legacy.py`.
- Handlers return a plain `dict` and never mutate the incoming `job`.
- Handlers must be idempotent: running a job twice must not break anything.

## Time

- Get the current time only from `jobs.clock.now()`. Never call
  `datetime.now()`, `datetime.utcnow()`, `datetime.today()` or `time.time()`
  in `jobs/`, except inside `jobs/clock.py`.
- Timestamps are naive UTC `datetime` objects.

## Retries

- Retry transient failures with the `@retry(...)` decorator from `jobs.retry`.
  Do not write hand-rolled retry loops and do not call `time.sleep` yourself.
- Only exceptions derived from `jobs.errors.TransientError` are retried.

## Metrics

- Every handler reports through `jobs.metrics.incr(name, n=1)` with names of
  the form `jobs.<job_type>.<event>`:
  - `runs`: once per invocation, at the start;
  - `items`: the number of units of work processed (records removed, mails sent);
  - `failures`: once when the handler raises.

## Style

- Line length 100, black defaults, one import per line.
- Type hints are welcome but not required in this package.
- Payload keys are snake_case.
- Keep handlers free of module-level mutable state.

## Process

- Run `python -m pytest -q tests/` before handing work over.
- Commit messages: imperative mood, subject under 72 columns.
- Pull requests need one reviewer and a green CI run.
- No new third-party dependencies.
