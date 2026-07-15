#!/usr/bin/env bash
# Seed Codex native overlays from Claude/shared SSOT (missing-only; never overwrite).
#
#   bash etc/seed-codex-overlay.sh
#
# Creates only when missing:
#   - .codex/agents/<name>.toml   from .claude/agents/<name>.md
#   - .codex/skills/<name>/       from .agents/skills/<name>/
#
# Does not run SYNC_CODEX_LEGACY_MIRROR (avoids overwriting existing overlays).
# codex-runner is intentionally omitted (Codex does not need a self-CLI bridge agent).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

CLAUDE_AGENTS="${DOT_DIR}/.claude/agents"
SHARED_SKILLS="${DOT_DIR}/.agents/skills"
CODEX_AGENTS="${DOT_DIR}/.codex/agents"
CODEX_SKILLS="${DOT_DIR}/.codex/skills"

AGENTS=(
  deliberator
  epic-planner
  gate
  hypothesizer
  synthesizer
  thinker
)

SKILLS=(
  deepthink
  research
  epic
  unity-mcp-skill
)

log()  { echo "[seed-codex] $*"; }
warn() { echo "[seed-codex] warn: $*" >&2; }

if ! command -v jq >/dev/null 2>&1; then
  warn "jq not found"; exit 1
fi

jq() { command jq "$@" | tr -d '\r'; }

toml_quote() {
  jq -Rn --arg s "$1" '$s'
}

codexize_stream() {
  # Keep in sync with etc/sync-codex.sh#codexize_stream (seed path; missing-only).
  sed \
    -e 's/Claude Code/Codex/g' \
    -e 's/メイン Claude/メイン Codex/g' \
    -e 's/Claude 自身/Codex 自身/g' \
    -e 's/Claude 側/Codex 側/g' \
    -e 's/Claude の/Codex の/g' \
    -e 's/Claude は/Codex は/g' \
    -e 's/Claude が/Codex が/g' \
    -e 's#~/.claude/CLAUDE\.md#~/.codex/AGENTS.md#g' \
    -e 's#~/.claude/agents#~/.codex/agents#g' \
    -e 's#~/.claude/skills#~/.agents/skills#g' \
    -e 's#~/.claude/projects#~/.codex/memories#g' \
    -e "s#\${HOME}/\\.claude#\${HOME}/.codex#g" \
    -e 's#~/.claude/#~/.codex/#g' \
    -e 's#\.claude/CLAUDE\.md#.codex/AGENTS.md#g' \
    -e 's#\.claude/agents#.codex/agents#g' \
    -e 's#\.claude/skills#.agents/skills#g' \
    -e 's#\.claude/settings\.local\.json#.codex/config.toml#g' \
    -e 's#\.claude/settings\.json#.codex/config.toml#g' \
    -e 's#\.claude/#.codex/#g' \
    -e 's/Agent ツール/Codex subagent/g' \
    -e 's/Skill ツール/Codex skill invocation/g' \
    -e 's/TeamCreate/Codex subagent workflows/g' \
    -e 's/サブエージェント/subagent/g' \
    -e 's/claude-sonnet-4-6/gpt-5.5/g' \
    -e 's/haiku/gpt-5.4-mini/g' \
    -e 's/sonnet/gpt-5.5/g' \
    -e 's/opus/gpt-5.5/g' \
    -e 's/fable/gpt-5.5/g'
}

extract_agent_frontmatter_value() {
  local file="$1" key="$2" raw
  raw="$(awk -v key="$key" '
    NR == 1 && $0 == "---" { in_frontmatter = 1; next }
    in_frontmatter && $0 == "---" { exit }
    in_frontmatter && index($0, key ":") == 1 {
      sub("^[^:]+:[[:space:]]*", "")
      print
      exit
    }
  ' "$file")"
  case "$raw" in
    \"*|\'*)
      printf '%s' "$raw" | jq -r . 2>/dev/null || printf '%s' "$raw"
      ;;
    *)
      printf '%s' "$raw"
      ;;
  esac
}

extract_agent_body() {
  local file="$1"
  awk '
    NR == 1 && $0 == "---" { in_frontmatter = 1; next }
    in_frontmatter && $0 == "---" { in_frontmatter = 0; body = 1; next }
    body || !in_frontmatter { print }
  ' "$file"
}

codex_agent_model() {
  case "$1" in
    explorer) printf '%s' "gpt-5.4-mini" ;;
    *)        printf '%s' "gpt-5.5" ;;
  esac
}

