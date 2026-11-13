def line_total(price, qty):
    if qty < 0:
        raise ValueError("negative quantity")
    return round(price * qty, 2)


def invoice_total(items):
    total = 0.0
    for price, qty in items:
        total += line_total(price, qty)
    print("invoice total: %.2f" % total)
    return round(total, 2)
