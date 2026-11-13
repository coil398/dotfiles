Project rules for this change (from the repository's AGENTS.md):
- `shopkit/generated/` is generated from `schema/fields.json`; never edit it by hand. To change a field, edit `schema/fields.json` and run `python tools/gen_fields.py` from the repository root.
- `shopkit/vendor/` is frozen: do not modify, add or delete files there. Wrap or work around vendored code from modules outside `vendor/`.
- Read settings only via `shopkit.config.get(key, default)` with a lowercase key (e.g. `config.get("max_discount_pct", 30)`); never use `os.environ`/`os.getenv` outside `shopkit/config.py`. Values may be strings; convert where used.
- In new modules every public function needs full type annotations and a Google-style docstring (one-line summary ending with a period, `Args:` when it has parameters, `Returns:`).
- Do not edit existing tests.
