# A single replacement for execute: explicit ordered backtracking, with no state
# merging. Semantics are preserved but ambiguous failures enumerate parse paths.
def execute(program, text, full):
    code, entry, groups, guard_count = program
    starts = [0] if full else range(len(text) + 1)
    for start in starts:
        stack = [(entry, start, (-1,) * (2*(groups+1)), (-1,) * guard_count)]
        while stack:
            pc, pos, tags, marks = stack.pop()
            inst = code[pc]
            op = inst[0]
            if op == 'match':
                if not full or pos == len(text):
                    return tuple(zip(tags[::2], tags[1::2]))
            elif op == 'char':
                if pos < len(text) and accepts(inst[1], text[pos]):
                    stack.append((inst[2], pos+1, tags, marks))
            elif op == 'split':
                stack.append((inst[2], pos, tags, marks))
                stack.append((inst[1], pos, tags, marks))
            elif op == 'save':
                slots = list(tags); slots[inst[1]] = pos
                stack.append((inst[2], pos, tuple(slots), marks))
            elif op == 'mark':
                slots = list(marks); slots[inst[1]] = pos
                stack.append((inst[2], pos, tags, tuple(slots)))
            elif op == 'progress':
                target = inst[3] if marks[inst[1]] == pos else inst[2]
                stack.append((target, pos, tags, marks))
    return None
