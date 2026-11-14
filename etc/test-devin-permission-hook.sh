#!/usr/bin/env bash
# Verify Devin PermissionRequest hook generation preserves user hooks and is idempotent.
set -euo pipefail

SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd -P "${SCRIPT_DIR}/.." && pwd)"
ROOT="$(mktemp -d "${TMPDIR:-/tmp}/devin-permission-hook.XXXXXX")"
trap 'rm -rf "$ROOT"' EXIT
HOME_FIXTURE="${ROOT}/home"
CONFIG="${HOME_FIXTURE}/.config/devin/config.json"
mkdir -p "$(dirname "$CONFIG")"
cat > "$CONFIG" <<'JSON'
{
  "custom_setting": "keep",
  "hooks": {
    "PermissionRequest": [
      {"matcher": "exec", "hooks": [{"type": "command", "command": "custom-policy"}]}
    ]
  }
}
JSON

HOME="$HOME_FIXTURE" bash "${SCRIPT_DIR}/sync-devin.sh"
jq -e '.custom_setting == "keep" and any(.hooks.PermissionRequest[]?.hooks[]?; .command == "custom-policy")' "$CONFIG" >/dev/null
[ "$(jq '[.hooks.PermissionRequest[]?.hooks[]? | select(.command | contains("permission-launcher.sh devin"))] | length' "$CONFIG")" -eq 1 ]

HOME="$HOME_FIXTURE" bash "${SCRIPT_DIR}/sync-devin.sh"
[ "$(jq '[.hooks.PermissionRequest[]?.hooks[]? | select(.command | contains("permission-launcher.sh devin"))] | length' "$CONFIG")" -eq 1 ]
echo "Devin PermissionRequest hook: pass"
