# TOMLKit batch editing

The package is TOMLKit 0.15.2 (MIT; see LICENSE). Its parser, item types and serializer are complete. Implement the exported batch API in tomlkit/batch.py, integrating with existing modules as needed.

- tomlkit/api.py: constructors, parse/dumps
- tomlkit/toml_document.py: document container
- tomlkit/container.py: ordered entries, table fragments, rendering
- tomlkit/items.py: keys, trivia, tables, arrays and arrays of tables
- tomlkit/parser.py: TOML parser
- docs/SPEC.md: batch API and preservation requirements

Python 3.11+; runtime uses stdlib only; tests use pytest.
