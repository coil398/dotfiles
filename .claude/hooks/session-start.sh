#!/bin/sh
# SessionStart hook: auto-deploy this dotfiles repo when a Claude Code session
# starts in the cloud (Claude Code on the web).
#
# This runs `etc/link.sh`, which symlinks the dotfiles into $HOME (shell config,
# ~/.claude, ~/.codex, git hooks, etc.), so a fresh ephemeral cloud container is
# provisioned with the same environment as a local machine.
#
# Guards (both must hold, otherwise this is a silent no-op):
#   1. CLAUDE_CODE_REMOTE=true  -> only act in the remote/cloud environment.
#      Local sessions deploy via `sh etc/link.sh` manually and must not be
#      disturbed on every SessionStart.
#   2. $CLAUDE_PROJECT_DIR/etc/link.sh exists -> only act when this session is
#      opened on the dotfiles repo itself. This settings.json is the user's
#      global SSOT (linked to ~/.claude/settings.json), so the hook can fire in
#      cloud sessions on unrelated repos; there it must do nothing.
set -eu

[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0
[ -f "${CLAUDE_PROJECT_DIR:-}/etc/link.sh" ] || exit 0

echo "[session-start] deploying dotfiles via etc/link.sh ..."
sh "$CLAUDE_PROJECT_DIR/etc/link.sh"
