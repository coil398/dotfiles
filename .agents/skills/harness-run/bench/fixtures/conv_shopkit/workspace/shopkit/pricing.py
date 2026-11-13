import os


def tax_rate():
    return float(os.environ.get("SHOPKIT_TAX_RATE", "0.2"))


def with_tax(cents):
    return int(cents * (1 + tax_rate()))
