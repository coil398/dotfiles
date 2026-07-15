#!/usr/bin/env bash
# Detect shared-core skills/agents that exist in only one runtime overlay
# (trapped shared rule), without requiring byte-identical copies.
#
#   bash etc/check-shared-drift.sh
#
# Exit 0 if clean, 1 if trapped items found.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

SHARED="${DOT_DIR}/.agents/skills"
CLAUDE_SKILLS="${DOT_DIR}/.claude/skills"
CURSOR_SKILLS="${DOT_DIR}/.cursor/skills"
CODEX_SKILLS="${DOT_DIR}/.codex/skills"
CLAUDE_AGENTS="${DOT_DIR}/.claude/agents"
CURSOR_AGENTS="${DOT_DIR}/.cursor/agents"
CODEX_AGENTS="${DOT_DIR}/.codex/agents"

# Intentionally Claude/Cursor-only (or Claude-only) — not trapped.
# Format: name|reason
SKILL_ALLOWLIST=(
  "pir2codex|Claude/Cursor Codex-implement bridge; not shared core"
)

# Agents that must not exist on a given runtime.
AGENT_ALLOWLIST=(
  "codex-runner|Codex self-CLI bridge; omit on Codex runtime"
)

fail=0
pass=0

ok() { echo "PASS: $*"; pass=$((pass + 1)); }
bad() { echo "FAIL: $*"; fail=$((fail + 1)); }
info() { echo "INFO: $*"; }

in_allowlist() {
  local name="$1" kind="$2" entry key
  local -n list_ref="${kind}_ALLOWLIST"
  for entry in "${list_ref[@]}"; do
    key="${entry%%|*}"
    if [ "$key" = "$name" ]; then
      return 0
    fi
  done
  return 1
}

list_dirs() {
  local root="$1"
  [ -d "$root" ] || return 0
  # Portable: no GNU -printf (macOS find lacks it; empty list → false clean).
  find "$root" -mindepth 1 -maxdepth 1 -type d | while IFS= read -r p; do
    basename "$p"
  done | sort
}

list_agents() {
  local root="$1" ext="$2"
  [ -d "$root" ] || return 0
  find "$root" -maxdepth 1 -type f -name "*.${ext}" | while IFS= read -r p; do
    basename "$p" ".${ext}"
  done | sort
}

# --- Skills: shared core should reach Cursor + Codex overlays (unless allowlisted) ---
while IFS= read -r name; do
  [ -n "$name" ] || continue
  if in_allowlist "$name" SKILL; then
    info "skill $name allowlisted"
    continue
  fi
  missing=""
  [ -d "${CURSOR_SKILLS}/${name}" ] || missing="${missing} cursor"
  [ -d "${CODEX_SKILLS}/${name}" ] || missing="${missing} codex"
  if [ -n "$missing" ]; then
    bad "shared skill '${name}' trapped (missing:${missing})"
  else
    ok "shared skill '${name}' present in cursor+codex"
  fi
done < <(list_dirs "$SHARED")

# Claude-only skills that are also in shared should not be Claudes exclusive:
# (Already covered by shared loop.)

# Claude skill present, shared absent, Cursor present via seed fallback — warn as promote candidate
while IFS= read -r name; do
  [ -n "$name" ] || continue
  if in_allowlist "$name" SKILL; then
    continue
  fi
  if [ -d "${CLAUDE_SKILLS}/${name}" ] && [ ! -d "${SHARED}/${name}" ]; then
    if [ -d "${CURSOR_SKILLS}/${name}" ] || [ -d "${CODEX_SKILLS}/${name}" ]; then
      bad "claude skill '${name}' used by overlay but not in .agents/skills (promote candidate)"
    else
      info "claude-only skill '${name}' (no overlay) — OK if intentional"
    fi
  fi
done < <(list_dirs "$CLAUDE_SKILLS")

# --- Agents: Claude set should reach Cursor; Codex gets set minus allowlisted ---
while IFS= read -r name; do
  [ -n "$name" ] || continue
  if [ ! -f "${CURSOR_AGENTS}/${name}.md" ]; then
    if in_allowlist "$name" AGENT && [ "$name" = "codex-runner" ]; then
      # Cursor should have it; allowlist is for Codex absence
      bad "cursor missing agent '${name}'"
    else
      bad "cursor missing agent '${name}'"
    fi
  else
    ok "cursor agent '${name}'"
  fi

  if in_allowlist "$name" AGENT; then
    if [ -f "${CODEX_AGENTS}/${name}.toml" ]; then
      bad "codex should omit allowlisted agent '${name}'"
    else
      ok "codex omits allowlisted agent '${name}'"
    fi
    continue
  fi

  if [ ! -f "${CODEX_AGENTS}/${name}.toml" ]; then
    bad "codex missing agent '${name}'"
  else
    ok "codex agent '${name}'"
  fi
done < <(list_agents "$CLAUDE_AGENTS" md)

echo
echo "shared drift: ${pass} passed, ${fail} failed"
if [ "$fail" -ne 0 ]; then
  exit 1
fi
exit 0
