#!/usr/bin/env bash
# Claude Code PostToolUse hook for OpenCode SSOT sync.
#
# Triggered after Edit/Write/MultiEdit. Runs etc/sync-opencode.sh only if the
# edited file is one of the OpenCode SSOT files:
#   - dotfiles/mcp-servers.json
#   - dotfiles/AGENTS.md
#   - dotfiles/.claude/settings.json
#   - dotfiles/.claude/agents/*.md
#   - dotfiles/.opencode/plugins/*.(js|ts|mjs)
#
# Other edits are ignored (early exit). The producer result is returned as
# PostToolUse additionalContext, while this hook remains non-blocking.

set -euo pipefail

SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd -P "${SCRIPT_DIR}/../.." && pwd)"
SYNC_SCRIPT="${DOT_DIR}/etc/sync-opencode.sh"

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

emit_sync_result() {
  local status="$1"
  local output="$2"
  local context

  if [ "$status" -eq 0 ]; then
    context="[opencode-hook] sync completed: ${SYNC_SCRIPT}"
  else
    context="[opencode-hook] sync failed (exit ${status}): ${SYNC_SCRIPT}"
  fi
  if [ -n "$output" ]; then
    context+=$'\n'
    context+="$output"
  fi

  jq -nc --arg ctx "$context" '{
    hookSpecificOutput: {
      hookEventName: "PostToolUse",
      additionalContext: $ctx
    }
  }'
}

# Read Claude Code hook payload from stdin (JSON)
input=$(cat)

# Extract edited file path from tool_input.file_path
if ! file_path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null); then
  exit 0
fi
[ -z "$file_path" ] && exit 0

# Normalize to absolute path
case "$file_path" in
  /*) abs="$file_path" ;;
  ~*) abs="${file_path/#\~/$HOME}" ;;
  *)  abs="$(pwd)/$file_path" ;;
esac

# Resolve symlinks: 1) file-level symlink chain, 2) directory-level via cd -P
# Handles both file symlinks and ~/.claude/agents/explorer.md (dir symlink)
# Uses readlink without -f for macOS compatibility; while loop handles multi-hop chains.
# If the directory does not exist (new file being created), cd -P fails silently
# and abs remains unresolved — the case match will simply be a no-op.
while [ -L "$abs" ]; do
  link_target="$(readlink "$abs")"
  case "$link_target" in
    /*) abs="$link_target" ;;
    *)  abs="$(dirname "$abs")/$link_target" ;;
  esac
done
abs_dir="$(dirname "$abs")"
abs_base="$(basename "$abs")"
if [ -d "$abs_dir" ]; then
  abs="$(cd -P "$abs_dir" 2>/dev/null && pwd)/$abs_base"
fi

# Match SSOT files
case "$abs" in
  "$DOT_DIR/mcp-servers.json"|"$DOT_DIR/AGENTS.md"|"$DOT_DIR/.claude/settings.json"|"$DOT_DIR/.claude/agents/"*.md|"$DOT_DIR/.opencode/plugins/"*.js|"$DOT_DIR/.opencode/plugins/"*.ts|"$DOT_DIR/.opencode/plugins/"*.mjs)
    if [ ! -f "$SYNC_SCRIPT" ]; then
      emit_sync_result 127 "producer not found"
      exit 0
    fi

    sync_output=""
    sync_status=0
    if sync_output=$(bash "$SYNC_SCRIPT" 2>&1); then
      sync_status=0
    else
      sync_status=$?
    fi
    emit_sync_result "$sync_status" "$sync_output"
    ;;
esac

exit 0
