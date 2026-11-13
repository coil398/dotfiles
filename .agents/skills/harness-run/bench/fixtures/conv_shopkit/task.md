Add optional per-product discounts to the `shopkit` package.

1. Products get an optional integer field `discount_pct` (0 to 100 inclusive). `shopkit.validate.validate_product` must accept products with a valid `discount_pct` and reject any other value (wrong type, below 0, above 100) with `ValueError`, like it does for the other fields.
2. Add a new module `shopkit/discounts.py` with:
   - `discounted_price_cents(product)`: the product's `price_cents` after the discount, rounded down to whole cents. The applied percentage is capped by the shop-wide maximum, which is controlled by the setting `SHOPKIT_MAX_DISCOUNT_PCT` (an integer, default 30): applied percentage = min(`discount_pct`, maximum). A product without `discount_pct` is not discounted.
   - `display_price(product)`: the discounted price as a string with a `$` sign and always two decimals, for example `"$12.50"` or `"$5.05"`. Use the existing price formatting helper of the package.

Run from workspace root: `uv run -q --no-project --with pytest python -m pytest -q tests/`
Do not commit. Return changed files, test results and anything unverified.
