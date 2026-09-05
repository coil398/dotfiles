#!/usr/bin/env bash
# 契約テスト集約ランナー。既定では runtime adapter の軽量な契約を実行し、
# --full 指定時は private fixture の Codex/autosync/worker/LTM 検証も追加する。
#
#   bash etc/test-all-contracts.sh [--full]
#
# 実行内容:
#   - test-cursor-contracts.sh       : sync-cursor.sh --check（read-only）と seed 非破壊確認を含む
#   - test-opencode-contracts.sh     : sync-opencode.sh --check、冪等性、agent 変換、孤児削除を含む
#   - check-shared-drift.sh          : runtime 間の shared drift を確認する
#   - test-codex-motitan-contract.sh : motitan 専用 Codex profile / launcher / link を確認する
# --full の追加対象:
#   - test-codex-config.sh           : Codex config generator の隔離 fixture
#   - test-dotfiles-autosync.sh      : autosync engine の隔離 Git fixture
#   - test-auto-gate.py              : Antigravity PreToolUse gate の 7 fixture tests
#   - test_mutable_paths.sh          : worker runner の隔離 fixture
#   - test_record_observation_routing.sh: worker observation routing の隔離 fixture
#   - .agents/skills/ai-ltm/tests/test_vector_search.py          : shared LTM vector search の隔離 fixture
#   - .agents/skills/ai-ltm/tests/test_vector_search_readonly.py : shared LTM read-only vector search の隔離 fixture
#   - .agents/skills/ai-ltm/tests/test_sync_memory.py            : shared LTM sync-memory の隔離 fixture
#   - .codex/skills/ai-ltm/tests/test_session_recall.py           : Codex LTM session recall の隔離 fixture
#   - .codex/skills/ai-ltm/tests/test_vector_search_readonly.py   : Codex LTM read-only vector search の隔離 fixture
#   - .cursor/skills/ai-ltm/tests/test_vector_search_readonly.py  : Cursor LTM read-only vector search の隔離 fixture
#   - .agents/skills/check-updates/tests/test_check_updates.py    : runtime 別更新対象と Git 保全の隔離 fixture
#
# fail-fast しない: いずれかが FAIL しても残りを実行し、最後に全体集計する。
# 全て PASS で exit 0、1 本でも FAIL なら exit 1。

# NOTE: -e は付けない（fail-fast を避け、失敗した契約も握って続行するため）。
set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FULL=0
for arg in "$@"; do
  case "$arg" in
    --full) FULL=1 ;;
    -h|--help)
      sed -n '2,24p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

# --- 1. cursor 契約 ---
echo "=================================================================="
echo ">>> test-cursor-contracts.sh  (sync-cursor --check / seed 非破壊)"
echo "=================================================================="
if bash "${SCRIPT_DIR}/test-cursor-contracts.sh"; then
  cursor_status="PASS"
else
  cursor_status="FAIL"
fi
echo

# --- 2. opencode 契約 ---
echo "=================================================================="
echo ">>> test-opencode-contracts.sh  (sync-opencode --check / 冪等性 / 孤児削除)"
echo "=================================================================="
if bash "${SCRIPT_DIR}/test-opencode-contracts.sh"; then
  opencode_status="PASS"
else
  opencode_status="FAIL"
fi
echo

# --- 3. shared-drift ---
echo "=================================================================="
echo ">>> check-shared-drift.sh"
echo "=================================================================="
if bash "${SCRIPT_DIR}/check-shared-drift.sh"; then
  drift_status="PASS"
else
  drift_status="FAIL"
fi
echo

# --- 4. codex-motitan 契約 ---
echo "=================================================================="
echo ">>> test-codex-motitan-contract.sh"
echo "=================================================================="
if bash "${SCRIPT_DIR}/test-codex-motitan-contract.sh"; then
  motitan_status="PASS"
else
  motitan_status="FAIL"
fi
echo

# --- 5. antigravity 契約 ---
echo "=================================================================="
echo ">>> test-antigravity-contracts.sh"
echo "=================================================================="
if bash "${SCRIPT_DIR}/test-antigravity-contracts.sh"; then
  antigravity_status="PASS"
