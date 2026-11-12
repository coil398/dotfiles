import re

NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")


def literal(token):
    if token.kind == 'STRING':
        return token.text
    text = token.text
    lower = text.casefold()
    if lower == 'null':
        return None
    if lower in ('true', 'false'):
        return lower == 'true'
    if NUMBER.fullmatch(text):
        return float(text) if any(c in text for c in '.eE') else int(text)
    return text
