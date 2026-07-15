#!/usr/bin/env bash
# Seed Cursor native overlays from Claude/shared SSOT (phase-3 expanded set).
#
# Creates only when missing:
#   - .cursor/agents/<name>.md   from .claude/agents/<name>.md
#   - .cursor/skills/<name>/     from .agents/skills/<name>/
#     (fallback: .claude/skills/<name>/ when shared core is absent)
#
# Never overwrites existing overlay files/directories (no FORCE path).
# Does not invent concrete Cursor model IDs — omits model frontmatter;
# operational defaults are role-based (see docs/brainstorm/2026-07-13-cursor-port.md).
# Codex bridge overlays may keep real Codex CLI model IDs (gpt-5.*).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

CLAUDE_AGENTS="${DOT_DIR}/.claude/agents"
CLAUDE_SKILLS="${DOT_DIR}/.claude/skills"
SHARED_SKILLS="${DOT_DIR}/.agents/skills"
CURSOR_AGENTS="${DOT_DIR}/.cursor/agents"
CURSOR_SKILLS="${DOT_DIR}/.cursor/skills"

# Phase-3 set. Existing overlays are never overwritten.
# Includes Codex bridge (codex-runner / codex / pir2codex) and submodule skills.
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
  codex-runner
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
  pir2codex
  deepthink
  research
  epic
  retro
  instruction-refactor
  check-updates
  ai-design-system
  ai-diary
  ai-ltm
  unity-mcp-skill
  codex
)

log()  { echo "[seed-cursor] $*"; }
warn() { echo "[seed-cursor] warn: $*" >&2; }

if [ "${SYNC_CURSOR_SEED_FORCE:-}" = "1" ]; then
  warn "SYNC_CURSOR_SEED_FORCE is ignored (force seed removed by design)"
fi

adapt_agent_body() {
  # NOTE: Do NOT rewrite ~/.claude/ paths into "dotfiles .claude reference:" —
  # that produced unexecutable shell paths (review 2026-07-13). Keep real paths
  # or map only known safe tokens below.
  # GNU sed BRE: literal braces via [{] [}] (\{n\} is interval syntax).
  # Do not rewrite gpt-5.* — Codex bridge overlays need real Codex CLI model IDs.
  sed \
    -e 's/`Agent` ツール/`Task` ツール/g' \
    -e 's/`Agent`/`Task`/g' \
    -e 's/Agent ツール/Task ツール/g' \
    -e 's/Agent({/Task({/g' \
    -e 's/background Agent/background Task/g' \
    -e 's/Codex subagent/Task subagent/g' \
    -e 's/メイン Claude/メインエージェント/g' \
    -e 's/メイン Codex/メインエージェント/g' \
    -e 's/Claude Code v2\.1\.[0-9][0-9]*/Cursor (Task\/subagent)/g' \
    -e 's/Claude Code/Cursor/g' \
    -e 's/~\/\.codex\/AGENTS\.md/AGENTS.md (shared SSOT)/g' \
    -e 's/~\/\.claude\/AGENTS\.md/AGENTS.md (shared SSOT)/g' \
    -e 's/~\/\.codex\/projects\//~\/.cursor\/projects\//g' \
    -e 's/~\/\.claude\/projects\//~\/.cursor\/projects\//g' \
    -e 's/\$[{]HOME[}]\/\.codex\/projects\//${HOME}\/.cursor\/projects\//g' \
    -e 's/\$[{]HOME[}]\/\.claude\/projects\//${HOME}\/.cursor\/projects\//g' \
    -e 's/~\/\.agents\/skills\//.cursor\/skills\//g' \
    -e 's/\$HOME\/\.agents\/skills\//.cursor\/skills\//g' \
    -e 's/~\/\.claude\/skills\//.cursor\/skills\//g' \
    -e 's/~\/\.claude\/agents\//.cursor\/agents\//g' \
    -e 's/subagent内からの Agent 呼び出しは Codex の設計上不可能なため/子 subagent からの Task 起動は Cursor では制限されるため/g' \
    -e 's/\bopus\b/reasoning/g' \
    -e 's/\bsonnet\b/coding/g' \
    -e 's/\bOpus\b/reasoning/g' \
    -e 's/\bSonnet\b/coding/g' \
    -e 's/\bfable\b/reasoning/g' \
    -e 's/\bFable\b/reasoning/g' \
    -e 's/Claude の `Task` ツール語彙は使わない/Claude の `Agent` ツール語彙は使わない/g'
}

