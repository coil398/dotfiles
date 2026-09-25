#!/bin/sh
# No key means no Python, filesystem writes, or network work.
case "${TYPESAFE_API_KEY:-}" in
    *[![:space:]]*) ;;
    *) printf '{}'; exit 0 ;;
esac
if [ "${JEV_HOOKS_MODE:-}" = off ]; then
    printf '{}'
    exit 0
fi
case "$1" in
    claude|codex|cursor|devin|grok) runtime="$1" ;;
    *) printf '{}'; exit 0 ;;
esac
hook_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || { printf '{}'; exit 0; }
script="$hook_dir/$runtime-hook.py"
log="${XDG_STATE_HOME:-$HOME/.local/state}/jev-hooks/launcher.log"

# Judgments are returned only as JSON on stdout. A missing script or a failed
# run must not reach the runtime as a non-zero exit: Stop hooks treat exit 2
# (python's "can't open file") as "continue", which loops a running session
# that still points at a renamed or deleted script.
fail_open() {
    mkdir -p "$(dirname -- "$log")" 2>/dev/null
    printf '%s %s rc=%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$runtime" "$1" "$script" >>"$log" 2>/dev/null
    printf '{}'
    exit 0
}

[ -f "$script" ] || fail_open missing
out=$(python3 "$script")
rc=$?
[ "$rc" -eq 0 ] || fail_open "$rc"
printf '%s' "$out"
