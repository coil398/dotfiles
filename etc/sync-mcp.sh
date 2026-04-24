#!/usr/bin/env bash
# Sync MCP servers from dotfiles/mcp-servers.json to Claude Code user scope.
#
# SSOT   : $DOTFILES/mcp-servers.json
# Target : ~/.claude.json (managed via `claude mcp` subcommands)
#
# Re-running is idempotent: each server is removed from user scope and re-added
# from the SSOT, so edits to mcp-servers.json propagate on next sync.
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

names=$(jq -r '.mcpServers | keys[]' "$CONFIG_FILE")

for name in $names; do
  server_json=$(jq -c --arg n "$name" '.mcpServers[$n]' "$CONFIG_FILE")
  echo "[sync-mcp] $name"
  claude mcp remove "$name" -s user >/dev/null 2>&1 || true
  claude mcp add-json "$name" "$server_json" -s user >/dev/null
done

echo "[sync-mcp] done (user scope)"
