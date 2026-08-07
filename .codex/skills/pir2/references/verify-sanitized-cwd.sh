#!/usr/bin/env bash
# verify-sanitized-cwd.sh
#
# Verify the nine Codex-native PIR² consumers against the sanitized-cwd SSOT.
# The repository root is derived from this script's own path, so the verifier
# can be run from any working directory.
#
# SSOT: ${PROJECT_ROOT}/.codex/skills/pir2/references/sanitized-cwd.md
#
# 揺れを検出した場合は exit 1 を返す（pre-commit / CI 組み込み可）。
#
# 使い方:
#   bash "${PROJECT_ROOT}/.codex/skills/pir2/references/verify-sanitized-cwd.sh"

set -euo pipefail

SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(CDPATH='' cd -- "${SCRIPT_DIR}/../../../.." && pwd -P)"
SSOT_PATH="${PROJECT_ROOT}/.codex/skills/pir2/references/sanitized-cwd.md"

EXPECTED_SED_EXPR='s|[^a-zA-Z0-9]|-|g'
EXPECTED_SSOT_REFERENCE='${PROJECT_ROOT}/.codex/skills/pir2/references/sanitized-cwd.md'

SKILL_FILES=(
  "${PROJECT_ROOT}/.codex/skills/pir2/SKILL.md"
  "${PROJECT_ROOT}/.codex/skills/pir2async/SKILL.md"
  "${PROJECT_ROOT}/.codex/skills/debug/SKILL.md"
  "${PROJECT_ROOT}/.codex/skills/ir/SKILL.md"
  "${PROJECT_ROOT}/.codex/skills/reviewer/SKILL.md"
  "${PROJECT_ROOT}/.codex/skills/review-pr/SKILL.md"
  "${PROJECT_ROOT}/.codex/skills/writing-plan/SKILL.md"
  "${PROJECT_ROOT}/.codex/skills/refactor-advisor/SKILL.md"
  "${PROJECT_ROOT}/.codex/skills/retro/SKILL.md"
)

DEVIATIONS=()
MISSING=()
SSOT_MISSING=false

if [[ ! -f "$SSOT_PATH" ]]; then
  SSOT_MISSING=true
elif ! grep -Fq "$EXPECTED_SED_EXPR" "$SSOT_PATH"; then
  DEVIATIONS+=("$SSOT_PATH: expected sanitize expression '$EXPECTED_SED_EXPR' not found")
fi

for f in "${SKILL_FILES[@]}"; do
  if [[ ! -f "$f" ]]; then
    MISSING+=("$f")
    continue
  fi

  # sanitized_cwd= で始まる行を抽出し、その中に SSOT の sed 式が含まれるかを確認
  matched_line="$(grep -nE 'sanitized_cwd=.*sed' "$f" || true)"
  if [[ -z "$matched_line" ]]; then
    DEVIATIONS+=("$f: no sanitized_cwd line found")
  elif ! grep -Fq "$EXPECTED_SED_EXPR" <<< "$matched_line"; then
    DEVIATIONS+=("$f: expected expression '$EXPECTED_SED_EXPR', got: $matched_line")
  fi

  ssot_lines="$(grep -nF "$EXPECTED_SSOT_REFERENCE" "$f" || true)"
  if [[ -z "$ssot_lines" ]] || ! grep -q 'sanitized-cwd' <<< "$ssot_lines"; then
    DEVIATIONS+=("$f: expected Codex SSOT reference '$EXPECTED_SSOT_REFERENCE' not found")
  fi
done

if [[ "$SSOT_MISSING" == true ]]; then
  echo "NG: SSOT file missing: $SSOT_PATH"
fi

if (( ${#MISSING[@]} > 0 )); then
  echo "NG: ${#MISSING[@]} expected Codex SKILL.md file(s) missing:"
  for m in "${MISSING[@]}"; do
    echo "  - $m"
  done
fi

if (( ${#DEVIATIONS[@]} > 0 )); then
  echo "NG: ${#DEVIATIONS[@]} file(s) deviate from the Codex sanitized-cwd SSOT"
  for d in "${DEVIATIONS[@]}"; do
    echo "  - $d"
  done
fi

if [[ "$SSOT_MISSING" == true ]] || (( ${#MISSING[@]} > 0 )) || (( ${#DEVIATIONS[@]} > 0 )); then
  exit 1
fi

echo "OK: ${#SKILL_FILES[@]} Codex SKILL.md files use the SSOT sanitize expression [^a-zA-Z0-9]|-|g"
exit 0
