from dataclasses import dataclass

from .graph import topological_order


@dataclass(frozen=True)
class Result:
    makespan: int
    jobs: dict[str, dict[str, int]]


def simulate(jobs, workers, resources=None, backoff=1):
    if workers < 1 or backoff < 0:
        raise ValueError("workers must be positive and backoff nonnegative")
    resources = resources or {}
    order = topological_order(jobs)
    for job in jobs.values():
        for name, count in job.resources.items():
            if count > resources.get(name, 0):
                raise ValueError(f"insufficient resource {name!r} for {job.name!r}")

    now = 0
    free = dict(resources)
    completed, active, attempts, retry_at, first_start, final_end = set(), {}, {}, {}, {}, {}
    while len(completed) < len(jobs):
        for name, run in list(active.items()):
            if run["end"] == now:
                job = jobs[name]
                for key, count in job.resources.items():
                    free[key] += count
                del active[name]
                if run["attempt"] <= job.fail:
                    retry_at[name] = now + backoff
                else:
                    completed.add(name)
                    final_end[name] = now

        ready = [name for name in order if name not in completed and name not in active
                 and retry_at.get(name, 0) <= now and all(d in completed for d in jobs[name].dependencies)]
        ready.sort(key=lambda name: (-jobs[name].priority,
                                    max((final_end[d] for d in jobs[name].dependencies), default=0), name))
        while ready and len(active) < workers:
            name = ready.pop(0)
            job = jobs[name]
            if any(free[key] < count for key, count in job.resources.items()):
                continue
            for key, count in job.resources.items():
                free[key] -= count
            attempt = attempts.get(name, 0) + 1
            attempts[name] = attempt
            first_start.setdefault(name, now)
            active[name] = {"start": now, "end": now + job.duration, "attempt": attempt}

        if len(completed) == len(jobs):
            break
        events = [run["end"] for run in active.values()]
        events += [t for name, t in retry_at.items() if name not in completed and name not in active and t > now]
        if not events:
            raise ValueError("schedule cannot make progress")
        now = min(events)
    return Result(max(final_end.values(), default=0), {
        name: {"start": first_start[name], "end": final_end[name]} for name in sorted(jobs)
    })
