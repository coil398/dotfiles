# Catalog

This package stores JSON records and exposes a query API plus `python -m catalog`.
Implement the feature according to [the complete specification](docs/query.md).
The existing modules separate tokenization, parsing, literal conversion, lookup,
matching, sorting, collection ownership, and the JSON command line adapter.
The exported API is `Catalog`, `Query`, `QueryError`, and `parse`.

Run the public tests with:

```sh
uv run -q --no-project --with pytest python -m pytest -q tests
```
