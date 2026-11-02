#!/bin/sh
case "$1" in
    claude|codex|cursor|devin|grok) runtime="$1" ;;
    *) printf '{}'; exit 0 ;;
esac
if [ "${JEV_HOOKS_MODE:-}" = off ]; then
    printf '{}'
    exit 0
fi

# The launcher doctor intentionally runs without a key so it can report the
# source that this entrypoint can access. Normal hooks still skip without one.
doctor_mode=false
if [ "$runtime" = codex ] && [ "${2:-}" = --doctor ]; then
    doctor_mode=true
fi

has_api_key=false
case "${TYPESAFE_API_KEY:-}" in
    *[![:space:]]*) has_api_key=true ;;
esac
if [ "$has_api_key" != true ] && [ "$runtime" = codex ] && [ "$(uname -s 2>/dev/null)" = Darwin ]; then
    launchd_api_key=$(launchctl getenv TYPESAFE_API_KEY 2>/dev/null || true)
    case "$launchd_api_key" in
        *[![:space:]]*)
        export TYPESAFE_API_KEY="$launchd_api_key"
        export JEV_HOOKS_API_KEY_SOURCE=launchd
        has_api_key=true
        ;;
    esac
fi

if [ "$has_api_key" != true ] && [ "$doctor_mode" != true ]; then
    printf '{}'
    exit 0
fi

hook_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || { printf '{}'; exit 0; }
if [ "$doctor_mode" = true ]; then
    script="$hook_dir/jev.py"
    set -- doctor
else
    script="$hook_dir/$runtime-hook.py"
    shift
fi
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
out=$(python3 "$script" "$@")
rc=$?
[ "$rc" -eq 0 ] || fail_open "$rc"
printf '%s' "$out"
