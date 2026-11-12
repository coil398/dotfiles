Repository: current working directory, the tagged_regex Python package.
Implement the regex compiler and VM described by docs/SPEC.md. The parser, AST
and public API are complete; the engine currently supports literal concatenation
only. Preserve that API and integrate through compile_ast and execute. Read
README.md for the file map. Allowed changes: tagged_regex/ only. Do not edit
public tests or docs. Do not delegate regex execution to an existing engine.
Run from workspace root: `uv run -q --no-project --with pytest python -m pytest -q tests/`
Do not commit. Return changed files, test results, and anything unverified.
