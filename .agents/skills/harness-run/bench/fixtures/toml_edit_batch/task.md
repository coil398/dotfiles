Repository: a vendored TOMLKit 0.15.2 package in the current working directory.
Implement `tomlkit.apply_edits(document, edits) -> TOMLDocument` as specified in docs/SPEC.md. The batch updates, deletes and renames entries without mutating the input, preserving TOMLKit formatting and comments. Read README.md for the package map. Integrate with the existing parser/container/items; preserve existing APIs.
Allowed changes: tomlkit/ only. Do not edit public tests, docs or license. No external dependencies. Do not commit.
Run from the workspace root: `uv run -q --no-project --with pytest python -m pytest -q tests/`
Return changed files, test results and anything unverified.
