"""Per-product discounts."""
from shopkit import config
from shopkit.compat import format_price


def discounted_price_cents(product: dict) -> int:
    """Return the product price in cents after the capped discount.

    Args:
        product: Product dict with `price_cents` and optional `discount_pct`.

    Returns:
        The discounted price in whole cents, rounded down.
    """
    cap = int(config.get("max_discount_pct", 30))
    pct = min(product.get("discount_pct", 0), cap)
    return product["price_cents"] * (100 - pct) // 100


def display_price(product: dict) -> str:
    """Return the discounted price formatted for display.

    Args:
        product: Product dict with `price_cents` and optional `discount_pct`.

    Returns:
        The price such as "$12.50".
    """
    return format_price(discounted_price_cents(product))
