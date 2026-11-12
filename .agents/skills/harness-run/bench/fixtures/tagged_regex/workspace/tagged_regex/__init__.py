"""Public API. Compiler and VM live in engine.py."""
from dataclasses import dataclass
from .parser import parse, ParseError
from .engine import compile_ast, execute


@dataclass(frozen=True)
class Match:
    string: str
    _spans: tuple

    def span(self, group=0):
        if type(group) is not int or not 0 <= group < len(self._spans):
            raise IndexError('no such group')
        return self._spans[group]

    def group(self, group=0):
        start, end = self.span(group)
        return None if start < 0 else self.string[start:end]

    def groups(self, default=None):
        return tuple(default if self.span(i)[0] < 0 else self.group(i)
                     for i in range(1, len(self._spans)))


class Pattern:
    def __init__(self, source):
        self.pattern = source
        ast, self.groups = parse(source)
        self._program = compile_ast(ast, self.groups)

    def _run(self, text, full):
        if not isinstance(text, str):
            raise TypeError('text must be str')
        spans = execute(self._program, text, full)
        return None if spans is None else Match(text, tuple(spans))

    def search(self, text):
        return self._run(text, False)

    def fullmatch(self, text):
        return self._run(text, True)


def compile(pattern):
    return Pattern(pattern)


def search(pattern, text):
    return compile(pattern).search(text)


def fullmatch(pattern, text):
    return compile(pattern).fullmatch(text)
