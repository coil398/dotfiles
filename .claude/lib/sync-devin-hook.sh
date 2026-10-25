#!/usr/bin/env bash
# Claude Code PostToolUse hook for Devin CLI SSOT sync.
#
# Triggered after Edit/Write/MultiEdit. Runs etc/sync-devin.sh only if the
# edited file is one of the Devin SSOT files:
#   - dotfiles/mcp-servers.json
#   - dotfiles/.claude/settings.json
#   - dotfiles/etc/sync-devin.sh
#
# dotfiles/.agents/global-instructions.md is not watched: it is symlinked
# directly to ~/.config/devin/AGENTS.md by etc/link.sh, so no regeneration is needed.
#
# Other edits are ignored (early exit). The producer result is returned as
# PostToolUse additionalContext, while this hook remains non-blocking.

set -euo pipefail

SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/sync-hook-common.sh"
sync_hook_init "${BASH_SOURCE[0]}" "sync-devin.sh" "devin"

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

if ! sync_hook_read_file_path; then
  exit 0
fi
sync_hook_resolve_path "$SYNC_HOOK_FILE_PATH"

# Match SSOT files
case "$SYNC_HOOK_ABS_PATH" in
  "$SYNC_HOOK_DOT_DIR/mcp-servers.json"|"$SYNC_HOOK_DOT_DIR/.claude/settings.json"|"$SYNC_HOOK_DOT_DIR/etc/sync-devin.sh")
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
