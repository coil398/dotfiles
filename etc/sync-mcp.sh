#!/usr/bin/env bash
# Sync MCP servers from dotfiles/mcp-servers.json to Claude Code user scope.
#
# SSOT   : $DOTFILES/mcp-servers.json
# Target : ~/.claude.json (managed via `claude mcp` subcommands)
#
# Re-running is idempotent: each server is removed from user scope and re-added
# from the SSOT, so edits to mcp-servers.json propagate on next sync.
#
# NOTE: Servers not present in mcp-servers.json, or marked openCodeOnly:true,
# are automatically removed from Claude Code user scope on each sync. Any
# server registered manually outside of this SSOT will also be removed.
#
# Project-scoped servers (e.g. serena, which depends on ${PWD}) belong in each
# repository's own .mcp.json and are NOT managed here.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/../mcp-servers.json"

if [ ! -f "$CONFIG_FILE" ]; then
  echo "[sync-mcp] error: $CONFIG_FILE not found" >&2
  exit 1
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "[sync-mcp] warn: claude command not found, skip" >&2
  exit 0
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "[sync-mcp] error: jq required" >&2
  exit 1
fi

# Remove orphan / openCodeOnly servers from Claude Code user scope.
# Reads current user-scope servers from ~/.claude.json directly because
# `claude mcp list` does not support a --scope flag.
# - Servers absent from SSOT (mcp-servers.json) are orphans → remove
# - Servers marked openCodeOnly:true are OpenCode-only → remove from Claude Code
ssot_names=$(jq -r '.mcpServers | to_entries | map(select(.value.openCodeOnly != true)) | .[].key' "$CONFIG_FILE" | sort -u)
if [ -f "${HOME}/.claude.json" ]; then
  current_names=$(jq -r '.mcpServers | keys[]' "${HOME}/.claude.json" 2>/dev/null | sort -u || true)
  for n in $current_names; do
    if ! echo "$ssot_names" | grep -qx "$n"; then
      echo "[sync-mcp] removing orphan/openCodeOnly server from Claude Code user scope: $n"
      claude mcp remove "$n" -s user >/dev/null 2>&1 || echo "[sync-mcp] warn: failed to remove $n"
    fi
  done
fi

names=$(jq -r '.mcpServers | to_entries | map(select(.value.openCodeOnly != true)) | .[].key' "$CONFIG_FILE")

for name in $names; do
  server_json=$(jq -c --arg n "$name" '.mcpServers[$n] | del(.type, .url, .claudeCodeOnly, .openCodeOnly)' "$CONFIG_FILE")
  echo "[sync-mcp] $name"
  claude mcp remove "$name" -s user >/dev/null 2>&1 || true
  claude mcp add-json "$name" "$server_json" -s user >/dev/null
done

echo "[sync-mcp] done (user scope)"
