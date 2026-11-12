from dataclasses import dataclass
from .errors import QueryError


@dataclass(frozen=True)
class Token:
    kind: str
    text: str
    position: int


def tokenize(text):
    if not isinstance(text, str):
        raise QueryError('query must be text')
    tokens = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        start = i
        if ch in '()':
            tokens.append(Token(ch, ch, i))
            i += 1
        elif ch in ':=!<>':
            i += 1
            if i < len(text) and text[i] == '=' and ch in '!<>':
                i += 1
            op = text[start:i]
            if op == '!':
                raise QueryError(f'invalid operator at {start}')
            tokens.append(Token('OP', op, start))
        elif ch in "\"'":
            quote = ch
            i += 1
            chars = []
            while i < len(text) and text[i] != quote:
                if text[i] == '\\':
                    i += 1
                    if i == len(text) or text[i] not in "\\\"'":
                        raise QueryError(f'invalid escape at {i}')
                chars.append(text[i])
                i += 1
            if i == len(text):
                raise QueryError(f'unterminated quote at {start}')
            i += 1
            tokens.append(Token('STRING', ''.join(chars), start))
        else:
            while i < len(text) and not text[i].isspace() and text[i] not in "():=!<>\"'":
                i += 1
            tokens.append(Token('BARE', text[start:i], start))
    return tokens
