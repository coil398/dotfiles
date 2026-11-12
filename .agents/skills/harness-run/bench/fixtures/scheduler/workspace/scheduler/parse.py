from dataclasses import dataclass


@dataclass(frozen=True)
class Job:
    name: str
    duration: int
    priority: int
    resources: dict[str, int]
    dependencies: tuple[str, ...]
    fail: int = 0


def parse_jobs(text):
    jobs = {}
    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        name, fields = parts[0], {}
        if name in jobs:
            raise ValueError(f"duplicate job {name!r} on line {line_no}")
        for part in parts[1:]:
            if "=" not in part:
                raise ValueError(f"invalid field {part!r} on line {line_no}")
            key, value = part.split("=", 1)
            if key in fields:
                raise ValueError(f"duplicate field {key!r} on line {line_no}")
            fields[key] = value
        try:
            duration = int(fields["duration"])
            priority = int(fields["priority"])
            fail = int(fields.get("fail", "0"))
            resource_text = fields.get("resources", "-")
            dep_text = fields.get("depends", "-")
            resources = {} if resource_text == "-" else {
                name: int(count) for name, count in (item.split(":", 1) for item in resource_text.split(","))
            }
            dependencies = () if dep_text == "-" else tuple(dep_text.split(","))
        except (KeyError, ValueError) as exc:
            raise ValueError(f"invalid job on line {line_no}: {exc}") from exc
        if duration <= 0 or fail < 0 or any(count <= 0 for count in resources.values()):
            raise ValueError(f"invalid nonpositive value on line {line_no}")
        if not name or priority < 0:
            raise ValueError(f"invalid job on line {line_no}")
        jobs[name] = Job(name, duration, priority, resources, dependencies, fail)
    return jobs