else
  antigravity_status="FAIL"
fi
echo

full_status="NOT_RUN"
full_fail=0
run_full_target() {
  local label="$1"
  shift
  echo "=================================================================="
  echo ">>> ${label}"
  echo "=================================================================="
  if "$@"; then
    echo "${label}: PASS"
  else
    echo "${label}: FAIL"
    full_fail=1
  fi
  echo
}

if [ "$FULL" = "1" ]; then
  full_status="PASS"
  run_full_target "test-codex-config.sh (private fixture)" bash "${SCRIPT_DIR}/test-codex-config.sh"
  run_full_target "test-dotfiles-autosync.sh (private fixture)" bash "${SCRIPT_DIR}/test-dotfiles-autosync.sh"
  run_full_target "test-auto-gate.py (private fixture)" env PYTHONDONTWRITEBYTECODE=1 python3 "${SCRIPT_DIR}/test-auto-gate.py"
  run_full_target "worker-delegation/tests/test_mutable_paths.sh" bash "${SCRIPT_DIR}/../.codex/skills/worker-delegation/tests/test_mutable_paths.sh"
  run_full_target "worker-delegation/tests/test_record_observation_routing.sh" bash "${SCRIPT_DIR}/../.codex/skills/worker-delegation/tests/test_record_observation_routing.sh"
  run_full_target ".agents/skills/ai-ltm/tests/test_vector_search.py" python3 "${SCRIPT_DIR}/../.agents/skills/ai-ltm/tests/test_vector_search.py"
  run_full_target ".agents/skills/ai-ltm/tests/test_vector_search_readonly.py" python3 "${SCRIPT_DIR}/../.agents/skills/ai-ltm/tests/test_vector_search_readonly.py"
  run_full_target ".agents/skills/ai-ltm/tests/test_sync_memory.py" python3 "${SCRIPT_DIR}/../.agents/skills/ai-ltm/tests/test_sync_memory.py"
  run_full_target ".codex/skills/ai-ltm/tests/test_session_recall.py" python3 "${SCRIPT_DIR}/../.codex/skills/ai-ltm/tests/test_session_recall.py"
  run_full_target ".codex/skills/ai-ltm/tests/test_vector_search_readonly.py" python3 "${SCRIPT_DIR}/../.codex/skills/ai-ltm/tests/test_vector_search_readonly.py"
  run_full_target ".cursor/skills/ai-ltm/tests/test_vector_search_readonly.py" python3 "${SCRIPT_DIR}/../.cursor/skills/ai-ltm/tests/test_vector_search_readonly.py"
  run_full_target ".agents/skills/check-updates/tests/test_check_updates.py" python3 "${SCRIPT_DIR}/../.agents/skills/check-updates/tests/test_check_updates.py"
  [ "$full_fail" -eq 0 ] || full_status="FAIL"
fi

# --- 集計 ---
echo "=================================================================="
echo " 契約テスト集計"
echo "=================================================================="
printf '  %-8s  %s\n' "$cursor_status" "test-cursor-contracts.sh"
printf '  %-8s  %s\n' "$opencode_status" "test-opencode-contracts.sh"
printf '  %-8s  %s\n' "$drift_status" "check-shared-drift.sh"
printf '  %-8s  %s\n' "$motitan_status" "test-codex-motitan-contract.sh"
printf '  %-8s  %s\n' "$antigravity_status" "test-antigravity-contracts.sh"
if [ "$FULL" = "1" ]; then
  printf '  %-8s  %s\n' "$full_status" "--full private fixture suite"
else
  printf '  %-8s  %s\n' "$full_status" "--full private fixture suite (not run)"
fi
echo

if [ "$cursor_status" = "PASS" ] && [ "$opencode_status" = "PASS" ] && [ "$drift_status" = "PASS" ] && [ "$motitan_status" = "PASS" ] && [ "$antigravity_status" = "PASS" ] && [ "$full_status" != "FAIL" ]; then
  echo "ALL PASS"
  exit 0
else
  echo "SOME FAILED"
  exit 1
fi
