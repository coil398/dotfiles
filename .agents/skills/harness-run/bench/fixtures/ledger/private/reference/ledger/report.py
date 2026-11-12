from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from .fx import to_jpy


def monthly_totals(rows):
    """Return {(YYYY-MM, account): total_jpy_int} rounded half-up to whole yen."""
    out = defaultdict(Decimal)
    for r in rows:
        key = (r["date"].strftime("%Y-%m"), r["account"])
        out[key] += to_jpy(r["amount"], r["currency"])
    return {k: int(v.quantize(Decimal("1"), rounding=ROUND_HALF_UP)) for k, v in out.items()}


def top_accounts(rows, n):
    totals = defaultdict(int)
    for (month, acct), v in monthly_totals(rows).items():
        totals[acct] += v
    return sorted(totals, key=lambda a: (-totals[a], a))[:n]
