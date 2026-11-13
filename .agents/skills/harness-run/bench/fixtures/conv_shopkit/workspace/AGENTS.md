# shopkit - project rules

Storefront helper library. Python 3.11, standard library only.

## Layout

- `schema/fields.json` product field specification
- `tools/gen_fields.py` generator for `shopkit/generated/fields.py`
- `shopkit/generated/` generated modules
- `shopkit/vendor/` third-party code copied in verbatim
- `shopkit/config.py` settings access
- `shopkit/validate.py`, `shopkit/pricing.py`, `shopkit/catalog.py` library code
- `tests/` public tests (maintained by the QA team, do not edit)

## Generated code

- Everything under `shopkit/generated/` is produced from `schema/fields.json`.
  Never edit those files by hand.
- To change a field, edit `schema/fields.json`, then run
  `python tools/gen_fields.py` from the repository root and commit both files.
- The generator output must match the committed generated file byte for byte.

## Vendored code

- `shopkit/vendor/` is frozen. Do not modify, add or delete files there; upstream
  syncs replace the whole directory.
- If vendored code is inadequate, wrap or work around it in code under `shopkit/`
  outside `vendor/`.

## Settings

- Read settings only through `shopkit.config.get(key, default)` with a lowercase
  key (for example `config.get("max_discount_pct", 30)`).
  Never read `os.environ` or call `os.getenv` outside `shopkit/config.py`.
- Values from `config.get` may be strings; convert them where they are used.

## Typing and docstrings (new modules)

- Every public function in a new module has full type annotations (all
  parameters and the return type).
- Every public function has a Google-style docstring: a one-line summary ending
  with a period, an `Args:` section when it takes parameters, and a `Returns:`
  section.
- Private helpers (leading underscore) are exempt.

## Style

- Line length 100, black defaults, one import per line.
- No wildcard imports; no mutable default arguments.
- Product dicts use plain `str` keys; prices are integer cents (`price_cents`).
- Do not add new dependencies.

## Process

- Run `python -m pytest -q tests/` before handing work over.
- Commit messages: imperative mood, subject under 72 columns.
- Pull requests need one reviewer and a green CI run.
