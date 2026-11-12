def topological_order(jobs):
    state, order, stack = {}, [], []

    def visit(name):
        mark = state.get(name, 0)
        if mark == 2:
            return
        if mark == 1:
            start = stack.index(name)
            cycle = stack[start:] + [name]
            raise ValueError("dependency cycle: " + " -> ".join(cycle))
        if name not in jobs:
            raise ValueError(f"unknown dependency {name!r}")
        state[name] = 1
        stack.append(name)
        for dep in sorted(jobs[name].dependencies):
            visit(dep)
        stack.pop()
        state[name] = 2
        order.append(name)

    for name in sorted(jobs):
        visit(name)
    return order
