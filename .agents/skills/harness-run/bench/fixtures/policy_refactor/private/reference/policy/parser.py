"""Recursive descent parser; parsing never executes user expressions."""
from .lexer import tokenize
from .model import Node

_COMPARISONS = {"==", "!=", "<", "<=", ">", ">=", "in", "contains"}
_RESERVED = {"not", "and", "or", "in", "contains"}


class Parser:
    def __init__(self, tokens):
        self.tokens = tuple(tokens)
        self.position = 0

    def peek(self):
        return self.tokens[self.position]

    def take(self):
        token = self.peek()
        self.position += 1
        return token

    def accept(self, value):
        token = self.peek()
        if token.kind in ("ident", "op") and token.value == value:
            return self.take()
        return None

    def need(self, value):
        if self.accept(value) is None:
            raise SyntaxError(f"expected {value!r} at {self.peek().offset}")

    def parse(self):
        tree = self.logic_or()
        if self.peek().kind != "eof":
            raise SyntaxError(f"unexpected token at {self.peek().offset}")
        return tree

    def logic_or(self):
        left = self.logic_and()
        while self.accept("or"):
            left = Node("binary", "or", (left, self.logic_and()))
        return left

    def logic_and(self):
        left = self.negation()
        while self.accept("and"):
            left = Node("binary", "and", (left, self.negation()))
        return left

    def negation(self):
        if self.accept("not"):
            return Node("unary", "not", (self.negation(),))
        return self.comparison()

    def comparison(self):
        left = self.atom()
        token = self.peek()
        if token.kind in ("ident", "op") and token.value in _COMPARISONS:
            operator = self.take().value
            left = Node("binary", operator, (left, self.atom()))
        return left

    def atom(self):
        token = self.peek()
        if token.kind == "literal":
            self.take()
            return Node("literal", token.value)
        if self.accept("("):
            tree = self.logic_or()
            self.need(")")
            return tree
        if token.kind == "ident" and token.value not in _RESERVED:
            self.take()
            if not self.accept("("):
                return Node("name", token.value)
            args = []
            if not self.accept(")"):
                while True:
                    args.append(self.logic_or())
                    if self.accept(")"):
                        break
                    self.need(",")
            return Node("call", token.value, tuple(args))
        raise SyntaxError(f"expected expression at {token.offset}")


def parse(source_or_tokens):
    tokens = tokenize(source_or_tokens) if isinstance(source_or_tokens, str) else source_or_tokens
    return Parser(tokens).parse()
