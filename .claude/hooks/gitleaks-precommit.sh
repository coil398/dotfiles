#!/usr/bin/env bash
# gitleaks-precommit
#
# git commit 実行前に staged 差分を gitleaks でスキャンし、秘密情報が
# 検出された場合はコミットをブロックする。
#
# Hook 配置: PreToolUse, matcher=Bash, if=Bash(git commit *)
# 入力:     stdin に Hook input JSON
# 出力:     OK なら exit 0、検出時 exit 2 (= block + reason を stderr で model に提示)

set -uo pipefail

# gitleaks 未インストール時は静かにスキップ（環境差分でコミットが詰まらないように）
if ! command -v gitleaks >/dev/null 2>&1; then
  echo "[gitleaks-precommit] gitleaks not installed; skipping secret scan" >&2
  exit 0
fi

# 入力 JSON を読むが、本フックは command 文字列を見ず、cwd の git レポジトリを直接スキャンする。
# (settings.json の `if: "Bash(git commit *)"` で既にコマンドフィルタ済み)
cat >/dev/null

# git リポジトリ外（init 前など）ならスキップ
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  exit 0
fi

# staged 差分が空ならスキップ（--allow-empty な amend など）
if git diff --cached --quiet; then
  exit 0
fi

# staged 差分をスキャン (--redact で値をマスク。-v で File/Line/RuleID を表示)
if gitleaks git --staged --redact --no-banner -v; then
  exit 0
fi

# 検出 → blocking error
cat >&2 <<'MSG'

❌ gitleaks detected potential secrets in staged changes.
   Findings above are redacted (values masked); rule names and line numbers are shown.

How to proceed:
  1) Edit the file to remove the secret (do NOT commit the value)
  2) git restore --staged <file>   if you want to unstage the whole file
  3) Add a .gitleaksignore entry only if confirmed false positive
MSG
exit 2
