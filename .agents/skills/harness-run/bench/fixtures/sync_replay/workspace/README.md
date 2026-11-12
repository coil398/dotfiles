# Replay repair workspace

Read [the behavior specification](docs/NOTES.md), then the package modules.
The in-memory adapters let you reproduce interruptions without external services.
FileCheckpoint and JournalSink exercise the same replay semantics after process
reconstruction. The source, engine and sink are independently replaceable by
objects implementing their small duck-typed protocols.

Run `uv run -q --no-project --with pytest python -m pytest -q tests`.
