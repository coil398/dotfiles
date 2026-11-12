"""Per-call CDCL with two watched literals and first-UIP learning.

Assumptions are root units in a fresh engine, so learned clauses never escape
an assumption context. Permanent clauses remain immutable in the API.
"""
from collections import defaultdict


def search(clauses, nvars, assumptions):
    database = [list(c) for c in clauses]
    database.extend([a] for a in assumptions)
    watches = defaultdict(list)
    values = [0] * (nvars + 1)
    levels = [0] * (nvars + 1)
    reasons = [-1] * (nvars + 1)
    activity = [0.0] * (nvars + 1)
    phase = [1] * (nvars + 1)
    trail = []
    limits = []
    head = 0
    increment = 1.0

    def value(lit):
        return values[abs(lit)] * (1 if lit > 0 else -1)

    def assign(lit, reason):
        v = abs(lit)
        if values[v]:
            return value(lit) > 0
        values[v] = phase[v] = 1 if lit > 0 else -1
        levels[v] = len(limits)
        reasons[v] = reason
        trail.append(lit)
        return True

    for ci, clause in enumerate(database):
        if not clause:
            return None
        for lit in clause:
            activity[abs(lit)] += 1
        watches[clause[0]].append(ci)
        if len(clause) > 1:
            watches[clause[1]].append(ci)
        elif not assign(clause[0], ci):
            return None

    def propagate():
        nonlocal head
        while head < len(trail):
            false = -trail[head]
            head += 1
            bucket = watches[false]
            i = 0
            while i < len(bucket):
                ci = bucket[i]
                clause = database[ci]
                if len(clause) == 1:
                    if value(clause[0]) < 0:
                        return ci
                    i += 1
                    continue
                if clause[0] == false:
                    clause[0], clause[1] = clause[1], clause[0]
                other = clause[0]
                if value(other) > 0:
                    i += 1
                    continue
                for k in range(2, len(clause)):
                    if value(clause[k]) >= 0:
                        clause[1], clause[k] = clause[k], clause[1]
                        watches[clause[1]].append(ci)
                        bucket[i] = bucket[-1]
                        bucket.pop()
                        break
                else:
                    if value(other) < 0:
                        return ci
                    assign(other, ci)
                    i += 1
        return -1

    while True:
        conflict = propagate()
        if conflict >= 0:
            if not limits:
                return None
            learned = [0]
            seen = set()
            pending = 0
            cursor = len(trail) - 1
            pivot = 0
            clause = database[conflict]
            while True:
                for lit in clause:
                    v = abs(lit)
                    if v == abs(pivot) or v in seen or levels[v] == 0:
                        continue
                    seen.add(v)
                    activity[v] += increment
                    if levels[v] == len(limits):
                        pending += 1
                    else:
                        learned.append(lit)
                while abs(trail[cursor]) not in seen:
                    cursor -= 1
                pivot = trail[cursor]
                cursor -= 1
                pending -= 1
                if pending == 0:
                    learned[0] = -pivot
                    break
                clause = database[reasons[abs(pivot)]]
            if len(learned) > 1:
                best = max(range(1, len(learned)), key=lambda k: levels[abs(learned[k])])
                learned[1], learned[best] = learned[best], learned[1]
                target = levels[abs(learned[1])]
            else:
                target = 0
            cut = limits[target]
            for lit in trail[cut:]:
                values[abs(lit)] = 0
                reasons[abs(lit)] = -1
                levels[abs(lit)] = 0
            del trail[cut:]
            del limits[target:]
            head = len(trail)
            ci = len(database)
            database.append(learned)
            watches[learned[0]].append(ci)
            if len(learned) > 1:
                watches[learned[1]].append(ci)
            assign(learned[0], ci)
            increment *= 1.05
            if increment > 1e100:
                activity[:] = [a * 1e-100 for a in activity]
                increment *= 1e-100
        else:
            candidates = (v for v in range(1, nvars + 1) if not values[v])
            branch = max(candidates, key=activity.__getitem__, default=0)
            if not branch:
                return {v: values[v] > 0 for v in range(1, nvars + 1)}
            limits.append(len(trail))
            assign(branch * phase[branch], -1)
