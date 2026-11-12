"""Execute an already parsed tree without retaining evaluation state."""
from .operators import compare


def evaluate_tree(tree, context, trace=None, functions=None):
    functions = {} if functions is None else functions
    trace = trace if isinstance(trace, list) else None

    def visit(node):
        if node.kind == "literal":
            return node.value
        if node.kind == "name":
            if node.value not in context:
                raise NameError(node.value)
            value = context[node.value]
            if trace is not None:
                trace.append(("name", node.value))
            return value
        if node.kind == "unary":
            return not visit(node.children[0])
        if node.kind == "binary":
            left = visit(node.children[0])
            if node.value == "and":
                return visit(node.children[1]) if left else left
            if node.value == "or":
                return left if left else visit(node.children[1])
            right = visit(node.children[1])
            return compare(node.value, left, right)
        if node.kind == "call":
            if node.value not in functions:
                raise NameError(node.value)
            function = functions[node.value]
            args = [visit(child) for child in node.children]
            if trace is not None:
                trace.append(("call", node.value))
            return function(*args)
        raise ValueError(f"unknown node {node.kind!r}")

    value = visit(tree)
    if trace is not None:
        trace.append(("result", value))
    return value
