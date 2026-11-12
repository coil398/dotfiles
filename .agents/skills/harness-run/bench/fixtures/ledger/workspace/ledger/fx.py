from decimal import Decimal

# Units of JPY per 1 unit of currency.
RATES = {"JPY": Decimal("1"), "USD": Decimal("150"), "EUR": Decimal("160")}


def to_jpy(amount, currency):
    return amount * RATES[currency]
