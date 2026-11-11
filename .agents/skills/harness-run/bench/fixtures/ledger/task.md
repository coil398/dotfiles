Repository: the current working directory (a small Python package `ledger/` with tests in `tests/`).
Goal: make every test in tests/test_ledger.py pass by changing only files under ledger/. Do not edit tests.
Behavior required (read the tests for exact details): amounts are parsed as Decimal with surrounding whitespace trimmed; an unknown currency raises ValueError mentioning the currency code at parse time; monthly totals are keyed by YYYY-MM and account, summed in exact Decimal JPY per (month, account) and only then rounded half-up to an int; top_accounts returns accounts by total descending, ties broken by account name ascending.
Run `uv run -q --no-project --with pytest python -m pytest -q` from the repository root to confirm. Do not commit.
Return: changed files, the test command result, and anything unverified.