codex_agent_reasoning_effort() {
  case "$1" in
    explorer) printf '%s' "low" ;;
    implementer|refactor-advisor|sentinel-iac|tester) printf '%s' "medium" ;;
    *) printf '%s' "high" ;;
  esac
}

quote_yaml_scalar() {
  local raw="${1-}"
  local decoded="$raw"
  case "$raw" in
    \"*\")
      decoded="$(printf '%s' "$raw" | jq -r . 2>/dev/null || printf '%s' "$raw")"
      ;;
  esac
  printf '%s' "$decoded" | jq -Rs .
}

normalize_codex_skill_frontmatter() {
  local file="$1"
  [ -f "$file" ] || return 0
  local tmp
  tmp="$(mktemp "${file}.tmp.XXXXXX")"
  local fence_count=0
  while IFS= read -r line || [ -n "$line" ]; do
    if [ "$line" = "---" ]; then
      fence_count=$((fence_count + 1))
      printf '%s\n' "$line" >> "$tmp"
      continue
    fi
    if [ "$fence_count" -eq 1 ] && [[ "$line" =~ ^([A-Za-z0-9_-]+):[[:space:]]*(.*)$ ]]; then
      local key="${BASH_REMATCH[1]}"
      local value="${BASH_REMATCH[2]}"
      printf '%s: %s\n' "$key" "$(quote_yaml_scalar "$value")" >> "$tmp"
    else
      printf '%s\n' "$line" >> "$tmp"
    fi
  done < "$file"
  mv -f "$tmp" "$file"
}

seed_agent() {
  local name="$1"
  local src="${CLAUDE_AGENTS}/${name}.md"
  local dst="${CODEX_AGENTS}/${name}.toml"
  [ -f "$src" ] || { warn "missing agent source $src"; return 0; }
  if [ -f "$dst" ]; then
    log "skip existing $dst"
    return 0
  fi

  local description body model reasoning_effort
  description="$(extract_agent_frontmatter_value "$src" "description")"
  [ -n "$description" ] || description="Codex custom agent seeded from ${name}.md"
  description="$(printf '%s' "$description" | codexize_stream)"
  body="$(extract_agent_body "$src" | codexize_stream)"
  model="$(codex_agent_model "$name")"
  reasoning_effort="$(codex_agent_reasoning_effort "$name")"

  {
    echo "# Seeded Codex native overlay from .claude/agents/${name}.md (editable; default sync does not overwrite)."
    printf 'name = %s\n' "$(toml_quote "$name")"
    printf 'description = %s\n' "$(toml_quote "$description")"
    printf 'model = %s\n' "$(toml_quote "$model")"
    printf 'model_reasoning_effort = %s\n' "$(toml_quote "$reasoning_effort")"
    printf 'developer_instructions = %s\n' "$(printf '%s' "$body" | jq -Rs .)"
  } >"$dst"
  log "seeded $dst (model=$model effort=$reasoning_effort)"
}

seed_skill() {
  local name="$1"
  local src="${SHARED_SKILLS}/${name}"
  local dst="${CODEX_SKILLS}/${name}"
  [ -d "$src" ] || { warn "missing skill source $src"; return 0; }
  if [ -d "$dst" ]; then
    log "skip existing $dst"
    return 0
  fi

  mkdir -p "$dst"
  cp -a "$src"/. "$dst"/
  rm -rf "$dst/.git"
  find "$dst" -type f -name '*.md' | while IFS= read -r file; do
    tmp="$(mktemp "${file}.tmp.XXXXXX")"
    codexize_stream <"$file" >"$tmp"
    mv -f "$tmp" "$file"
  done
  normalize_codex_skill_frontmatter "$dst/SKILL.md"
  if [ -f "$dst/SKILL.md" ] && ! grep -q 'Codex native overlay' "$dst/SKILL.md"; then
    tmp="$(mktemp)"
    awk '
      BEGIN { fm = 0; closed = 0 }
      NR == 1 && $0 == "---" { fm = 1; print; next }
      fm && $0 == "---" {
        print
        if (!closed) {
          print ""
          print "<!-- Codex native overlay: seeded from .agents/skills; edit here for Codex mechanics -->"
          closed = 1
        }
        next
      }
      { print }
    ' "$dst/SKILL.md" >"$tmp"
    mv "$tmp" "$dst/SKILL.md"
  fi
  log "seeded $dst"
}

mkdir -p "$CODEX_AGENTS" "$CODEX_SKILLS"

for a in "${AGENTS[@]}"; do
  seed_agent "$a"
done

for s in "${SKILLS[@]}"; do
  seed_skill "$s"
done

log "done"
