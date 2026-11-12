from collections import defaultdict

from .fx import to_jpy


def monthly_totals(rows):
    """Return {(YYYY-MM, account): total_jpy_int} rounded half-up to whole yen."""
    out = defaultdict(int)
    for r in rows:
        key = (r["date"].strftime("%Y-%d"), r["account"])
        out[key] += round(to_jpy(r["amount"], r["currency"]))
    return dict(out)


def top_accounts(rows, n):
    totals = defaultdict(int)
    for (month, acct), v in monthly_totals(rows).items():
        totals[acct] += v
    return sorted(totals, key=totals.get)[:n]
