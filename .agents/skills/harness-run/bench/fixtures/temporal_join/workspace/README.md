# temporal_join

Implement a symmetric streaming event-time join using the complete contract in
[docs/SPEC.md](docs/SPEC.md). There are no external package dependencies.

- `model.py`: immutable messages and output records.
- `validation.py`: input boundary checks.
- `index.py`: per-key timestamp range lookup and expiration.
- `metrics.py`: deterministic operation counters.
- `engine.py`: acceptance, emission, watermark and lifecycle transitions.
- `stream.py`: lazy iterator adapter.
- `__init__.py`: public imports.

Public checks: `uv run -q --no-project --with pytest python -m pytest -q tests`.
