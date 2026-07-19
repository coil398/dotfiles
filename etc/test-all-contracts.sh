#!/usr/bin/env bash
# 契約テスト集約ランナー。cursor / codex / shared-drift の 3 契約をまとめて実行する。
#
#   bash etc/test-all-contracts.sh
#
# 実行内容:
#   - test-cursor-contracts.sh : sync-cursor.sh --check（read-only）と seed 非破壊確認を含む
#   - test-codex-contracts.sh  : seed 非破壊確認（非破壊だが純 read-only ではない副作用あり）と、
#                                内部で check-shared-drift.sh を実行する
#
# 二重実行回避: check-shared-drift.sh は test-codex-contracts.sh が内部で実行するため、
# この wrapper では単独起動しない。drift の PASS/FAIL は codex の出力行から抽出して
# 独立行として集計表示する（codex が drift を包含するため overall 判定は cursor+codex のみで行う）。
#
# fail-fast しない: いずれかが FAIL しても残りを実行し、最後に全体集計する。
# 全て PASS で exit 0、1 本でも FAIL なら exit 1。

# NOTE: -e は付けない（fail-fast を避け、失敗した契約も握って続行するため）。
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

codex_log="$(mktemp "${TMPDIR:-/tmp}/all-contracts-codex.XXXXXX")"
trap 'rm -f "$codex_log"' EXIT

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

# --- 2. codex 契約（check-shared-drift.sh を内包） ---
echo "=================================================================="
echo ">>> test-codex-contracts.sh  (seed 非破壊[副作用あり] / drift 内包)"
echo "=================================================================="
if bash "${SCRIPT_DIR}/test-codex-contracts.sh" 2>&1 | tee "$codex_log"; then
  codex_status="PASS"
else
  codex_status="FAIL"
fi
echo

# --- 3. shared-drift（codex 出力から抽出。単独実行はしない = 二重実行回避） ---
# codex は check-shared-drift.sh の成否を自分の集計に
#   PASS: check-shared-drift clean  /  FAIL: check-shared-drift failed
# として出力する。この行だけを抽出して drift を独立表示する。
# 抽出できない場合（codex 側の文言変更等）は UNKNOWN とし、overall には影響させない。
if grep -q '^PASS: check-shared-drift' "$codex_log"; then
  drift_status="PASS"
elif grep -q '^FAIL: check-shared-drift' "$codex_log"; then
  drift_status="FAIL"
else
  drift_status="UNKNOWN"
fi

# --- 集計 ---
echo "=================================================================="
echo " 契約テスト集計"
echo "=================================================================="
printf '  %-8s  %s\n' "$cursor_status" "test-cursor-contracts.sh"
printf '  %-8s  %s\n' "$codex_status" "test-codex-contracts.sh"
printf '  %-8s  %s\n' "$drift_status" "check-shared-drift.sh  (codex 内包 / 単独実行せず)"
echo

# overall は cursor + codex の結果のみで決める（codex が drift を包含するため二重カウントしない）。
if [ "$cursor_status" = "PASS" ] && [ "$codex_status" = "PASS" ]; then
  echo "ALL PASS"
  exit 0
else
  echo "SOME FAILED"
  exit 1
fi
