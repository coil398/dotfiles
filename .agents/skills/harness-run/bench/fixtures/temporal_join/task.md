Repository: the current working directory, a Python streaming join package.
Goal: implement the incremental temporal join described in docs/SPEC.md. Read README.md for the package map. Preserve the documented API and integrate the iterator and stateful entry points.
Allowed changes: temporal_join/ only. Do not edit tests or the public specification.
Run from the workspace root: `uv run -q --no-project --with pytest python -m pytest -q tests`
Do not commit.
Return: changed files, the test command result, and anything unverified.
