Project rules for this change (from the repository's AGENTS.md):
- Raise only subclasses of `billing.errors.AppError` from billing code: `InvalidInputError` for bad arguments, `NotFoundError` for unknown entities, `ConflictError` for clashes with existing state. Never raise builtin `ValueError`/`KeyError`/`Exception`.
- Get loggers via `billing.log.get_logger(__name__)`; no `logging.getLogger`, no `print()`. Log user-visible actions such as refunds at INFO.
- Money is always integer cents, never `float`; name money keys with a `_cents` suffix (e.g. `amount_cents`); round down with `//`.
- Add one line under `## Unreleased` at the top of `CHANGELOG.md` (create the heading if missing): `- <feat|fix|chore>(billing): <summary>`, summary lowercase, no trailing period. Do not edit released entries.
- Do not edit existing tests.
