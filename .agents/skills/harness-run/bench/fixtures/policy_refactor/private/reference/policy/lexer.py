"""Scan policy source into immutable, position-bearing tokens."""
import re
from .model import Token

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_INT = re.compile(r"[0-9]+")
_LITERALS = {"true": True, "false": False, "null": None}
_ESCAPES = {"n": "\n", "r": "\r", "t": "\t"}
_SYMBOLS = ("==", "!=", "<=", ">=", "<", ">", "(", ")", ",")


def tokenize(source):
    if not isinstance(source, str):
        raise TypeError("source must be str")
    tokens = []
    offset = 0
    while offset < len(source):
        char = source[offset]
        if char.isspace():
            offset += 1
            continue
        if char == "#":
            break
        if char in "'\"":
            start = offset
            quote = char
            offset += 1
            decoded = []
            while offset < len(source) and source[offset] != quote:
                char = source[offset]
                if char == "\\":
                    offset += 1
                    if offset == len(source):
                        raise SyntaxError(f"unterminated escape at {start}")
                    char = _ESCAPES.get(source[offset], source[offset])
                decoded.append(char)
                offset += 1
            if offset == len(source):
                raise SyntaxError(f"unterminated string at {start}")
            tokens.append(Token("literal", "".join(decoded), start))
            offset += 1
            continue
        match = _INT.match(source, offset)
        if match:
            tokens.append(Token("literal", int(match.group()), offset))
            offset = match.end()
            continue
        match = _IDENT.match(source, offset)
        if match:
            word = match.group()
            kind = "literal" if word in _LITERALS else "ident"
            tokens.append(Token(kind, _LITERALS.get(word, word), offset))
            offset = match.end()
            continue
        symbol = next((s for s in _SYMBOLS if source.startswith(s, offset)), None)
        if symbol is None:
            raise SyntaxError(f"unexpected character {char!r} at {offset}")
        tokens.append(Token("op", symbol, offset))
        offset += len(symbol)
    tokens.append(Token("eof", None, len(source)))
    return tuple(tokens)
