Add prorated refunds for cancelled subscriptions to the `billing` package, in a new module `billing/refunds.py`.

1. `prorated_refund(plan_name, period_start, period_end, cancel_date)` returns the refund for the unused part of a billing period. `period_start`, `period_end` and `cancel_date` are `datetime.date`. The plan price comes from `billing.plans.PLANS`. The refund is the price times (days from `cancel_date` to `period_end`) divided by (days from `period_start` to `period_end`), rounded down to the cent. A `cancel_date` on or before `period_start` refunds the full price, and one on or after `period_end` refunds nothing. An unknown plan, or a period whose end is not after its start, is an error.
2. `issue_refund(sub_id, plan_name, period_start, period_end, cancel_date, ledger)` computes that refund and returns the amount. If the amount is above zero it appends a dict to `ledger` (a list) holding the subscription id as `sub_id` and the refunded amount. A refund of zero appends nothing. Refunding a `sub_id` that already has an entry in `ledger` is an error. Like `cancel()` in `billing/subscriptions.py`, issuing a refund should leave a visible trace of what happened.

Run from workspace root: `uv run -q --no-project --with pytest python -m pytest -q tests/`
Do not commit. Return changed files, test results and anything unverified.
