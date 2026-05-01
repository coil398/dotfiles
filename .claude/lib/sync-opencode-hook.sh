#!/usr/bin/env bash
# Claude Code PostToolUse hook for OpenCode SSOT sync.
#
# Triggered after Edit/Write/MultiEdit. Runs etc/sync-opencode.sh only if the
# edited file is one of the OpenCode SSOT files:
#   - dotfiles/mcp-servers.json
#   - dotfiles/.claude/settings.json
#   - dotfiles/.claude/agents/*.md
#
# Other edits are ignored (early exit). Failures are non-blocking.

set -euo pipefail

SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd -P "${SCRIPT_DIR}/../.." && pwd)"
SYNC_SCRIPT="${DOT_DIR}/etc/sync-opencode.sh"

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

# Read Claude Code hook payload from stdin (JSON)
input=$(cat)

# Extract edited file path from tool_input.file_path
file_path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
[ -z "$file_path" ] && exit 0

# Normalize to absolute path
case "$file_path" in
  /*) abs="$file_path" ;;
  ~*) abs="${file_path/#\~/$HOME}" ;;
  *)  abs="$(pwd)/$file_path" ;;
esac

# Resolve symlinks so that ~/.claude/agents/explorer.md (symlink) maps to
# ~/dotfiles/.claude/agents/explorer.md (physical path) for SSOT matching.
# Uses `cd -P` because macOS readlink does not support -f.
# If the directory does not exist (new file being created), cd -P fails silently
# and abs remains unresolved — the case match will simply be a no-op.
abs_dir="$(dirname "$abs")"
abs_base="$(basename "$abs")"
if [ -d "$abs_dir" ]; then
  abs="$(cd -P "$abs_dir" 2>/dev/null && pwd)/$abs_base"
fi

# Match SSOT files
case "$abs" in
  "$DOT_DIR/mcp-servers.json"|"$DOT_DIR/.claude/settings.json"|"$DOT_DIR/.claude/agents/"*.md)
    if [ -f "$SYNC_SCRIPT" ]; then
      bash "$SYNC_SCRIPT" 2>&1 | sed 's/^/[opencode-hook] /' || true
    fi
    ;;
esac

exit 0
