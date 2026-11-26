#!/usr/bin/env bash
# sync-pstack-runtimes.sh が Codex と Grok の plugin コマンドを冪等に呼ぶかを、偽 CLI の隔離 fixture で確認する。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC="${SCRIPT_DIR}/sync-pstack-runtimes.sh"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/sync-pstack-runtimes.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

fail=0
pass=0
ok() { echo "PASS: $*"; pass=$((pass + 1)); }
bad() { echo "FAIL: $*" >&2; fail=$((fail + 1)); }

# 偽 CLI は呼び出しを $CALLS へ追記し、状態を $STATE_DIR のファイルで持つ。
make_fakes() {
  local bin="$1"
  mkdir -p "$bin"
  cat >"$bin/codex" <<'FAKE'
#!/bin/sh
echo "codex $*" >>"$CALLS"
case "$*" in
  "plugin marketplace list")
    echo "MARKETPLACE     ROOT"
    [ -f "$STATE_DIR/codex-marketplace" ] && echo "cursor-plugins  /fake/root"
    exit 0 ;;
  "plugin marketplace add "*) touch "$STATE_DIR/codex-marketplace" ;;
  "plugin marketplace upgrade "*) [ -z "${FAIL_CODEX_UPGRADE:-}" ] || exit 1 ;;
  "plugin add "*) touch "$STATE_DIR/codex-plugin" ;;
esac
exit 0
FAKE
  cat >"$bin/grok" <<'FAKE'
#!/bin/sh
echo "grok $*" >>"$CALLS"
case "$*" in
  "plugin list")
    [ -f "$STATE_DIR/grok-plugin" ] && echo "  plugins-pstack-d54b5880: pstack [git: https://github.com/cursor/plugins]"
    exit 0 ;;
  "plugin install "*) touch "$STATE_DIR/grok-plugin" ;;
esac
exit 0
FAKE
  chmod 755 "$bin/codex" "$bin/grok"
}

run_sync() {
  CALLS="$WORK/calls.log" STATE_DIR="$WORK/state" PATH="$WORK/bin:$PATH" sh "$SYNC" >"$WORK/out.log" 2>&1
}

make_fakes "$WORK/bin"
mkdir -p "$WORK/state"
: >"$WORK/calls.log"

if run_sync; then ok "first run exits 0"; else bad "first run exits 0"; fi
for expected in \
  "codex plugin marketplace add cursor/plugins" \
  "codex plugin add pstack@cursor-plugins" \
  "grok plugin install cursor/plugins#pstack --trust"; do
  if grep -Fxq "$expected" "$WORK/calls.log"; then ok "first run calls: $expected"; else bad "first run calls: $expected"; fi
done

: >"$WORK/calls.log"
if run_sync; then ok "second run exits 0"; else bad "second run exits 0"; fi
for expected in \
  "codex plugin marketplace upgrade cursor-plugins" \
  "codex plugin add pstack@cursor-plugins" \
  "grok plugin update pstack"; do
  if grep -Fxq "$expected" "$WORK/calls.log"; then ok "second run calls: $expected"; else bad "second run calls: $expected"; fi
done
for unexpected in "codex plugin marketplace add cursor/plugins" "grok plugin install cursor/plugins#pstack --trust"; do
  if grep -Fxq "$unexpected" "$WORK/calls.log"; then bad "second run does not repeat: $unexpected"; else ok "second run does not repeat: $unexpected"; fi
done

: >"$WORK/calls.log"
if FAIL_CODEX_UPGRADE=1 run_sync && grep -q 'upgrade_failed' "$WORK/out.log"; then
  ok "failed upgrade is logged and non-fatal"
else
  bad "failed upgrade is logged and non-fatal"
fi

# CLI が無い環境では何も呼ばず exit 0。
EMPTY_BIN="$WORK/empty-bin"
mkdir -p "$EMPTY_BIN"
for tool in sh timeout env grep printf; do
  tool_path="$(command -v "$tool")"
  ln -s "$tool_path" "$EMPTY_BIN/$tool"
done
if PATH="$EMPTY_BIN" "$EMPTY_BIN/sh" "$SYNC" >"$WORK/none.log" 2>&1 \
  && grep -q 'codex skip reason=codex_unavailable' "$WORK/none.log" \
  && grep -q 'grok skip reason=grok_unavailable' "$WORK/none.log"; then
  ok "missing CLIs are skipped"
else
  bad "missing CLIs are skipped"
fi

echo "pass=${pass} fail=${fail}"
[ "$fail" -eq 0 ]
