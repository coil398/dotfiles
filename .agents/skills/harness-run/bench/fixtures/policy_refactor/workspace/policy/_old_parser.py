"""Legacy bytecode compiler used by the old source-only evaluator.

The public pipeline has a value-tree API. This compiler instead patches jump
addresses while consuming tokens and has no public AST representation.
"""
from ._old_lexer import tokenize

_BINDING = {'or': 1, 'and': 2, '==': 4, '!=': 4, '<': 4,
            '<=': 4, '>': 4, '>=': 4, 'in': 4, 'contains': 4}
_RESERVED = {'not', 'and', 'or', 'in', 'contains'}


class Compiler:
    def __init__(self, source):
        self.stream = tokenize(source)
        self.cursor = 0
        self.code = []

    def current(self):
        return self.stream[self.cursor]

    def advance(self):
        token = self.current()
        self.cursor += 1
        return token

    def symbol(self, spelling):
        kind, value, offset = self.current()
        return kind in ('word', 'symbol') and value == spelling

    def expect(self, spelling):
        if not self.symbol(spelling):
            raise SyntaxError(f'expected {spelling!r} at {self.current()[2]}')
        self.advance()

    def emit(self, opcode, argument=None):
        self.code.append((opcode, argument))
        return len(self.code) - 1

    def expression(self, minimum=0):
        kind, value, offset = self.advance()
        if kind == 'value':
            self.emit('PUSH', value)
        elif kind == 'word' and value == 'not' and minimum <= 3:
            self.expression(3)
            self.emit('NOT')
        elif kind == 'symbol' and value == '(':
            self.expression()
            self.expect(')')
        elif kind == 'word' and value not in _RESERVED:
            if self.symbol('('):
                self.advance()
                self.emit('RESOLVE', value)
                argc = 0
                if not self.symbol(')'):
                    while True:
                        self.expression()
                        argc += 1
                        if self.symbol(')'):
                            break
                        self.expect(',')
                self.expect(')')
                self.emit('INVOKE', (value, argc))
            else:
                self.emit('LOAD', value)
        else:
            raise SyntaxError(f'expected expression at {offset}')
        compared = False
        while True:
            kind, operator, offset = self.current()
            if kind not in ('word', 'symbol'):
                break
            power = _BINDING.get(operator, -1)
            if power < minimum:
                break
            self.advance()
            if power == 4:
                if compared:
                    raise SyntaxError(f'chained comparison at {offset}')
                compared = True
            if operator in ('and', 'or'):
                branch = self.emit('KEEP_FALSE' if operator == 'and' else 'KEEP_TRUE')
                self.expression(power + 1)
                self.code[branch] = (self.code[branch][0], len(self.code))
            else:
                self.expression(power + 1)
                self.emit('COMPARE', operator)

    def compile(self):
        self.expression()
        if self.current()[0] != 'end':
            raise SyntaxError(f'unexpected token at {self.current()[2]}')
        return tuple(self.code)


def parse(source):
    return Compiler(source).compile()
