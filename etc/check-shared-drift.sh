#!/usr/bin/env bash
# Check that shared-core skills have a usable SSOT and report optional runtime
# overlays without requiring every runtime to copy the shared body.
#
#   bash etc/check-shared-drift.sh
#
# Exit 0 if every shared skill has a readable SSOT, 1 otherwise.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

SHARED="${DOT_DIR}/.agents/skills"
CLAUDE_SKILLS="${DOT_DIR}/.claude/skills"
CURSOR_SKILLS="${DOT_DIR}/.cursor/skills"
CURSOR_AGENTS="${DOT_DIR}/.cursor/agents"

fail=0
pass=0

ok() { echo "PASS: $*"; pass=$((pass + 1)); }
bad() { echo "FAIL: $*"; fail=$((fail + 1)); }
info() { echo "INFO: $*"; }

list_dirs() {
  local root="$1"
  [ -d "$root" ] || return 0
  # Portable: no GNU -printf (macOS find lacks it; empty list → false clean).
  find "$root" -mindepth 1 -maxdepth 1 -type d | while IFS= read -r p; do
    basename "$p"
  done | sort
}

# --- Skills: shared core is the SSOT; native overlays are optional ---
while IFS= read -r name; do
  [ -n "$name" ] || continue
  if [ ! -f "${SHARED}/${name}/SKILL.md" ] || [ ! -r "${SHARED}/${name}/SKILL.md" ]; then
    bad "shared skill '${name}' missing or unreadable SKILL.md"
    continue
  fi
  overlays=""
  [ -d "${CURSOR_SKILLS}/${name}" ] && overlays="${overlays} cursor"
  if [ -n "$overlays" ]; then
    info "shared skill '${name}' available from SSOT (native overlays:${overlays})"
  else
    ok "shared skill '${name}' available from SSOT (native overlays omitted)"
  fi
done < <(list_dirs "$SHARED")

# Runtime-specific skill directories remain valid when their specialized body
# has not been promoted to the shared SSOT.  Report them for visibility only.
while IFS= read -r name; do
  [ -n "$name" ] || continue
  if [ -d "${CLAUDE_SKILLS}/${name}" ] && [ ! -d "${SHARED}/${name}" ]; then
    info "runtime-specific Claude skill '${name}' is outside shared SSOT"
  fi
done < <(list_dirs "$CLAUDE_SKILLS")

# --- Agents: runtime definitions are independent and optional ---
# No cross-runtime set is required because standard runtime agents and shared
# Skills provide the common behavior.
if [ -d "$CURSOR_AGENTS" ]; then
  info "runtime agent directory available: ${CURSOR_AGENTS}"
fi

# --- Codex runner: one shared procedure read by every runtime's /codex entry ---
if [ -r "${SHARED}/codex/references/runner.md" ]; then
  ok "shared codex runner reference is readable"
else
  bad "shared codex runner reference missing: ${SHARED}/codex/references/runner.md"
fi
for runner_copy in "${CLAUDE_SKILLS}/codex/references/runner.md" "${CURSOR_AGENTS}/codex-runner.md"; do
  if [ -e "$runner_copy" ]; then
    bad "runtime-local codex runner copy duplicates the shared reference: ${runner_copy}"
  fi
done

echo
echo "shared drift: ${pass} passed, ${fail} failed"
if [ "$fail" -ne 0 ]; then
  exit 1
fi
exit 0
