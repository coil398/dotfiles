#!/usr/bin/env bash
# verify-sanitized-cwd.sh
#
# 現在の共有 skill consumer が sanitize 正規表現の SSOT と一致することを検証する。
# SSOT: このスクリプトと同じ共有 skill package の references/sanitized-cwd.md
#
# 揺れを検出した場合は exit 1 を返す（pre-commit / CI 組み込み可）。
#
# 使い方:
#   bash path/to/.agents/skills/pir2/references/verify-sanitized-cwd.sh

set -euo pipefail

EXPECTED_TEXT='[^a-zA-Z0-9]|-|g'

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SHARED_SKILLS_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd -P)"
SANITIZE_REFERENCE="${SHARED_SKILLS_ROOT}/pir2/references/sanitized-cwd.md"

if [[ ! -f "${SANITIZE_REFERENCE}" ]]; then
  echo "NG: sanitize SSOT is missing: ${SANITIZE_REFERENCE}"
  exit 1
fi

# 現行 consumer は、共有 SKILL.md に sanitize の実行契約が記載されているものだけを検出する。
# 固定された runtime path や過去の consumer 一覧は検査対象にしない。
SKILL_FILES=()
while IFS= read -r -d '' f; do
  if grep -qE "sanitized_cwd=.*sed" "${f}"; then
    SKILL_FILES+=("${f}")
  fi
done < <(find "${SHARED_SKILLS_ROOT}" -type f -name SKILL.md -print0 | sort -z)

if (( ${#SKILL_FILES[@]} == 0 )); then
  echo "INFO: 0 current sanitize consumer(s) discovered under ${SHARED_SKILLS_ROOT}; no consumer was validated"
  exit 0
fi

DEVIATIONS=()
MISSING=()

for f in "${SKILL_FILES[@]}"; do
  if [[ ! -f "$f" ]]; then
    MISSING+=("$f")
    continue
  fi
  # sanitized_cwd= で始まる行を抽出し、その中に SSOT の式が含まれるかを確認
  matched_line=$(grep -nE "sanitized_cwd=.*sed" "$f" || true)
  if [[ -z "$matched_line" ]]; then
    DEVIATIONS+=("$f: no sanitized_cwd line found")
    continue
  fi
  if ! echo "$matched_line" | grep -qF "$EXPECTED_TEXT"; then
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
  echo "SSOT: ${SANITIZE_REFERENCE}"
  exit 1
fi

if (( ${#MISSING[@]} > 0 )); then
  exit 1
fi

echo "OK: ${#SKILL_FILES[@]} current sanitize consumer(s) all use the SSOT sanitize regex [^a-zA-Z0-9]|-|g"
exit 0
