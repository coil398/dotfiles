#!/bin/sh
# PIR² 系スキル（/pir2, /pir2async, /debug）共通の preflight。
#
# 役割:
#   1. ensure-pir-permissions.sh を呼んで .claude/settings.local.json に additionalDirectories を追加
#   2. sanitized_cwd / PROJECT_MEMORY_DIR / PROJECT_ROOT を決定
#   3. run_ts / run_feature から RUN_DIR を決定・作成
#   4. HANDOFF_PATH と RESUME_MODE を決定（"引継い"/"続き"/"resume"/"handoff"/"carry on" 含む場合 resume）
#   5. 上記すべてを KEY=VALUE 形式で標準出力に echo
#
# 引数:
#   $1 = ARGUMENTS（タスク説明。run_feature 生成と RESUME_MODE 判定に使う）
#
# 単一 Bash 呼び出しに凝縮することで Claude Code の permission prompt を回避する狙い。
# 本スクリプトは `~/.claude/settings.json` の allow list で `Bash(sh ~/.claude/lib/pir-preflight.sh *)`
# として登録されている前提。

set -eu

ARGUMENTS="${1:-}"

# 1. ensure-pir-permissions
sh "${HOME}/.claude/lib/ensure-pir-permissions.sh"

# 2. プロジェクトメモリパス
sanitized_cwd="$(pwd | sed 's|/|-|g')"
PROJECT_MEMORY_DIR="${HOME}/.claude/projects/${sanitized_cwd}/memory"
PROJECT_ROOT="$(pwd)"

# 3. RUN_DIR
run_ts="$(date +%Y%m%d-%H%M%S)"
run_feature="$(printf '%s' "${ARGUMENTS}" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
[ -z "${run_feature}" ] && run_feature="task"
RUN_DIR="${HOME}/.ai-pir-runs/${sanitized_cwd}/${run_ts}-${run_feature}"
mkdir -p "${RUN_DIR}"

# 4. HANDOFF_PATH / RESUME_MODE
HANDOFF_PATH="${HOME}/.ai-pir-runs/${sanitized_cwd}/handoff.md"
case "${ARGUMENTS}" in
  *引継い*|*続き*|*resume*|*Resume*|*RESUME*|*handoff*|*Handoff*|*HANDOFF*|*"carry on"*)
    RESUME_MODE="resume" ;;
  *)
    if [ -f "${HANDOFF_PATH}" ]; then
      RESUME_MODE="passive-notice"
    else
      RESUME_MODE="new"
    fi ;;
esac

# 5. KEY=VALUE 出力
echo "PROJECT_MEMORY_DIR=${PROJECT_MEMORY_DIR}"
echo "PROJECT_ROOT=${PROJECT_ROOT}"
echo "RUN_DIR=${RUN_DIR}"
echo "HANDOFF_PATH=${HANDOFF_PATH}"
echo "RESUME_MODE=${RESUME_MODE}"
