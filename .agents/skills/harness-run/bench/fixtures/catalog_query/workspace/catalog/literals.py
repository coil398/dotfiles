import re

NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")


def literal(token):
    if token.kind == 'STRING':
        return token.text
    text = token.text
    return None if text.casefold() == 'null' else text
