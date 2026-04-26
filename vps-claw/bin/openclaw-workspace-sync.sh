#!/usr/bin/env bash
#
# Auto-sync OpenClaw agent workspace repo (~/.openclaw/workspace).
# Captures everything not gitignored (raw workspace state).
#
# Designed to run from cron. Idempotent; no-op when nothing changed.

set -uo pipefail

REPO=/home/claw/.openclaw/workspace
LOG=/home/claw/.local/share/openclaw-workspace-sync.log
GIT_SSH_COMMAND="ssh -o BatchMode=yes -i /home/claw/.ssh/github -F /home/claw/.ssh/config"
export GIT_SSH_COMMAND

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "[$(ts)] $*" >>"$LOG"; }

cd "$REPO" || { log "FAIL cd $REPO"; exit 1; }

# 1. Pull first.
if ! git pull --rebase --autostash --quiet 2>>"$LOG"; then
  log "WARN pull failed (likely conflict; manual resolution needed)"
  exit 1
fi

# 2. Stage everything not gitignored.
git add -A 2>>"$LOG" || true

# 3. No-op if nothing staged.
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
