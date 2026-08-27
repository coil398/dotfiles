#!/usr/bin/env bash
# Normalize Cursor overlay skills so:
#   - directory is <source-name>/  (same basename as .agents/skills; no cursor- prefix)
#   - frontmatter name matches directory (Cursor requires this)
#   - slash triggers use /<source-name>
#   - path refs use .cursor/skills/<source-name>/
#
# .cursor/skills takes precedence over .claude/skills and .agents/skills, so a
# shared basename is intentional and does not need a cursor- namespace.
#
# Usage:
#   bash etc/normalize-cursor-skill-names.sh
#   bash etc/normalize-cursor-skill-names.sh PATH DIRNAME
#     DIRNAME must be the overlay dir basename (e.g. epic)
set -euo pipefail

SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd -P "${SCRIPT_DIR}/.." && pwd)"
SKILLS_ROOT="${DOT_DIR}/.cursor/skills"

normalize_one() {
  local skill_md="$1"
  local dirname="$2"
  python3 - "$skill_md" "$dirname" "$SKILLS_ROOT" <<'PY'
import re
import sys
from pathlib import Path

skill_md = Path(sys.argv[1])
dirname = sys.argv[2]
skills_root = Path(sys.argv[3])

if dirname.startswith("cursor-"):
    raise SystemExit(
        f"dirname must be unprefixed (no cursor-): got {dirname}"
    )

skill_dirs = sorted(
    p.name
    for p in skills_root.iterdir()
    if p.is_dir() and not p.name.startswith(".")
)
if dirname not in skill_dirs:
    skill_dirs = sorted(set(skill_dirs) | {dirname})

# Reject leftover cursor-* dirs
legacy = [d for d in skill_dirs if d.startswith("cursor-")]
if legacy:
    raise SystemExit(f"legacy cursor-* skill dirs remain: {legacy}")

bases = sorted(skill_dirs, key=len, reverse=True)

text = skill_md.read_text(encoding="utf-8")
if not text.startswith("---"):
    raise SystemExit(f"no frontmatter: {skill_md}")
end = text.find("\n---", 3)
if end < 0:
    raise SystemExit(f"bad frontmatter: {skill_md}")
fm = text[4:end]
body = text[end + 4 :]

# Cursor docs: name must match parent folder name
fm2 = re.sub(r"^name:\s*.*$", f'name: "{dirname}"', fm, count=1, flags=re.M)

def rewrite(s: str) -> str:
    out = s
    # Paths: .cursor/skills/cursor-<base> -> .cursor/skills/<base>
    for base in bases:
        out = re.sub(
            rf"\.cursor/skills/cursor-({re.escape(base)})(?=/|[\"'`\s]|$)",
            rf".cursor/skills/\1",
            out,
        )
        out = re.sub(
            rf"~/\.cursor/skills/cursor-({re.escape(base)})(?=/|[\"'`\s]|$)",
            rf"~/.cursor/skills/\1",
            out,
        )
    # Slash: /cursor-<base> -> /<base>
    for base in bases:
        out = re.sub(
            rf"(?<![\w./-])/cursor-{re.escape(base)}(?![\w-])",
            f"/{base}",
            out,
        )
    return out

fm2 = "\n".join(
    rewrite(line) if line.startswith("description:") else line
    for line in fm2.splitlines()
)
body2 = rewrite(body)
new_text = f"---\n{fm2}\n---{body2}"
if new_text != text:
    skill_md.write_text(new_text, encoding="utf-8")
    print(f"normalized {skill_md} -> {dirname}")
else:
    print(f"ok {skill_md} ({dirname})")
PY
}

if [ "$#" -eq 2 ]; then
  normalize_one "$1" "$2"
  exit 0
fi

if [ "$#" -ne 0 ]; then
  echo "usage: $0 [SKILL.md dirname]" >&2
  exit 2
fi

shopt -s nullglob
for d in "${SKILLS_ROOT}"/*/; do
  name="$(basename "$d")"
  case "$name" in
    cursor-*)
      echo "error: legacy cursor-* dir remains: $name" >&2
      exit 1
      ;;
  esac
  skill_md="${d}SKILL.md"
  if [ -f "$skill_md" ]; then
    normalize_one "$skill_md" "$name"
  fi
done
