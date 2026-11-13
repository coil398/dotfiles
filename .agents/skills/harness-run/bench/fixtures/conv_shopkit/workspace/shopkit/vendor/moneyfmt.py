# moneyfmt 0.4.1 - vendored, do not edit
def format_cents(cents, symbol="$"):
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return "%s%s%d.%d" % (sign, symbol, cents // 100, cents % 100)
