from dataclasses import dataclass
from .errors import QueryError
from .fields import valid_field
from .literals import literal
from .tokens import tokenize


@dataclass(frozen=True)
class Query:
    tree: object

    @classmethod
    def parse(cls, text):
        return parse(text)


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0

    def peek(self, kind=None, text=None):
        if self.index == len(self.tokens):
            return False
        token = self.tokens[self.index]
        return (kind is None or token.kind == kind) and (text is None or token.text.upper() == text)

    def take(self):
        if not self.peek():
            raise QueryError('expected operand')
        token = self.tokens[self.index]
        self.index += 1
        return token

    def disjunction(self):
        children = [self.conjunction()]
        while self.peek('BARE', 'OR'):
            self.take()
            children.append(self.conjunction())
        return children[0] if len(children) == 1 else ('OR', tuple(children))

    def conjunction(self):
        children = [self.atom()]
        while self.peek('BARE', 'AND'):
            self.take()
            children.append(self.atom())
        return children[0] if len(children) == 1 else ('AND', tuple(children))

    def atom(self):
        token = self.take()
        if token.kind == '(':
            node = self.disjunction()
            if self.take().kind != ')':
                raise QueryError('expected closing parenthesis')
            return node
        if token.kind != 'BARE' or not valid_field(token.text):
            raise QueryError('expected field')
        op = self.take()
        if op.kind != 'OP':
            raise QueryError('expected comparison operator')
        value = self.take()
        if value.kind not in ('BARE', 'STRING') or (value.kind == 'BARE' and value.text.upper() in ('AND', 'OR')):
            raise QueryError('expected value')
        return ('CMP', token.text, op.text, literal(value))


def parse(text):
    tokens = tokenize(text)
    if not tokens:
        return Query(None)
    parser = Parser(tokens)
    tree = parser.disjunction()
    if parser.peek():
        raise QueryError('unexpected trailing token')
    return Query(tree)
