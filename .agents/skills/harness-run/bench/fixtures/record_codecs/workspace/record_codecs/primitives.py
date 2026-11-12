"""Complete conversion primitives for valid non-null values."""
def text_encode(value):
    return value

def text_decode(value):
    return value

def decimal_encode(value):
    return str(value)

def decimal_decode(value):
    return int(value)

def boolean_encode(value, tokens):
    return tokens[0] if value else tokens[1]

def boolean_decode(value, tokens):
    return value == tokens[0]

def enum_encode(value, mapping):
    return mapping[value]

def enum_decode(value, mapping):
    return {wire: source for source, wire in mapping.items()}[value]

def scale_encode(value, multiplier):
    return value * multiplier

def scale_decode(value, multiplier):
    return value // multiplier

def strings_encode(value):
    return list(value)

def strings_decode(value):
    return list(value)
