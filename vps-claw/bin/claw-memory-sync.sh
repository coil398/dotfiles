#!/usr/bin/env bash
#
# Auto-sync claw-memory skill repo:
#   - data/memory.db
#   - workspace-backup/ (md + memory/ via symlinks)
#
# Designed to run from cron. Idempotent; no-op when there are no changes.

set -uo pipefail

REPO=/home/claw/.openclaw/workspace/skills/claw-memory
LOG=/home/claw/.local/share/claw-memory-sync.log
GIT_SSH_COMMAND="ssh -o BatchMode=yes -i /home/claw/.ssh/github -F /home/claw/.ssh/config"
export GIT_SSH_COMMAND

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "[$(ts)] $*" >>"$LOG"; }

cd "$REPO" || { log "FAIL cd $REPO"; exit 1; }

# 1. Pull first to avoid push rejections.
if ! git pull --rebase --autostash --quiet 2>>"$LOG"; then
  log "WARN pull failed; aborting (likely binary conflict on memory.db; see SKILL.md merge resolution)"
  exit 1
fi

# 2. Stage only the directories we own (data/ + workspace-backup/).
git add data/ workspace-backup/ 2>>"$LOG" || true

# 3. No-op if nothing changed.
if git diff --cached --quiet; then
  exit 0
fi

# 4. Commit + push.
if ! git commit -m "auto-sync: $(ts)" --quiet >>"$LOG" 2>&1; then
  log "FAIL commit"
  exit 1
fi

if ! git push --quiet 2>>"$LOG"; then
  log "FAIL push"
  exit 1
fi

log "OK pushed auto-sync"
