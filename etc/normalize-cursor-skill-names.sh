#!/usr/bin/env bash
# Normalize Cursor overlay skill slash names to cursor-<dirname>.
# Usage:
#   bash etc/normalize-cursor-skill-names.sh                 # all .cursor/skills/*/SKILL.md
#   bash etc/normalize-cursor-skill-names.sh PATH DIRNAME    # one SKILL.md (seed hook)
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
skill_dirs = sorted(p.name for p in skills_root.iterdir() if p.is_dir())
if dirname not in skill_dirs:
    skill_dirs = sorted(set(skill_dirs) | {dirname})

text = skill_md.read_text(encoding="utf-8")
if not text.startswith("---"):
    raise SystemExit(f"no frontmatter: {skill_md}")
end = text.find("\n---", 3)
if end < 0:
    raise SystemExit(f"bad frontmatter: {skill_md}")
fm = text[4:end]
body = text[end + 4 :]

new_name = f"cursor-{dirname}"
if not re.search(r"^name:\s*", fm, re.M):
    raise SystemExit(f"no name: {skill_md}")
fm2 = re.sub(r"^name:\s*.*$", f'name: "{new_name}"', fm, count=1, flags=re.M)

def rewrite_slashes(s: str) -> str:
    out = s
    for sd in skill_dirs:
        out = re.sub(rf"(?<![\w./-])/{re.escape(sd)}(?![\w-])", f"/cursor-{sd}", out)
    return out

fm2 = "\n".join(
    rewrite_slashes(line) if line.startswith("description:") else line
    for line in fm2.splitlines()
)
body2 = rewrite_slashes(body)
new_text = f"---\n{fm2}\n---{body2}"
if new_text != text:
    skill_md.write_text(new_text, encoding="utf-8")
    print(f"normalized {skill_md} -> {new_name}")
else:
    print(f"ok {skill_md} ({new_name})")
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
  skill_md="${d}SKILL.md"
  if [ -f "$skill_md" ]; then
    normalize_one "$skill_md" "$name"
  fi
done
