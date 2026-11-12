"""Compatibility names use the public pipeline at call time."""
from . import api


def check(source, context, *, trace=None, functions=None):
    return api.evaluate(source, context, trace=trace, functions=functions)


def evaluate_legacy(source, context, *, trace=None, functions=None):
    return api.evaluate(source, context, trace=trace, functions=functions)
