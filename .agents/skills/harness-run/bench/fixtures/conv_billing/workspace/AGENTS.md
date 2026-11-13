# billing - project rules

Small internal billing library. Python 3.11, standard library only.

## Layout

- `billing/plans.py` plan catalog
- `billing/subscriptions.py` subscription lifecycle helpers
- `billing/invoices.py` invoice totals
- `billing/errors.py` project exception types
- `billing/log.py` logger factory
- `tests/` public tests (maintained by the QA team, do not edit)

## Code style

- Line length 100, formatted with black defaults.
- Imports: stdlib, then `billing.*`, one import per line, no wildcard imports.
- Dates are `datetime.date`, never ISO strings, inside the package.
- Identifiers (subscription ids, plan names) are plain `str`.
- Keep functions short; prefer early returns over nested `if`.
- SQL, if ever added, must use parameterized queries.

## Errors

- Code under `billing/` must raise subclasses of `billing.errors.AppError`
  (`InvalidInputError`, `NotFoundError`, `ConflictError`). Never raise builtin
  `ValueError`, `KeyError` or `Exception` from billing code.
- Use `InvalidInputError` for bad arguments, `NotFoundError` for unknown
  entities and `ConflictError` for operations that clash with existing state.

## Logging

- Obtain loggers with `billing.log.get_logger(__name__)`; do not call
  `logging.getLogger` directly and do not use `print()` in package code.
- User-visible actions (cancellations, refunds, ...) are logged at INFO.
- DEBUG is for developer diagnostics only and must not carry customer data.

## Money

- Money is always an integer number of cents. Never use `float` for money.
- Name money fields and keys with a `_cents` suffix (for example `amount_cents`).
- Divide with `//` (round down) unless a spec says otherwise.

## Changelog

- Every user-visible change adds one line under `## Unreleased` at the top of
  `CHANGELOG.md` (create the heading if it is missing).
- Format: `- <type>(<scope>): <summary>` where type is `feat`, `fix` or `chore`,
  scope is the package name (`billing`), and the summary starts lowercase and has
  no trailing period.
- Do not edit entries of already released versions.

## Testing and review

- Run `python -m pytest -q tests/` before handing work over.
- Do not weaken or edit existing tests.
- Commits use imperative mood, 72 columns for the subject.
- Pull requests need one reviewer and a green CI run.
- New third-party dependencies need explicit approval.
