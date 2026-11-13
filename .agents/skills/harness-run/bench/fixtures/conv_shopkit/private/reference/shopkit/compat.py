"""Workarounds for the vendored helpers."""


def format_price(cents: int) -> str:
    """Format integer cents as a dollar string with two decimals.

    Args:
        cents: Non-negative amount in cents.

    Returns:
        The amount such as "$12.50".
    """
    return "$%d.%02d" % (cents // 100, cents % 100)
