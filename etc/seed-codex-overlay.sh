#!/usr/bin/env bash
# Check the Codex native overlay boundary without synthesizing files.
#
# Codex native Skills are maintained in .codex/skills and shared expertise is
# kept in .agents/skills.  A missing native source is handled by the existing
# layout/link checks or by the task that owns that source; this command never
# reconstructs it from another runtime.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CODEX_SKILLS="${DOT_DIR}/.codex/skills"

log() { echo "[seed-codex] $*"; }

if [ -d "$CODEX_SKILLS" ]; then
  log "preserved Codex native Skills in $CODEX_SKILLS"
else
  log "no Codex native Skill directory at $CODEX_SKILLS"
fi

log "no Codex native seeding performed"
