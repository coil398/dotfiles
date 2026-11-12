# tagged_regex

`tagged_regex/parser.py` builds immutable AST tuples and numbers captures.
`tagged_regex/__init__.py` provides Pattern, Match and convenience entry points.
`tagged_regex/engine.py` owns compilation and execution; implement these there.
`docs/SPEC.md` specifies syntax, choice order, capture history and scale.
`tests/` contains public examples; the grader adds private semantic and scale cases.

Run: `uv run -q --no-project --with pytest python -m pytest -q tests/`
