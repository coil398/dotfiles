Add a new job type `purge_expired` to the `jobs` package.

A `purge_expired` job looks like `{"type": "purge_expired", "ttl_days": 30}`. Running it through `jobs.runner.run(job, store)` deletes every record in the store that was created more than `ttl_days` days ago (strictly older; a record exactly `ttl_days` old stays) and returns `{"removed": <count>}`.

- `store.all()` returns the records (dicts with `id`, `kind` and a naive-UTC `created_at` datetime); `store.delete(ids)` deletes the given ids in one call. If nothing has expired, `delete` must not be called and `{"removed": 0}` is returned.
- `ttl_days` must be a positive `int`; anything else makes the job fail with an exception.
- `store.delete` can fail transiently by raising `jobs.errors.StoreUnavailable`. The deletion should be attempted up to 3 times in total; if all attempts fail, the last `StoreUnavailable` propagates.

Run from workspace root: `uv run -q --no-project --with pytest python -m pytest -q tests/`
Do not commit. Return changed files, test results and anything unverified.
