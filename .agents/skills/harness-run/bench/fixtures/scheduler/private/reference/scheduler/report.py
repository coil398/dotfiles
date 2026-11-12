from .graph import topological_order


def build_report(jobs, result):
    order = topological_order(jobs)
    length, predecessor = {}, {}
    for name in order:
        candidates = [(length[dep], dep) for dep in jobs[name].dependencies]
        if candidates:
            best_length = max(value for value, _ in candidates)
            best_dep = min(dep for value, dep in candidates if value == best_length)
            length[name] = best_length + jobs[name].duration
            predecessor[name] = best_dep
        else:
            length[name] = jobs[name].duration
            predecessor[name] = None
    end = min(name for name, value in length.items() if value == max(length.values())) if length else None
    path = []
    while end is not None:
        path.append(end)
        end = predecessor[end]
    path.reverse()
    return {"makespan": result.makespan, "jobs": result.jobs, "critical_path": path}
