#!/usr/bin/env bash
set -euo pipefail

is_valid_design_repo() {
  local candidate="$1"

  [ -d "$candidate/design-system" ] \
    && [ -f "$candidate/.claude/skills/design-review/SKILL.md" ]
}

print_if_valid() {
  local candidate="$1"

  if [ -n "$candidate" ] && is_valid_design_repo "$candidate"; then
    printf '%s\n' "$candidate"
    return 0
  fi
  return 1
}

print_if_valid_design_candidate() {
  local candidate="$1"
  candidate="${candidate%/}"

  if [ -n "$candidate" ] \
    && [ "${candidate##*/}" = "design" ] \
    && is_valid_design_repo "$candidate"; then
    printf '%s\n' "$candidate"
    return 0
  fi
  return 1
}

if [ -n "${DESIGN_REPO:-}" ] && print_if_valid "$DESIGN_REPO"; then
  exit 0
fi

if command -v ghq >/dev/null 2>&1; then
  while IFS= read -r candidate; do
    [ -n "$candidate" ] || continue
    if print_if_valid_design_candidate "$candidate"; then
      exit 0
    fi
  done < <(ghq list -p 2>/dev/null || true)
fi

home_ghq_root="${HOME:-}/ghq"
if [ -n "${HOME:-}" ] && [ -d "$home_ghq_root" ]; then
  for home_candidate in \
    "$home_ghq_root"/design \
    "$home_ghq_root"/*/design \
    "$home_ghq_root"/*/*/design \
    "$home_ghq_root"/*/*/*/design \
    "$home_ghq_root"/*/*/*/*/design; do
    [ -d "$home_candidate" ] || continue
    if print_if_valid_design_candidate "$home_candidate"; then
      exit 0
    fi
  done
fi

printf '%s\n' 'resolve-design-repo: no valid design repository found; each candidate must be a directory named design containing design-system/ and .claude/skills/design-review/SKILL.md; checked DESIGN_REPO, ghq list -p, and limited-depth design candidates below $HOME/ghq.' >&2
exit 1
