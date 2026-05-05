#!/usr/bin/env bash
# Claude Code PostToolUse hook for Codex SSOT sync.
#
# Triggered after Edit/Write/MultiEdit. Runs etc/sync-codex.sh only if the
# edited file is one of the Codex SSOT files:
#   - dotfiles/mcp-servers.json
#   - dotfiles/.codex/config.base.toml
#   - dotfiles/.claude/CLAUDE.md
#   - dotfiles/.claude/format.md
#   - dotfiles/.claude/pir-handoff.md
#   - dotfiles/.claude/agents/*.md
#   - dotfiles/.claude/skills/**
#
# Other edits are ignored (early exit). Failures are non-blocking.

set -euo pipefail

SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd -P "${SCRIPT_DIR}/../.." && pwd)"
SYNC_SCRIPT="${DOT_DIR}/etc/sync-codex.sh"

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

input=$(cat)

file_path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
[ -z "$file_path" ] && exit 0

case "$file_path" in
  /*) abs="$file_path" ;;
  ~*) abs="${file_path/#\~/$HOME}" ;;
  *)  abs="$(pwd)/$file_path" ;;
esac

abs_dir="$(dirname "$abs")"
abs_base="$(basename "$abs")"
if [ -d "$abs_dir" ]; then
  abs="$(cd -P "$abs_dir" 2>/dev/null && pwd)/$abs_base"
fi

case "$abs" in
  "$DOT_DIR/mcp-servers.json"|"$DOT_DIR/.codex/config.base.toml"|"$DOT_DIR/.claude/CLAUDE.md"|"$DOT_DIR/.claude/format.md"|"$DOT_DIR/.claude/pir-handoff.md"|"$DOT_DIR/.claude/agents/"*.md|"$DOT_DIR/.claude/skills/"*)
    if [ -f "$SYNC_SCRIPT" ]; then
      bash "$SYNC_SCRIPT" 2>&1 | sed 's/^/[codex-hook] /' || true
    fi
    ;;
esac

exit 0
