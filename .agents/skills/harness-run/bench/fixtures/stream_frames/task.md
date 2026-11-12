Repository: the current working directory contains a Python package `framing/`, protocol notes in `docs/NOTES.md`, a failing incident log in `logs/incident.log`, and public tests in `tests/`.
Goal: repair the streaming frame decoder so the public tests pass and its behavior matches `docs/NOTES.md`. Use the incident log to locate the chunk-boundary failure. Change only files under `framing/`. Do not edit tests. The public test command is `uv run -q --no-project --with pytest python -m pytest -q tests`. Do not commit.
Return: changed files, the test command result, and anything unverified.
