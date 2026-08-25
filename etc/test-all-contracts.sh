#!/usr/bin/env bash
# 契約テスト集約ランナー。cursor / shared-drift / codex-motitan の契約をまとめて実行する。
#
#   bash etc/test-all-contracts.sh
#
# 実行内容:
#   - test-cursor-contracts.sh : sync-cursor.sh --check（read-only）と seed 非破壊確認を含む
#   - check-shared-drift.sh    : runtime 間の shared drift を確認する
#   - test-codex-motitan-contract.sh : motitan 専用 Codex profile / launcher / link を確認する
#
# fail-fast しない: いずれかが FAIL しても残りを実行し、最後に全体集計する。
# 全て PASS で exit 0、1 本でも FAIL なら exit 1。

# NOTE: -e は付けない（fail-fast を避け、失敗した契約も握って続行するため）。
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

# --- 2. shared-drift ---
echo "=================================================================="
echo ">>> check-shared-drift.sh"
echo "=================================================================="
if bash "${SCRIPT_DIR}/check-shared-drift.sh"; then
  drift_status="PASS"
else
  drift_status="FAIL"
fi
echo

# --- 3. codex-motitan 契約 ---
echo "=================================================================="
echo ">>> test-codex-motitan-contract.sh"
echo "=================================================================="
if bash "${SCRIPT_DIR}/test-codex-motitan-contract.sh"; then
  motitan_status="PASS"
else
  motitan_status="FAIL"
fi
echo

# --- 集計 ---
echo "=================================================================="
echo " 契約テスト集計"
echo "=================================================================="
printf '  %-8s  %s\n' "$cursor_status" "test-cursor-contracts.sh"
printf '  %-8s  %s\n' "$drift_status" "check-shared-drift.sh"
printf '  %-8s  %s\n' "$motitan_status" "test-codex-motitan-contract.sh"
echo

if [ "$cursor_status" = "PASS" ] && [ "$drift_status" = "PASS" ] && [ "$motitan_status" = "PASS" ]; then
  echo "ALL PASS"
  exit 0
else
  echo "SOME FAILED"
  exit 1
fi
