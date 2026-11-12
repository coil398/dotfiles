import argparse
import json
from .loader import load


def load_cli(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--set", action="append", default=[])
    try:
        args = parser.parse_args(argv)
        overrides = {}
        for assignment in args.set:
            if "=" not in assignment:
                raise ValueError(f"--set requires dotted.path=JSON_VALUE: {assignment!r}")
            dotted, encoded = assignment.split("=", 1)
            parts = dotted.split(".")
            if any(not p for p in parts):
                raise ValueError(f"invalid dotted path: {dotted!r}")
            value = json.loads(encoded)
            cursor = overrides
            for part in parts[:-1]:
                if not isinstance(cursor.get(part), dict):
                    cursor[part] = {}
                cursor = cursor[part]
            cursor[parts[-1]] = value
    except SystemExit as exc:
        raise ValueError("invalid command line") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in --set: {exc}") from exc
    return load(args.config, overrides=overrides)
