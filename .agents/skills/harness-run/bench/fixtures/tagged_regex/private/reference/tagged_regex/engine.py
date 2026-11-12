"""Ordered tagged Thompson machine with progress guards for nullable loops."""
def compile_ast(ast, groups):
    code = [('match',)]
    guards = 0

    def emit(inst):
        code.append(inst)
        return len(code) - 1

    def build(node, tail):
        nonlocal guards
        kind = node[0]
        if kind in ('lit', 'dot', 'class'):
            return emit(('char', node, tail))
        if kind == 'seq':
            for child in reversed(node[1]):
                tail = build(child, tail)
            return tail
        if kind == 'alt':
            heads = [build(child, tail) for child in node[1]]
            head = heads[-1]
            for other in reversed(heads[:-1]):
                head = emit(('split', other, head))
            return head
        if kind == 'group':
            close = emit(('save', 2 * node[1] + 1, tail))
            return emit(('save', 2 * node[1], build(node[2], close)))
        if kind == 'repeat':
            _, child, quant, lazy = node
            if quant == '?':
                head = build(child, tail)
                return emit(('split', tail, head) if lazy else ('split', head, tail))
            guard = guards
            guards += 1
            split = emit(('pending',))
            progress = emit(('progress', guard, split, tail))
            body = emit(('mark', guard, build(child, progress)))
            code[split] = ('split', tail, body) if lazy else ('split', body, tail)
            return body if quant == '+' else split
        raise AssertionError(kind)

    end = emit(('save', 1, 0))
    entry = emit(('save', 0, build(ast, end)))
    return code, entry, groups, guards


def accepts(node, char):
    if node[0] == 'lit':
        return char == node[1]
    if node[0] == 'dot':
        return char != '\n'
    inside = any(a <= char <= b for a, b in node[2])
    return inside != node[1]


def execute(program, text, full):
    code, entry, groups, guard_count = program
    # Each position carries ordered threads. Lower-priority acceptances are
    # fallback candidates until all higher-priority consuming threads fail.
    threads = []
    best = None
    for pos in range(len(text) + 1):
        if not full and best is None or full and pos == 0:
            threads.append((entry, (-1,) * (2 * (groups + 1)), (-1,) * guard_count))
        stack = list(reversed(threads))
        seen = set()
        consuming = []
        while stack:
            pc, tags, marks = stack.pop()
            key = pc, marks
            if key in seen:
                continue
            seen.add(key)
            inst = code[pc]
            op = inst[0]
            if op == 'match':
                if full and pos != len(text):
                    continue
                best = tuple((tags[i], tags[i + 1]) for i in range(0, len(tags), 2))
                break
            if op == 'char':
                consuming.append((pc, tags, marks))
            elif op == 'split':
                stack.append((inst[2], tags, marks))
                stack.append((inst[1], tags, marks))
            elif op == 'save':
                updated = list(tags)
                updated[inst[1]] = pos
                stack.append((inst[2], tuple(updated), marks))
            elif op == 'mark':
                updated = list(marks)
                updated[inst[1]] = pos
                stack.append((inst[2], tags, tuple(updated)))
            elif op == 'progress':
                target = inst[3] if marks[inst[1]] == pos else inst[2]
                stack.append((target, tags, marks))
        if pos == len(text):
            return best
        threads = [(code[pc][2], tags, marks) for pc, tags, marks in consuming
                   if accepts(code[pc][1], text[pos])]
        if best is not None and not threads:
            return best
    return best
