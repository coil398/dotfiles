#!/usr/bin/env bash
# Run a native permission adapter and fail closed if its interpreter or output
# is unavailable. This script never evaluates or executes tool_input.command.
set -u
SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME="${1:-}"
case "$RUNTIME" in
  codex|claude) fallback='{"hookSpecificOutput":{"hookEventName":"PermissionRequest","decision":{"behavior":"deny","message":"Jev permission hook failed; skip this operation and report it."}}}' ;;
  cursor) fallback='{"permission":"deny","user_message":"Jev permission hook failed; skip this operation and report it.","agent_message":"Jev permission hook failed; skip this operation and report it."}' ;;
  devin) fallback='{"decision":"block","reason":"Jev permission hook failed; skip this operation and report it."}' ;;
  opencode) fallback='{"effect":"deny","message":"Jev permission hook failed; skip this operation and report it."}' ;;
  antigravity) fallback='{"decision":"deny","reason":"Jev permission hook failed; skip this operation and report it."}' ;;
  grok) fallback='{"decision":"deny","reason":"Jev permission hook failed; skip this operation and report it."}' ;;
  *) exit 2 ;;
esac
out=""
if command -v python3 >/dev/null 2>&1 && [ -f "${SCRIPT_DIR}/permission-adapter.py" ]; then
  out=$(python3 "${SCRIPT_DIR}/permission-adapter.py" "$RUNTIME" 2>/dev/null) || out=""
fi
case "$RUNTIME:$out" in
  codex:*'"behavior"'*|claude:*'"behavior"'*|cursor:*'"permission"'*|devin:*'"decision"'*|opencode:*'"effect"'*|antigravity:*'"decision"'*|grok:*'"decision"'*) printf '%s' "$out" ;;
  *) printf '%s' "$fallback" ;;
esac
exit 0
