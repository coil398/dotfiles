#!/usr/bin/env bash
#
# Auto-sync ~/dotfiles repo (git@github.com:coil398/dotfiles).
# Pulls upstream changes; local edits are autostashed and re-applied.
#
# Designed to run from cron. No-op when nothing to pull.

set -uo pipefail

REPO=/home/claw/dotfiles
LOG=/home/claw/.local/share/dotfiles-sync.log
GIT_SSH_COMMAND="ssh -o BatchMode=yes -i /home/claw/.ssh/github -F /home/claw/.ssh/config"
export GIT_SSH_COMMAND

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "[$(ts)] $*" >>"$LOG"; }

cd "$REPO" || { log "FAIL cd $REPO"; exit 1; }

if ! git pull --rebase --autostash --quiet 2>>"$LOG"; then
  log "WARN pull failed (likely conflict; manual resolution needed)"
  exit 1
fi
