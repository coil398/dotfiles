PLANS = {
    "basic": {"price": 9.99, "seats": 1},
    "pro": {"price": 29.0, "seats": 3},
    "team": {"price": 49.5, "seats": 10},
}


def price_of(name):
    return PLANS[name]["price"]


def seats_of(name):
    if name not in PLANS:
        raise ValueError("unknown plan: %s" % name)
    return PLANS[name]["seats"]
