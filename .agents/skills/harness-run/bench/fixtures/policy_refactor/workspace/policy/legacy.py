"""Existing policy entry points, to be migrated to the public pipeline."""
from ._old_parser import parse
from ._old_evaluator import evaluate_tree


def evaluate_legacy(source, context, *, trace=None, functions=None):
    return evaluate_tree(parse(source), context, trace, functions)


def check(source, context, *, trace=None, functions=None):
    return evaluate_legacy(source, context, trace=trace, functions=functions)
