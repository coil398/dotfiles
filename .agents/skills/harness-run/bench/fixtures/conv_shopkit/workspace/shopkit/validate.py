from shopkit.generated.fields import FIELDS

_TYPES = {"str": str, "int": int}


def validate_product(product):
    spec = FIELDS["product"]
    for name in product:
        if name not in spec:
            raise ValueError("unknown field: %s" % name)
    for name, rule in spec.items():
        if name not in product:
            if rule.get("required"):
                raise ValueError("missing field: %s" % name)
            continue
        value = product[name]
        if not isinstance(value, _TYPES[rule["type"]]) or isinstance(value, bool):
            raise ValueError("bad type for %s" % name)
        if "min" in rule and value < rule["min"]:
            raise ValueError("%s below minimum" % name)
        if "max" in rule and value > rule["max"]:
            raise ValueError("%s above maximum" % name)
    return product
