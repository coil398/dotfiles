#!/usr/bin/env bash
# Seed Cursor native overlays from Claude/shared SSOT (phase-2 expanded slice).
#
# Creates only when missing:
#   - .cursor/agents/<name>.md   from .claude/agents/<name>.md
#   - .cursor/skills/<name>/     from .agents/skills/<name>/
#     (fallback: .claude/skills/<name>/ when shared core is absent)
#
# Never overwrites existing overlay files/directories (no FORCE path).
# Does not invent concrete Cursor model IDs — omits model frontmatter;
# operational defaults are role-based (see docs/brainstorm/2026-07-13-cursor-port.md).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

CLAUDE_AGENTS="${DOT_DIR}/.claude/agents"
CLAUDE_SKILLS="${DOT_DIR}/.claude/skills"
SHARED_SKILLS="${DOT_DIR}/.agents/skills"
CURSOR_AGENTS="${DOT_DIR}/.cursor/agents"
CURSOR_SKILLS="${DOT_DIR}/.cursor/skills"

# Phase-2 set (design wave-2). Existing overlays are never overwritten.
# codex-runner is omitted (Cursor does not need Codex CLI runner agent).
AGENTS=(
  explorer
  implementer
  reviewer
  planner
  tester
  tech-validator
  refactor-advisor
  sentinel-iac
  ui-ux-reviewer
  deliberator
  gate
  synthesizer
  hypothesizer
  epic-planner
  retrospector
  meta-retrospector
  thinker
)

SKILLS=(
  chat
  brainstorm
  walkthrough
  reviewer
  debug
  writing-plan
  ir
  tester
  review-pr
  refactor-advisor
  sentinel-review
  pir2
  pir2async
  deepthink
  research
  epic
  retro
  instruction-refactor
  check-updates
)

log()  { echo "[seed-cursor] $*"; }
warn() { echo "[seed-cursor] warn: $*" >&2; }

if [ "${SYNC_CURSOR_SEED_FORCE:-}" = "1" ]; then
  warn "SYNC_CURSOR_SEED_FORCE is ignored (force seed removed by design)"
fi

adapt_agent_body() {
  sed \
    -e 's/`Agent` ツール/`Task` ツール/g' \
    -e 's/Agent ツール/Task ツール/g' \
    -e 's/Codex subagent/Task subagent/g' \
    -e 's/メイン Claude/メインエージェント/g' \
    -e 's/メイン Codex/メインエージェント/g' \
    -e 's/Claude Code/Cursor/g' \
    -e 's/~\/\.codex\/AGENTS\.md/AGENTS.md (shared SSOT)/g' \
    -e 's/~\/\.claude\/AGENTS\.md/AGENTS.md (shared SSOT)/g' \
    -e 's/~\/\.claude\//dotfiles .claude reference: /g' \
    -e 's/subagent内からの Agent 呼び出しは Codex の設計上不可能なため/子 subagent からの Task 起動は Cursor では制限されるため/g'
}

extract_frontmatter_field() {
  local file="$1" field="$2"
  awk -v f="$field" '
    NR == 1 && $0 == "---" { in_fm = 1; next }
    in_fm && $0 == "---" { exit }
    in_fm && $0 ~ "^" f ":" {
      sub("^" f ": *", "")
      print
      exit
    }
  ' "$file"
}

role_for_claude_model() {
  case "${1:-}" in
    opus|fable) printf '%s' 'reasoning' ;;
    *)          printf '%s' 'coding' ;;
  esac
}

seed_agent() {
  local name="$1"
  local src="${CLAUDE_AGENTS}/${name}.md"
  local dest="${CURSOR_AGENTS}/${name}.md"
  [ -f "$src" ] || { warn "missing agent source $src"; return 0; }
  if [ -f "$dest" ]; then
    log "skip existing $dest"
    return 0
  fi

  local description claude_model role
  description="$(extract_frontmatter_field "$src" description)"
  claude_model="$(extract_frontmatter_field "$src" model)"
  role="$(role_for_claude_model "$claude_model")"
  description="$(printf '%s' "$description" | adapt_agent_body)"

  mkdir -p "$CURSOR_AGENTS"
  {
    printf '%s\n' '---'
    printf 'name: %s\n' "$name"
    printf 'description: %s\n' "$description"
    printf '%s\n' '---'
    printf '\n'
    printf '<!-- Cursor native overlay. role=%s (no model pin; operational default via Cursor UI) -->\n' "$role"
    printf '\n'
    awk 'BEGIN { fm = 0; done = 0 }
      NR == 1 && $0 == "---" { fm = 1; next }
      fm && $0 == "---" { fm = 0; done = 1; next }
      fm { next }
      done { print }' "$src" | adapt_agent_body
  } >"$dest"
  log "seeded $dest (role=$role)"
}

resolve_skill_src() {
  local name="$1"
  if [ -d "${SHARED_SKILLS}/${name}" ]; then
    printf '%s' "${SHARED_SKILLS}/${name}"
    return 0
  fi
  if [ -d "${CLAUDE_SKILLS}/${name}" ]; then
    printf '%s' "${CLAUDE_SKILLS}/${name}"
    return 0
  fi
  return 1
}

seed_skill_dir() {
  local name="$1"
  local src dest
  dest="${CURSOR_SKILLS}/${name}"
  if ! src="$(resolve_skill_src "$name")"; then
    warn "missing skill source for $name (checked .agents/skills and .claude/skills)"
    return 0
  fi
  if [ -d "$dest" ]; then
    log "skip existing $dest"
    return 0
  fi

  local src_label=".agents/skills"
  case "$src" in
    "${CLAUDE_SKILLS}"/*) src_label=".claude/skills" ;;
  esac

  mkdir -p "$dest"
  for f in SKILL.md references scripts assets; do
    [ -e "${src}/${f}" ] || continue
    if [ -f "${src}/${f}" ]; then
      adapt_agent_body <"${src}/${f}" >"${dest}/${f}"
    elif [ -d "${src}/${f}" ]; then
      mkdir -p "${dest}/${f}"
      find "${src}/${f}" -type f | while read -r sf; do
        rel="${sf#${src}/${f}/}"
        mkdir -p "$(dirname "${dest}/${f}/${rel}")"
        adapt_agent_body <"$sf" >"${dest}/${f}/${rel}"
      done
    fi
  done

  if [ -f "${dest}/SKILL.md" ]; then
    if ! grep -q 'Cursor native overlay' "${dest}/SKILL.md"; then
      tmp="$(mktemp)"
      awk -v src_label="$src_label" '
        BEGIN { fm = 0; closed = 0 }
        NR == 1 && $0 == "---" { fm = 1; print; next }
        fm && $0 == "---" {
          print
          if (!closed) {
            print ""
            print "<!-- Cursor native overlay: seeded from " src_label "; edit here for Cursor mechanics -->"
            closed = 1
          }
          next
        }
        { print }
      ' "${dest}/SKILL.md" >"$tmp"
      mv "$tmp" "${dest}/SKILL.md"
    fi
  fi
  log "seeded $dest (from $src_label)"
}

mkdir -p "$CURSOR_AGENTS" "$CURSOR_SKILLS"

for a in "${AGENTS[@]}"; do
  seed_agent "$a"
done

for s in "${SKILLS[@]}"; do
  seed_skill_dir "$s"
done

log "done"
