#!/usr/bin/env bash
# Seed missing Cursor skill entries from the shared skill SSOT.
#
# Creates only when missing:
#   - .cursor/skills/<name>/SKILL.md as a thin read-entry for
#     .agents/skills/<name>/SKILL.md
# Cursor agent overlays are authored as short runtime-native adapters. This
# seed does not mirror the Claude skill or agent sets and never recreates
# removed roles.
#
# Never overwrites existing overlay files/directories (no FORCE path).
# Does not invent model policy; follow AGENTS.md and Cursor's public schema for
# model selection and role metadata.
# Claude-only skills are reported when they have no existing Cursor overlay.

set -euo pipefail

SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
DOT_DIR="$(cd -P "${SCRIPT_DIR}/.." && pwd -P)"

SHARED_SKILLS="${DOT_DIR}/.agents/skills"
CLAUDE_SKILLS="${DOT_DIR}/.claude/skills"
CURSOR_AGENTS="${DOT_DIR}/.cursor/agents"
CURSOR_SKILLS="${DOT_DIR}/.cursor/skills"

log()  { echo "[seed-cursor] $*"; }
warn() { echo "[seed-cursor] warn: $*" >&2; }

if [ "${SYNC_CURSOR_SEED_FORCE:-}" = "1" ]; then
  warn "SYNC_CURSOR_SEED_FORCE is ignored (force seed removed by design)"
fi

# Fail seed if known-bad residues remain in the overlay tree.
# Keep this check focused on Cursor-specific launch/path residues. Explicit
# public model IDs in native prose are valid and are not rejected here.
verify_cursor_overlay_hygiene() {
  local bad
  bad="$(
    {
      grep -RInE 'dotfiles \.claude reference:|~/\.claude/projects/|\$\{HOME\}/\.claude/projects/' \
        "$CURSOR_AGENTS" "$CURSOR_SKILLS" 2>/dev/null || true
      # Agent-as-launcher residue (banners that say "語彙は使わない" are OK)
      grep -RInE '`Agent` ツール|Agent ツール' "$CURSOR_AGENTS" "$CURSOR_SKILLS" 2>/dev/null \
        | grep -v '語彙は使わない' || true
      # Check model assignments, not unrelated prose or slash-flag aliases.
      grep -RInE 'model[[:space:]]*[:=][[:space:]]*[[:punct:]]?(opus|sonnet|Opus|Sonnet)([^[:alnum:]_-]|$)' \
        "$CURSOR_AGENTS" "$CURSOR_SKILLS" 2>/dev/null || true
      grep -RInE 'model=reasoning|（model: reasoning）|\*\*`model=reasoning`\*\*' \
        "$CURSOR_SKILLS" 2>/dev/null || true
      grep -RInE '^model: (coding|reasoning)[[:space:]]*$' \
        "$CURSOR_AGENTS" 2>/dev/null || true
      grep -RInE 'ベンダーモデル名' "$CURSOR_SKILLS" 2>/dev/null || true
      grep -RInF 'role=reasoning|coding' "$CURSOR_SKILLS" 2>/dev/null || true
    } | head -50
  )"
  if [ -n "$bad" ]; then
    warn "overlay hygiene check failed:"
    printf '%s\n' "$bad" >&2
    return 1
  fi
  log "overlay hygiene check passed"
}

resolve_shared_skill_src() {
  local name="$1"
  if [ -f "${SHARED_SKILLS}/${name}/SKILL.md" ]; then
    printf '%s' "${SHARED_SKILLS}/${name}"
    return 0
  fi
  return 1
}

list_shared_skill_names() {
  local skill_dir
  [ -d "$SHARED_SKILLS" ] || return 0
  for skill_dir in "$SHARED_SKILLS"/*; do
    [ -f "${skill_dir}/SKILL.md" ] || continue
    basename "$skill_dir"
  done | sort -u
}

report_unseeded_claude_skills() {
  local skill_dir name dest
  [ -d "$CLAUDE_SKILLS" ] || return 0
  for skill_dir in "$CLAUDE_SKILLS"/*; do
    [ -f "${skill_dir}/SKILL.md" ] || continue
    name="$(basename "$skill_dir")"
    [ -f "${SHARED_SKILLS}/${name}/SKILL.md" ] && continue
    dest="${CURSOR_SKILLS}/${name}"
    if [ -e "$dest" ] || [ -L "$dest" ]; then
      log "preserve existing Cursor overlay for Claude-only skill $name"
    else
      warn "Claude-only skill $name has no shared source or existing Cursor overlay; not seeded"
    fi
  done
}

render_skill_entry() {
  local src_md="$1" name="$2" fallback="$3" out="$4"
  # Copy only the first YAML frontmatter block. The shared body and all
  # references/scripts/assets remain at the SSOT path.
  if ! awk '
    NR == 1 && $0 == "---" { opened = 1; print; next }
    opened && $0 == "---" { print; closed = 1; exit }
    opened { print; next }
    { exit 1 }
    END { if (!closed) exit 1 }
  ' "$src_md" >"$out"; then
    warn "shared skill has invalid frontmatter; cannot seed $name: $src_md"
    return 1
  fi
  cat >>"$out" <<EOF

<!-- Cursor thin entry; the shared skill remains the source of truth. -->
SHARED_SKILL_PATH=../../../.agents/skills/${name}/SKILL.md

Read the shared skill at \`SHARED_SKILL_PATH\` relative to this entry file, then follow its instructions.
If relative resolution is unavailable, read the checked-out source at \`${fallback}\`.
The shared skill's references/, scripts/, and other assets remain at that source path and are not copied here.
EOF
}

seed_skill_dir() {
  local name="$1" src dest tmp
  # Same basename as .agents/skills — .cursor/skills takes precedence, so no cursor- prefix.
  dest="${CURSOR_SKILLS}/${name}"
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    log "skip existing $dest"
    return 0
  fi
  if ! src="$(resolve_shared_skill_src "$name")"; then
    warn "missing shared skill source for $name; not seeded from Claude"
    return 0
  fi

  tmp="$(mktemp)"
  if ! render_skill_entry "${src}/SKILL.md" "$name" "${src}/SKILL.md" "$tmp"; then
    rm -f "$tmp"
    return 1
  fi
  mkdir -p "$dest"
  if ! mv "$tmp" "${dest}/SKILL.md"; then
    rm -f "$tmp"
    return 1
  fi
  # Directory + frontmatter name must match (Cursor requires name == folder).
  bash "${SCRIPT_DIR}/normalize-cursor-skill-names.sh" "${dest}/SKILL.md" "$name"
  log "seeded $dest/SKILL.md (thin entry for ${src}/SKILL.md)"
}

mkdir -p "$CURSOR_SKILLS"

while IFS= read -r s; do
  [ -n "$s" ] || continue
  seed_skill_dir "$s"
done < <(list_shared_skill_names)

report_unseeded_claude_skills

verify_cursor_overlay_hygiene

log "done"
