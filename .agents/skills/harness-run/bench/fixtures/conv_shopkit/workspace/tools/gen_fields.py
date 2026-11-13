"""Generate shopkit/generated/fields.py from schema/fields.json.

Usage: python tools/gen_fields.py [--out PATH]
"""
import argparse
import json
import pprint
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "schema" / "fields.json"
DEFAULT_OUT = ROOT / "shopkit" / "generated" / "fields.py"


def render(spec):
    return "FIELDS = " + pprint.pformat(spec, sort_dicts=False, width=100) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    Path(args.out).write_text(render(json.loads(SPEC.read_text())))


if __name__ == "__main__":
    main()
