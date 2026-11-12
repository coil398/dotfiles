"""Compiler/VM scaffold. The literal-only matcher is intentionally incomplete."""
def compile_ast(ast, groups):
    return ast, groups


def execute(program, text, full):
    ast, groups = program
    def literal(node):
        if node[0] == 'lit':
            return node[1]
        if node[0] == 'seq':
            parts = [literal(child) for child in node[1]]
            if all(part is not None for part in parts):
                return ''.join(parts)
        return None
    word = literal(ast)
    if word is None:
        return None
    start = 0 if full else text.find(word)
    if start < 0 or (full and text != word):
        return None
    return ((start, start + len(word)),) + ((-1, -1),) * groups
