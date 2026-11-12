"""Parser for the documented grammar. AST nodes are immutable tuples."""
class ParseError(ValueError):
    pass


def parse(pattern):
    if not isinstance(pattern, str):
        raise TypeError('pattern must be str')
    return Parser(pattern).parse()


class Parser:
    def __init__(self, source):
        self.s, self.i, self.groups = source, 0, 0

    def parse(self):
        node = self.alternative()
        if self.i != len(self.s):
            raise ParseError('unexpected closing parenthesis')
        return node, self.groups

    def alternative(self):
        nodes = [self.sequence()]
        while self.i < len(self.s) and self.s[self.i] == '|':
            self.i += 1
            nodes.append(self.sequence())
        return ('alt', tuple(nodes)) if len(nodes) > 1 else nodes[0]

    def sequence(self):
        nodes = []
        while self.i < len(self.s) and self.s[self.i] not in ')|':
            node = self.atom()
            if self.i < len(self.s) and self.s[self.i] in '*+?':
                quant = self.s[self.i]
                self.i += 1
                lazy = self.i < len(self.s) and self.s[self.i] == '?'
                self.i += int(lazy)
                node = ('repeat', node, quant, lazy)
                if self.i < len(self.s) and self.s[self.i] in '*+?':
                    raise ParseError('multiple quantifiers')
            nodes.append(node)
        return ('seq', tuple(nodes))

    def escaped(self):
        if self.i == len(self.s):
            raise ParseError('trailing escape')
        c = self.s[self.i]
        self.i += 1
        if c in 'nrt':
            return {'n': '\n', 'r': '\r', 't': '\t'}[c]
        if c.isalnum():
            raise ParseError('unsupported escape')
        return c

    def atom(self):
        c = self.s[self.i]
        self.i += 1
        if c == '(':
            if self.i < len(self.s) and self.s[self.i] == '?':
                raise ParseError('special groups are unsupported')
            self.groups += 1
            group = self.groups
            node = self.alternative()
            if self.i == len(self.s) or self.s[self.i] != ')':
                raise ParseError('unclosed group')
            self.i += 1
            return ('group', group, node)
        if c == '.':
            return ('dot',)
        if c == '\\':
            return ('lit', self.escaped())
        if c == '[':
            negated = self.i < len(self.s) and self.s[self.i] == '^'
            self.i += int(negated)
            ranges = []
            while self.i < len(self.s) and self.s[self.i] != ']':
                a = self.class_char()
                if self.i + 1 < len(self.s) and self.s[self.i] == '-' and self.s[self.i + 1] != ']':
                    self.i += 1
                    b = self.class_char()
                    if ord(a) > ord(b):
                        raise ParseError('reversed range')
                else:
                    b = a
                ranges.append((a, b))
            if not ranges or self.i == len(self.s):
                raise ParseError('empty or unclosed class')
            self.i += 1
            return ('class', negated, tuple(ranges))
        if c in '*+?^${}':
            raise ParseError('unsupported metacharacter')
        return ('lit', c)

    def class_char(self):
        c = self.s[self.i]
        self.i += 1
        return self.escaped() if c == '\\' else c
