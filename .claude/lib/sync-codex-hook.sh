#!/usr/bin/env bash
# Claude Code PostToolUse hook for Codex SSOT sync.
#
# Triggered after Edit/Write/MultiEdit. Runs etc/sync-codex.sh only if the
# edited file is one of the Codex SSOT files:
#   - dotfiles/mcp-servers.json
#   - dotfiles/.agents/global-instructions.md
#   - dotfiles/.agents/skills/*/SKILL.md (native shared-skill inventory)
#   - dotfiles/.codex/config.base.toml
#   - dotfiles/.codex/codex-native-supplement.md
#   - dotfiles/.claude/user-feedback-protocol.md
#   - dotfiles/.claude/dev-server.md
#   - dotfiles/etc/sync-codex.sh
#
# Other edits are ignored (early exit). The producer result is returned as
# PostToolUse additionalContext, while this hook remains non-blocking.

set -euo pipefail

SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/sync-hook-common.sh"
sync_hook_init "${BASH_SOURCE[0]}" "sync-codex.sh" "codex"

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

if ! sync_hook_read_file_path; then
  exit 0
fi
sync_hook_resolve_path "$SYNC_HOOK_FILE_PATH"

case "$SYNC_HOOK_ABS_PATH" in
  "$SYNC_HOOK_DOT_DIR/mcp-servers.json"|"$SYNC_HOOK_DOT_DIR/.agents/global-instructions.md"|"$SYNC_HOOK_DOT_DIR/.agents/skills/"*/SKILL.md|"$SYNC_HOOK_DOT_DIR/.codex/config.base.toml"|"$SYNC_HOOK_DOT_DIR/.codex/codex-native-supplement.md"|"$SYNC_HOOK_DOT_DIR/.claude/user-feedback-protocol.md"|"$SYNC_HOOK_DOT_DIR/.claude/dev-server.md"|"$SYNC_HOOK_DOT_DIR/etc/sync-codex.sh")
    if [ ! -f "$SYNC_HOOK_SYNC_SCRIPT" ]; then
      sync_hook_emit_result 127 "producer not found"
      exit 0
    fi

    sync_output=""
    sync_status=0
    if sync_output=$(bash "$SYNC_HOOK_SYNC_SCRIPT" 2>&1); then
      sync_status=0
    else
      sync_status=$?
    fi
    sync_hook_emit_result "$sync_status" "$sync_output"
    ;;
esac

exit 0