# Fail seed if known-bad residues remain in the overlay tree.
# Codex bridge overlays (codex-runner / codex / pir2codex) may mention gpt-5.* —
# those are real Codex CLI model IDs, not Cursor vendor pins.
verify_cursor_overlay_hygiene() {
  local bad
  bad="$(
    {
      grep -RInE 'dotfiles \.claude reference:|~/\.claude/projects/|\$\{HOME\}/\.claude/projects/' \
        "$CURSOR_AGENTS" "$CURSOR_SKILLS" 2>/dev/null || true
      grep -RInE 'gpt-5\.' "$CURSOR_AGENTS" "$CURSOR_SKILLS" 2>/dev/null \
        | grep -vE '/(codex-runner\.md|codex/|pir2codex/)' || true
      # Agent-as-launcher residue (banners that say "語彙は使わない" are OK)
      grep -RInE '`Agent` ツール|Agent ツール' "$CURSOR_AGENTS" "$CURSOR_SKILLS" 2>/dev/null \
        | grep -v '語彙は使わない' || true
      grep -RInE '\b(opus|sonnet|Opus|Sonnet)\b' "$CURSOR_AGENTS" "$CURSOR_SKILLS" 2>/dev/null \
        | grep -vE 'role=|experimental|Observation' || true
    } | head -50
  )"
  if [ -n "$bad" ]; then
    warn "overlay hygiene check failed:"
    printf '%s\n' "$bad" >&2
    return 1
  fi
  log "overlay hygiene check passed"
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
  # Full tree copy (submodule skills need more than SKILL.md/references/scripts/assets).
  # Skip VCS metadata and binary-ish cache; adapt text via adapt_agent_body.
  find "$src" -type f \
    ! -path '*/.git/*' ! -name '.git' \
    ! -name '*.png' ! -name '*.jpg' ! -name '*.jpeg' ! -name '*.gif' ! -name '*.webp' \
    ! -name '*.woff' ! -name '*.woff2' ! -name '*.ttf' \
    | while read -r sf; do
      rel="${sf#"${src}"/}"
      mkdir -p "$(dirname "${dest}/${rel}")"
      case "$sf" in
        *.md|*.MD|*.txt|*.sh|*.bash|*.json|*.jsonc|*.toml|*.yml|*.yaml|*.sql|*.ts|*.tsx|*.js|*.jsx|*.css|*.html)
          adapt_agent_body <"$sf" >"${dest}/${rel}"
          ;;
        *)
          cp -a "$sf" "${dest}/${rel}"
          ;;
      esac
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
            print ""
            print "> **Cursor 実行時の注意**"
            print "> - 子エージェントは `Task` ツール（`subagent_type`）で起動する。Claude の `Agent` ツール語彙は使わない"
            print "> - メインエージェントがオーケストレーター。VERDICT ループ・ユーザー確認ゲート・ループカウンタはメインが保持する"
            print "> - Claude 専用機能（`TeamCreate` / Agent Teams / `~/.claude/hooks`）は Cursor では非対応のためスキップする"
            print "> - ベンダーモデル名（Cursor 側）はハードコードしない。agent overlay の `role=reasoning|coding` と Cursor UI の運用既定に従う"
            print "> - Codex CLI 橋渡し（`/codex` / `codex-runner` / `/pir2codex`）では Codex 側 model ID の明示指定は許可する"
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

verify_cursor_overlay_hygiene

log "done"
