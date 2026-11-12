"""Legacy stack machine; compilation is complete before execution starts."""
from ._old_operators import compare


def evaluate_tree(program, context, trace=None, functions=None):
    stack = []
    pc = 0
    record = trace if isinstance(trace, list) else None
    functions = {} if functions is None else functions
    while pc < len(program):
        opcode, argument = program[pc]
        pc += 1
        if opcode == 'PUSH':
            stack.append(argument)
        elif opcode == 'LOAD':
            if argument not in context:
                raise NameError(argument)
            value = context[argument]
            if record is not None:
                record.append(('name', argument))
            stack.append(value)
        elif opcode == 'NOT':
            stack.append(not stack.pop())
        elif opcode in ('KEEP_TRUE', 'KEEP_FALSE'):
            keep = bool(stack[-1]) if opcode == 'KEEP_TRUE' else not stack[-1]
            if keep:
                pc = argument
            else:
                stack.pop()
        elif opcode == 'COMPARE':
            right = stack.pop()
            left = stack.pop()
            stack.append(compare(argument, left, right))
        elif opcode == 'RESOLVE':
            if argument not in functions:
                raise NameError(argument)
            stack.append(functions[argument])
        elif opcode == 'INVOKE':
            name, count = argument
            args = stack[-count:] if count else []
            if count:
                del stack[-count:]
            function = stack.pop()
            if record is not None:
                record.append(('call', name))
            stack.append(function(*args))
        else:
            raise ValueError(f'unknown instruction {opcode!r}')
    value = stack.pop()
    if record is not None:
        record.append(('result', value))
    return value
