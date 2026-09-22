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
    codex|cursor|devin|grok) runtime="$1" ;;
    *) printf '{}'; exit 0 ;;
esac
hook_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 0
exec python3 "$hook_dir/$runtime-hook.py"
