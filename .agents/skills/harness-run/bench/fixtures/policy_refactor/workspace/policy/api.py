"""Public composition boundary for parsing, compilation and evaluation."""
from .parser import parse
from .evaluator import evaluate_tree
from .model import CompiledPolicy


def evaluate(source_or_ast, context, *, trace=None, functions=None):
    if isinstance(source_or_ast, str):
        tree = parse(source_or_ast)
    elif isinstance(source_or_ast, CompiledPolicy):
        tree = parse(source_or_ast.source)
    else:
        tree = source_or_ast
    return evaluate_tree(tree, context, trace, functions)


def compile_policy(source):
    return CompiledPolicy(source, parse(source))


def check(source, context, *, trace=None, functions=None):
    return evaluate(source, context, trace=trace, functions=functions)


def evaluate_legacy(source, context, *, trace=None, functions=None):
    return evaluate(source, context, trace=trace, functions=functions)
