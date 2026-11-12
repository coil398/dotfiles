from .fx import RATES
import csv
from datetime import datetime
from decimal import Decimal


def parse_rows(text):
    """Parse CSV with header: date,account,amount,currency."""
    rows = []
    for rec in csv.DictReader(text.splitlines()):
        if rec["currency"] not in RATES:
            raise ValueError(rec["currency"])
        rows.append({
            "date": datetime.strptime(rec["date"], "%Y-%m-%d").date(),
            "account": rec["account"],
            "amount": Decimal(rec["amount"].strip()),
            "currency": rec["currency"],
        })
    return rows
