import os

from shopkit.vendor.moneyfmt import format_cents


def discounted_price_cents(product):
    cap = int(os.environ.get("SHOPKIT_MAX_DISCOUNT_PCT", "30"))
    pct = min(product.get("discount_pct", 0), cap)
    return product["price_cents"] * (100 - pct) // 100


def display_price(product):
    return format_cents(discounted_price_cents(product))
