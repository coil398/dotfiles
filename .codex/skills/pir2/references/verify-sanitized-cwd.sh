#!/usr/bin/env bash
# verify-sanitized-cwd.sh
#
# Verify the Codex-native PIR² consumers against the sanitized-cwd SSOT.
# CODEX_SKILLS_DIR is resolved from this script's own location, so the
# verifier can be run from an arbitrary application repository.
#
# SSOT: ${CODEX_SKILLS_DIR}/pir2/references/sanitized-cwd.md
#
# 揺れを検出した場合は exit 1 を返す（pre-commit / CI 組み込み可）。
#
# 使い方:
#   bash "${CODEX_SKILLS_DIR}/pir2/references/verify-sanitized-cwd.sh"

set -euo pipefail

SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PIR2_DIR="$(CDPATH='' cd -- "${SCRIPT_DIR}/.." && pwd -P)"
CODEX_SKILLS_DIR="$(CDPATH='' cd -- "${PIR2_DIR}/.." && pwd -P)"
SSOT_PATH="${CODEX_SKILLS_DIR}/pir2/references/sanitized-cwd.md"

EXPECTED_SED_EXPR='s|[^a-zA-Z0-9]|-|g'
SAMPLE_PATH='/home/user/ghq/github.com/org/repo'
EXPECTED_SANITIZED='-home-user-ghq-github-com-org-repo'

SKILL_NAMES=(
  pir2
  pir2async
  debug
  ir
  reviewer
  review-pr
  writing-plan
  refactor-advisor
  retro
)

DEVIATIONS=()
MISSING=()
RESOLVED_COUNT=0
ACTIVE_COUNT=0

if [[ ! -f "$SSOT_PATH" ]]; then
  MISSING+=("$SSOT_PATH")
elif ! grep -Fq "$EXPECTED_SED_EXPR" "$SSOT_PATH"; then
  DEVIATIONS+=("$SSOT_PATH: expected sanitize expression '$EXPECTED_SED_EXPR' not found")
fi

actual_sanitized="$(printf '%s' "$SAMPLE_PATH" | sed "$EXPECTED_SED_EXPR")"
if [[ "$actual_sanitized" != "$EXPECTED_SANITIZED" ]]; then
  DEVIATIONS+=("sanitize behavior: expected '$EXPECTED_SANITIZED', got '$actual_sanitized'")
fi

for skill_name in "${SKILL_NAMES[@]}"; do
  skill_file="${CODEX_SKILLS_DIR}/${skill_name}/SKILL.md"
  if [[ ! -f "$skill_file" ]]; then
    MISSING+=("$skill_file")
    continue
  fi
  RESOLVED_COUNT=$((RESOLVED_COUNT + 1))

  # 実際の sanitizer / メモリパス導出だけを検査し、説明コメントや SSOT
  # パスの固定文字列には依存しない。メモリ導出を行わない skill は対象外とする。
  matched_lines="$(grep -nE '^[[:space:]]*(sanitized_cwd|PROJECT_MEMORY_DIR|memory_dir)[[:space:]]*=.*sed' "$skill_file" || true)"
  [[ -z "$matched_lines" ]] && continue
  ACTIVE_COUNT=$((ACTIVE_COUNT + 1))

  while IFS= read -r matched_line; do
    [[ -z "$matched_line" ]] && continue
    if [[ "$matched_line" != *"$EXPECTED_SED_EXPR"* ]]; then
      DEVIATIONS+=("$skill_file: expected expression '$EXPECTED_SED_EXPR', got: $matched_line")
    fi
  done <<< "$matched_lines"
done

if (( ${#MISSING[@]} > 0 )); then
  echo "NG: ${#MISSING[@]} expected Codex skill path(s) missing"
  for missing_path in "${MISSING[@]}"; do
    echo "  - $missing_path"
  done
fi

if (( ${#DEVIATIONS[@]} > 0 )); then
  echo "NG: ${#DEVIATIONS[@]} Codex sanitized-cwd check(s) failed"
  for deviation in "${DEVIATIONS[@]}"; do
    echo "  - $deviation"
  done
fi

if (( ${#MISSING[@]} > 0 )) || (( ${#DEVIATIONS[@]} > 0 )); then
  exit 1
fi

echo "OK: ${RESOLVED_COUNT} Codex skill paths resolved from CODEX_SKILLS_DIR; ${ACTIVE_COUNT} sanitize consumers use [^a-zA-Z0-9]|-|g"
exit 0
