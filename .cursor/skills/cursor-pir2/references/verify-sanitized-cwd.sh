#!/usr/bin/env bash
# verify-sanitized-cwd.sh
#
# PIR² 系 9 SKILL.md の sanitize 正規表現が SSOT と一致していることを検証する。
# SSOT: .cursor/skills/cursor-pir2/references/sanitized-cwd.md
#
# 揺れを検出した場合は exit 1 を返す（pre-commit / CI 組み込み可）。
#
# 使い方:
#   bash .cursor/skills/cursor-pir2/references/verify-sanitized-cwd.sh

set -euo pipefail

EXPECTED_REGEX="\[\^a-zA-Z0-9\]|-|g"

SKILL_FILES=(
  "${HOME}/.claude/skills/pir2/SKILL.md"
  "${HOME}/.claude/skills/pir2async/SKILL.md"
  "${HOME}/.claude/skills/debug/SKILL.md"
  "${HOME}/.claude/skills/ir/SKILL.md"
  "${HOME}/.claude/skills/reviewer/SKILL.md"
  "${HOME}/.claude/skills/review-pr/SKILL.md"
  "${HOME}/.claude/skills/writing-plan/SKILL.md"
  "${HOME}/.claude/skills/refactor-advisor/SKILL.md"
  "${HOME}/.claude/skills/retro/SKILL.md"
)

DEVIATIONS=()
MISSING=()

for f in "${SKILL_FILES[@]}"; do
  if [[ ! -f "$f" ]]; then
    MISSING+=("$f")
    continue
  fi
  # sanitized_cwd= で始まる行を抽出し、その中に EXPECTED_REGEX が含まれるかを確認
  matched_line=$(grep -nE "sanitized_cwd=.*sed" "$f" || true)
  if [[ -z "$matched_line" ]]; then
    DEVIATIONS+=("$f: no sanitized_cwd line found")
    continue
  fi
  if ! echo "$matched_line" | grep -qE "$EXPECTED_REGEX"; then
    DEVIATIONS+=("$f: expected pattern '[^a-zA-Z0-9]|-|g', got: $matched_line")
  fi
done

if (( ${#MISSING[@]} > 0 )); then
  echo "WARNING: ${#MISSING[@]} expected file(s) missing:"
  for m in "${MISSING[@]}"; do
    echo "  - $m"
  done
fi

if (( ${#DEVIATIONS[@]} > 0 )); then
  echo "NG: ${#DEVIATIONS[@]} file(s) deviate from SSOT sanitize regex"
  for d in "${DEVIATIONS[@]}"; do
    echo "  - $d"
  done
  echo ""
  echo "SSOT: .cursor/skills/cursor-pir2/references/sanitized-cwd.md"
  exit 1
fi

if (( ${#MISSING[@]} > 0 )); then
  exit 1
fi

echo "OK: ${#SKILL_FILES[@]} SKILL.md files all use the SSOT sanitize regex [^a-zA-Z0-9]|-|g"
exit 0
