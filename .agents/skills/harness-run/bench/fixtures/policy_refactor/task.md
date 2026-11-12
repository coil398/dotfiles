Repository: the current working directory contains `policy/`, `docs/`, and `tests/`.

Goal: refactor the policy evaluator into a public tokenize → parse → evaluate API, while preserving the behavior specified in `docs/NOTES.md` and keeping the legacy entry points wired through that API. Change only `policy/` and `docs/NOTES.md`. Do not edit tests.

Run `uv run -q --no-project --with pytest python -m pytest -q tests` from the repository root. Do not commit.

Return: changed files, the test command result, and anything unverified.
