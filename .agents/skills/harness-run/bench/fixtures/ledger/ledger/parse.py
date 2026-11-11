import csv
from datetime import datetime
from decimal import Decimal


def parse_rows(text):
    """Parse CSV with header: date,account,amount,currency."""
    rows = []
    for rec in csv.DictReader(text.splitlines()):
        rows.append({
            "date": datetime.strptime(rec["date"], "%Y-%m-%d").date(),
            "account": rec["account"],
            "amount": float(rec["amount"]),
            "currency": rec["currency"],
        })
    return rows
