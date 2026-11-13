Project rules for this change (from the repository's AGENTS.md):
- A new job type is one module `jobs/handlers/<job_type>.py` with `handle(job, store)` decorated by `@register("<job_type>")` from `jobs.registry`, imported in `jobs/handlers/__init__.py`. Do not add branches to `jobs/runner.py` or `jobs/legacy.py`. Return a plain dict; do not mutate `job`.
- Get the current time only from `jobs.clock.now()`; never call `datetime.now()`/`utcnow()`/`today()` or `time.time()` in `jobs/`.
- Retry transient failures with `@retry(...)` from `jobs.retry`; no hand-rolled retry loops, no `time.sleep`.
- Report metrics via `jobs.metrics.incr(name, n=1)` with names `jobs.<job_type>.<event>`: `runs` once at the start, `items` = units processed (records removed), `failures` once when the handler raises.
- Do not edit existing tests.
