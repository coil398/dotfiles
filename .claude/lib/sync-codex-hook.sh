#!/usr/bin/env bash
# Claude Code PostToolUse hook for Codex SSOT sync.
#
# Triggered after Edit/Write/MultiEdit. Runs etc/sync-codex.sh only if the
# edited file is one of the Codex SSOT files:
#   - dotfiles/mcp-servers.json
#   - dotfiles/AGENTS.md
#   - dotfiles/.agents/skills/**
#   - dotfiles/.codex/config.base.toml
#   - dotfiles/.codex/codex-native-supplement.md
#   - dotfiles/.claude/settings.json
#   - dotfiles/.claude/format.md
#   - dotfiles/.claude/pir-handoff.md
#   - dotfiles/.claude/user-feedback-protocol.md
#   - dotfiles/.claude/agent-delegation.md
#   - dotfiles/.claude/pir2-protocol.md
#   - dotfiles/.claude/dev-server.md
#   - dotfiles/.claude/subagent-permissions.md
#   - dotfiles/.claude/agents/*.md
#
# Other edits are ignored (early exit). The producer result is returned as
# PostToolUse additionalContext, while this hook remains non-blocking.

set -euo pipefail

SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd -P "${SCRIPT_DIR}/../.." && pwd)"
SYNC_SCRIPT="${DOT_DIR}/etc/sync-codex.sh"

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

emit_sync_result() {
  local status="$1"
  local output="$2"
  local context

  if [ "$status" -eq 0 ]; then
    context="[codex-hook] sync completed: ${SYNC_SCRIPT}"
  else
    context="[codex-hook] sync failed (exit ${status}): ${SYNC_SCRIPT}"
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

input=$(cat)

if ! file_path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null); then
  exit 0
fi
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
  "$DOT_DIR/mcp-servers.json"|"$DOT_DIR/AGENTS.md"|"$DOT_DIR/.agents/skills/"*|"$DOT_DIR/.codex/config.base.toml"|"$DOT_DIR/.codex/codex-native-supplement.md"|"$DOT_DIR/.claude/settings.json"|"$DOT_DIR/.claude/format.md"|"$DOT_DIR/.claude/pir-handoff.md"|"$DOT_DIR/.claude/user-feedback-protocol.md"|"$DOT_DIR/.claude/agent-delegation.md"|"$DOT_DIR/.claude/pir2-protocol.md"|"$DOT_DIR/.claude/dev-server.md"|"$DOT_DIR/.claude/subagent-permissions.md"|"$DOT_DIR/.claude/agents/"*.md)
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
