Repository: the current working directory, containing the Python package sync_replay/.
Goal: repair checkpointed event synchronization to satisfy docs/NOTES.md, including
replay, failures, durable resume, and the public APIs. Read the complete spec.
Allowed paths: sync_replay/ and docs/NOTES.md only. Do not edit tests.
Run the public tests from the working directory:
`uv run -q --no-project --with pytest python -m pytest -q tests`
Do not commit.
Return: changed files, the test command result, and anything unverified.
