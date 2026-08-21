#!/usr/bin/env bash
# Sync Codex config from dotfiles SSOT to Codex-native dotfiles targets.
#
# SSOT:
#   - $DOT_DIR/mcp-servers.json          (MCP servers)
#   - $DOT_DIR/AGENTS.md                 (shared global instructions)
#   - $DOT_DIR/.agents/skills/*          (shared skill definitions)
#   - $DOT_DIR/.claude/format.md         (referenced instructions)
#   - $DOT_DIR/.claude/pir-handoff.md    (referenced instructions)
#   - $DOT_DIR/.claude/user-feedback-protocol.md (referenced instructions)
#   - $DOT_DIR/.claude/ui-ux-principles.md     (referenced instructions)
#   - $DOT_DIR/.claude/agent-delegation.md     (referenced instructions)
#   - $DOT_DIR/.claude/pir2-protocol.md        (referenced instructions)
#   - $DOT_DIR/.claude/dev-server.md           (referenced instructions)
#   - $DOT_DIR/.claude/subagent-permissions.md (referenced instructions)
#   - $DOT_DIR/.claude/agents/*.md       (legacy mirror input only; disabled by default)
#
# Generated (AUTO-GENERATED, do not hand-edit):
#   - $DOT_DIR/.codex/config.toml
#   - $DOT_DIR/.codex/AGENTS.md
#   - $DOT_DIR/.codex/format.md
#   - $DOT_DIR/.codex/pir-handoff.md
#   - $DOT_DIR/.codex/user-feedback-protocol.md
#   - $DOT_DIR/.codex/ui-ux-principles.md
#   - $DOT_DIR/.codex/agent-delegation.md
#   - $DOT_DIR/.codex/pir2-protocol.md
#   - $DOT_DIR/.codex/dev-server.md
#   - $DOT_DIR/.codex/subagent-permissions.md
#   - explicitly LEGACY-GENERATED $DOT_DIR/.codex/agents/<name>.toml snapshots
#                                               (refresh only when SYNC_CODEX_LEGACY_MIRROR=1)
#   - $DOT_DIR/.codex/skills/<name>/         (legacy mirror only when SYNC_CODEX_LEGACY_MIRROR=1)
#
# Preserved native overlays (never generated):
#   - $DOT_DIR/.codex/agents/*.toml
#   - $DOT_DIR/.codex/skills/epic/
#   - $DOT_DIR/.codex/skills/worker-delegation/
#
# Re-running is idempotent.
#
# Native overlay policy:
#   Strict mirroring of .claude/agents and .agents/skills into .codex is disabled
#   by default. .agents/skills is the shared core, while .codex/agents and
#   .codex/skills are Codex-native overlays. Set SYNC_CODEX_LEGACY_MIRROR=1 only
#   when intentionally refreshing explicitly legacy-generated snapshots; it
#   never overwrites native agent overlays. The worker-
#   delegation package and its actor/model routing remain Codex-native in all
#   modes and are not copied into the shared .agents tree.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

MCP_SRC="${DOT_DIR}/mcp-servers.json"
AGENTS_SRC="${DOT_DIR}/AGENTS.md"
CLAUDE_DIR="${DOT_DIR}/.claude"
CODEX_DIR="${DOT_DIR}/.codex"
CODEX_BASE_CONFIG="${CODEX_DIR}/config.base.toml"
CODEX_CONFIG="${CODEX_DIR}/config.toml"
CODEX_AGENTS_DIR="${CODEX_DIR}/agents"
CODEX_SKILLS_DIR="${CODEX_DIR}/skills"
SHARED_SKILLS_DIR="${DOT_DIR}/.agents/skills"

log()  { echo "[sync-codex] $*"; }
warn() { echo "[sync-codex] warn: $*" >&2; }

if ! command -v jq >/dev/null 2>&1; then
  warn "jq not found, skipping sync"
  exit 0
fi

# Windows-native jq emits CRLF line terminators, which leak \r into generated
# TOML keys/values (e.g. [mcp_servers."codex\r"]) and break key matching.
# Wrap jq to strip CR from its output so generation is byte-clean on any OS.
# Defined AFTER the availability check above so `command -v jq` still tests the
# real binary, not this function.
jq() { command jq "$@" | tr -d '\r'; }

if [ ! -f "$MCP_SRC" ]; then warn "missing $MCP_SRC"; exit 0; fi
if [ ! -f "$AGENTS_SRC" ]; then warn "missing $AGENTS_SRC"; exit 0; fi
if [ ! -f "$CODEX_BASE_CONFIG" ]; then warn "missing $CODEX_BASE_CONFIG"; exit 0; fi

mkdir -p "$CODEX_DIR" "$CODEX_AGENTS_DIR" "$CODEX_SKILLS_DIR"

toml_quote() {
  jq -Rn --arg s "$1" '$s'
}

toml_array() {
  jq -c '.' | sed 's/,/, /g'
}

build_hooks_section_toml() {
  echo
  echo "# ---- AUTO-GENERATED hooks (dotfiles SSOT) ----"
  echo "[features]"
  # Codex 公式の現行フラグは `hooks = true`（`codex_hooks` は deprecated alias）
  echo "hooks = true"
  echo
  echo "[[hooks.PostToolUse]]"
  echo 'matcher = "Edit|Write|MultiEdit"'
  echo
  echo "[[hooks.PostToolUse.hooks]]"
  echo 'type = "command"'
  printf 'command = %s\n' "$(toml_quote "bash ${DOT_DIR}/etc/sync-codex.sh")"
}

# プロジェクト trust ([projects."<abs path>"]) はマシン固有の絶対パスのため共有 SSOT
# (config.base.toml) には置かない。各マシンの config.toml にだけ存在し、再生成で消えると
# Codex が毎回 trust を聞いてくるので、既存 config.toml の [projects.*] 節をそのまま引き継ぐ。
preserve_projects_toml() {
  [ -f "$CODEX_CONFIG" ] || return 0
  local projects
  projects="$(awk '
    /^\[projects\./ { cap=1; print; next }
    cap && /^# ---- AUTO-GENERATED/ { cap=0 }
    /^\[/           { cap=0 }
    cap             { print }
  ' "$CODEX_CONFIG")"
  # 末尾の空行を除去（perl で BSD/GNU 両対応。GNU sed 専用の :a/N/ba ループは macOS BSD sed で失敗する）
  projects="$(printf '%s' "$projects" | perl -0pe 's/\n+\z/\n/')"
  [ -n "$projects" ] || return 0
  echo "# ---- preserved per-machine project trust (machine-local; not in SSOT) ----"
  printf '%s\n' "$projects"
  echo
}

write_codex_config() {
  # Guard: 既存 config.toml が AUTO-GENERATED ヘッダを持たない場合は手書きと見なし保護する
  if [ -f "$CODEX_CONFIG" ] && ! head -1 "$CODEX_CONFIG" | grep -q '^# AUTO-GENERATED by dotfiles/etc/sync-codex.sh'; then
    warn "refusing to overwrite hand-edited $CODEX_CONFIG (no AUTO-GENERATED header)"
    warn "remove the file or restore the header to enable sync"
    return 0
  fi

  local tmp toml_err
  tmp="$(mktemp "${CODEX_DIR}/config.toml.tmp.XXXXXX")"

  {
    echo "# AUTO-GENERATED by dotfiles/etc/sync-codex.sh from SSOT."
    echo "# Edit .codex/config.base.toml or the shared AI workflow SSOT files instead."

    echo
    cat "$CODEX_BASE_CONFIG"
    echo
    preserve_projects_toml
    echo "# ---- AUTO-GENERATED MCP servers from mcp-servers.json ----"

    jq -r '.mcpServers | keys[]' "$MCP_SRC" | while IFS= read -r name; do
      local server type table_name command args env_json env_rendered url npx_shell_command
      server="$(jq -c --arg name "$name" '.mcpServers[$name]' "$MCP_SRC")"

      if [ "$(printf '%s' "$server" | jq -r '.codexOnly // false')" = "false" ] &&
         { [ "$(printf '%s' "$server" | jq -r '.claudeCodeOnly // false')" = "true" ] ||
           [ "$(printf '%s' "$server" | jq -r '.openCodeOnly // false')" = "true" ]; }; then
        continue
      fi

      table_name="$(toml_quote "$name")"
      type="$(printf '%s' "$server" | jq -r '.type // (if .url then "remote" else "local" end)')"

      echo
      printf '[mcp_servers.%s]\n' "$table_name"
      echo "enabled = true"

      if [ "$type" = "remote" ]; then
        url="$(printf '%s' "$server" | jq -r '.url // empty')"
        if [ -z "$url" ]; then
          warn "remote MCP server '$name' has no url, skipping"
          continue
        fi
        printf 'url = %s\n' "$(toml_quote "$url")"
        if printf '%s' "$server" | jq -e '.bearer_token_env_var? // empty' >/dev/null; then
          printf 'bearer_token_env_var = %s\n' "$(toml_quote "$(printf '%s' "$server" | jq -r '.bearer_token_env_var')")"
        fi
      else
        command="$(printf '%s' "$server" | jq -r '.command // empty')"
        if [ -z "$command" ]; then
          warn "local MCP server '$name' has no command, skipping"
          continue
        fi
        if [ "$command" = "npx" ]; then
          # Codex prepends its own helper paths and may inherit WSL Windows PATH
          # entries. npm/npx shebangs use `/usr/bin/env node`, and that lookup can
          # fail before reaching the Linux node binary. Run through bash login
          # command resolution so user shell PATH setup is applied for Codex only.
          npx_shell_command="exec npx $(printf '%s' "$server" | jq -r '.args // [] | map(@sh) | join(" ")')"
          args="$(jq -nc --arg cmd "$npx_shell_command" '["-lc", $cmd]' | toml_array)"
          printf 'command = %s\n' "$(toml_quote "bash")"
          printf 'args = %s\n' "$args"
        else
          args="$(printf '%s' "$server" | jq '.args // []' | toml_array)"
          printf 'command = %s\n' "$(toml_quote "$command")"
          printf 'args = %s\n' "$args"
        fi

        env_json="$(printf '%s' "$server" | jq -c '.env // {}')"
        if [ "$(printf '%s' "$env_json" | jq 'length')" != "0" ]; then
          # Note: rendered into an intermediate variable to avoid bash 3.2's
          # brace-expansion bug, where literal '{ ... , ... }' inside a single-
          # quoted filter nested in "$(...)" gets mis-expanded into two words.
          env_rendered="$(printf '%s' "$env_json" | jq -r 'to_entries | map("\(.key) = \(.value | @json)") | "{ " + join(", ") + " }"')"
          printf 'env = %s\n' "$env_rendered"
        fi
      fi

      jq -r --arg name "$name" '.codexToolApprovalModes[$name] // {} | to_entries[] | [.key, .value] | @tsv' "$MCP_SRC" |
        while IFS=$'\t' read -r tool_name approval_mode; do
          case "$approval_mode" in
            approve|ask|deny) ;;
            *)
              warn "invalid Codex approval mode for MCP tool '$name/$tool_name': $approval_mode"
              return 1
              ;;
          esac
          echo
          printf '[mcp_servers.%s.tools.%s]\n' "$table_name" "$(toml_quote "$tool_name")"
          printf 'approval_mode = %s\n' "$(toml_quote "$approval_mode")"
        done
    done

    build_hooks_section_toml
  } > "$tmp"

  # TOML 構文検証。macOS標準Pythonのバージョン差を避け、uvで3.13を固定する。
  if command -v uv >/dev/null 2>&1; then
    if ! toml_err="$(uv run --python 3.13 python -c 'import sys, tomllib; tomllib.load(open(sys.argv[1], "rb"))' "$tmp" 2>&1)"; then
      warn "generated TOML is invalid, aborting (tmp: $tmp)"
      warn "uv Python TOML error: $toml_err"
      return 1
    fi
  else
    warn "uv not available, skipping TOML syntax validation"
  fi

  mv -f "$tmp" "$CODEX_CONFIG"
  log "wrote $CODEX_CONFIG"
}

copy_with_header() {
  local src="$1" dst="$2" label="$3"
  [ -f "$src" ] || return 0
  {
    printf '<!-- AUTO-GENERATED by etc/sync-codex.sh from %s. Do not edit. -->\n\n' "$label"
    cat "$src"
  } > "$dst"
  log "wrote $dst"
}

copy_codexized_with_header() {
  local src="$1" dst="$2" label="$3"
  [ -f "$src" ] || return 0
  {
    printf '<!-- AUTO-GENERATED by etc/sync-codex.sh from %s. Do not edit. -->\n\n' "$label"
    codexize_stream < "$src"
  } > "$dst"
  log "wrote $dst"
}

codexize_stream() {
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
    -e 's#~/.codex/agents/\([^/ ]*\)\.md#~/.codex/agents/\1.toml#g' \
    -e 's#\.codex/agents/\([^/ ]*\)\.md#.codex/agents/\1.toml#g' \
    -e 's/Agent Teams 機能（`TeamCreate` ツールで構成する）/Codex collaboration API（`spawn_agent` と `agent_type` で構成する）/g' \
    -e 's#深さ上限5、推奨2-3#深さ上限2（`.codex/config.toml` の `[agents].max_depth = 2`、read-only explorer の1段ネストまで）#g' \
    -e 's/`Agent`[[:space:]][[:space:]]*ツール/Codex collaboration `spawn_agent` API/g' \
    -e 's/`Agent`[[:space:]][[:space:]]*tool/Codex collaboration `spawn_agent` API/g' \
    -e 's/`tools` に `Agent` を持つ/Codex collaboration API の `spawn_agent` を使う/g' \
    -e 's/tools に `Agent` を持つ/Codex collaboration API の `spawn_agent` を使う/g' \
    -e 's/`tools` に `Agent` を持たない/ネスト起動APIを持たない/g' \
    -e 's/tools に `Agent` を持たない/ネスト起動APIを持たない/g' \
    -e 's/Agent ツール/Codex collaboration `spawn_agent`/g' \
    -e 's/Agent tool/Codex collaboration `spawn_agent`/g' \
    -e 's/Agent Teams/Codex collaboration API/g' \
    -e 's/SendMessage/`send_message`/g' \
    -e 's/Skill ツール/Codex skill invocation/g' \
    -e 's/TeamCreate/`spawn_agent`/g' \
    -e 's/subagent_type/agent_type/g' \
    -e 's/サブエージェント/subagent/g' \
    -e 's/claude-sonnet-4-6/gpt-5.6-terra/g' \
    -e 's/haiku/gpt-5.6-luna/g' \
    -e 's/sonnet/gpt-5.6-terra/g' \
    -e 's/opus/gpt-5.6-terra/g' \
    -e 's/fable/gpt-5.6-terra/g'
}

codexize_pir2_protocol_stream() {
  codexize_stream |
    sed -e 's#全て `gpt-5\.6-terra` モデル。#モデル選択は各 role の `.codex/agents/<name>.toml` にある role 設定（`gpt-5.6-luna` / `gpt-5.6-terra`）に委ねる。#g'
}

sync_pir2_protocol() {
  local src="${CLAUDE_DIR}/pir2-protocol.md"
  local dst="${CODEX_DIR}/pir2-protocol.md"
  [ -f "$src" ] || return 0

  {
    printf '%s\n\n' '<!-- AUTO-GENERATED by etc/sync-codex.sh from .claude/pir2-protocol.md via the Codex-native terminology transform. Do not edit. -->'
    codexize_pir2_protocol_stream < "$src"
  } > "$dst"
  log "wrote $dst"
}

codexize_file_in_place() {
  local file="$1" tmp
  [ -f "$file" ] || return 0
  tmp="$(mktemp "${file}.tmp.XXXXXX")"
  codexize_stream < "$file" > "$tmp"
  mv -f "$tmp" "$file"
}

build_codex_agents_md() {
  local src="$AGENTS_SRC"
  local dst="${CODEX_DIR}/AGENTS.md"
  [ -f "$src" ] || return 0

  {
    cat <<'HEADER'
<!-- AUTO-GENERATED by etc/sync-codex.sh from AGENTS.md.
     Do not edit by hand. Re-run: bash etc/sync-codex.sh
     Codex reads AGENTS.md. This file is generated in Codex-native format. -->

HEADER
    cat "$src"
  } > "$dst"

  log "wrote $dst"
}

quote_yaml_scalar() {
  local raw="$1"
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
    explorer|implementer)
      printf '%s' "gpt-5.6-luna"
      ;;
    *)
      printf '%s' "gpt-5.6-terra"
      ;;
  esac
}

codex_agent_reasoning_effort() {
  case "$1" in
    explorer)
      printf '%s' "low"
      ;;
    implementer|refactor-advisor|sentinel-iac|tester)
      printf '%s' "medium"
      ;;
    *)
      printf '%s' "high"
      ;;
  esac
}

convert_agent_to_toml() {
  local src="$1" dst="$2" name description body model reasoning_effort
  name="$(extract_agent_frontmatter_value "$src" "name")"
  description="$(extract_agent_frontmatter_value "$src" "description")"
  if [ -z "$name" ]; then
    name="$(basename "$src" .md)"
  fi
  if [ -z "$description" ]; then
    description="Codex custom agent generated from $(basename "$src")."
  fi
  description="$(printf '%s' "$description" | codexize_stream)"
  body="$(extract_agent_body "$src" | codexize_stream)"
  model="$(codex_agent_model "$name")"
  reasoning_effort="$(codex_agent_reasoning_effort "$name")"

  {
    echo "# LEGACY-GENERATED by etc/sync-codex.sh from .claude/agents/$(basename "$src") (legacy snapshot; not a native overlay). Do not edit."
    printf 'name = %s\n' "$(toml_quote "$name")"
    printf 'description = %s\n' "$(toml_quote "$description")"
    printf 'model = %s\n' "$(toml_quote "$model")"
    printf 'model_reasoning_effort = %s\n' "$(toml_quote "$reasoning_effort")"
    printf 'developer_instructions = %s\n' "$(printf '%s' "$body" | jq -Rs .)"
  } > "$dst"

  log "wrote $dst"
}

is_legacy_generated_agent() {
  [ -f "$1" ] &&
    head -1 "$1" | grep -q '^# LEGACY-GENERATED by etc/sync-codex.sh from \.claude/agents/'
}

sync_agents() {
  local src_dir="${CLAUDE_DIR}/agents"
  local dst src
  [ -d "$src_dir" ] || return 0

  # .codex/agents/*.toml are editable native overlays. Legacy mode only
  # refreshes targets that were explicitly marked as legacy-generated; it
  # never creates, deletes, or overwrites a native overlay.
  for dst in "$CODEX_AGENTS_DIR"/*.toml; do
    [ -f "$dst" ] || continue
    if ! is_legacy_generated_agent "$dst"; then
      log "preserved native agent overlay: $(basename "$dst")"
      continue
    fi

    src="${src_dir}/$(basename "$dst" .toml).md"
    if [ ! -f "$src" ]; then
      warn "legacy-generated agent source is missing; preserved snapshot: $(basename "$dst")"
      continue
    fi
    convert_agent_to_toml "$src" "$dst"
  done
}

codexize_markdown_tree() {
  local dir="$1"
  find "$dir" -type f -name '*.md' | while IFS= read -r file; do
    codexize_file_in_place "$file"
  done
}

mirror_skill_to_dir() {
  local src="$1" root="$2" marker_name="$3" label="$4"
  local name dst marker
  name="$(basename "$src")"
  dst="${root}/${name}"
  marker="${dst}/${marker_name}"

  # These overlays are Codex-native source-controlled assets. Never adopt,
  # regenerate, or remove them from a shared/Claude skill source, even when
  # legacy mirror mode is explicitly enabled.
  if [ "$root" = "$CODEX_SKILLS_DIR" ]; then
    case "$name" in
      epic|worker-delegation)
        if [ -d "$dst" ]; then
          log "preserved native Codex skill: $name"
        else
          warn "missing native Codex skill: $dst (not generated from $src)"
        fi
        return 0
        ;;
    esac
  fi

  if [ -e "$dst" ] && [ ! -f "$marker" ] &&
     [ ! -f "$dst/.codex-generated-from-claude" ] &&
     [ ! -f "$dst/.generated-from-claude" ]; then
    if diff -qr "$src" "$dst" >/dev/null 2>&1; then
      log "adopting existing mirrored skill as generated: $dst"
    else
      warn "not overwriting non-generated skill: $dst"
      return 0
    fi
  fi

  rm -rf "$dst"
  mkdir -p "$dst"
  cp -a "$src"/. "$dst"/
  rm -rf "$dst/.git"
  normalize_codex_skill_frontmatter "$dst/SKILL.md"
  codexize_markdown_tree "$dst"
  touch "$marker"
  log "${label} skill: $name"
}

cleanup_generated_skill_orphans() {
  local root="$1" marker_name="$2" src_dir="$3" label="$4"
  local d
  for d in "$root"/*; do
    [ -d "$d" ] || continue
    [ -f "$d/$marker_name" ] || continue
    if [ ! -d "${src_dir}/$(basename "$d")" ]; then
      rm -rf "$d"
      log "removed orphan ${label} skill: $(basename "$d")"
    fi
  done
}

sync_skills() {
  local src_dir="$SHARED_SKILLS_DIR"
  [ -d "$src_dir" ] || return 0

  for d in "$src_dir"/*; do
    [ -d "$d" ] || continue
    mirror_skill_to_dir "$d" "$CODEX_SKILLS_DIR" ".codex-generated-from-shared" "Codex mirror"
  done

  cleanup_generated_skill_orphans "$CODEX_SKILLS_DIR" ".codex-generated-from-shared" "$src_dir" "Codex mirror"
  cleanup_generated_skill_orphans "$CODEX_SKILLS_DIR" ".codex-generated-from-claude" "$src_dir" "legacy Codex mirror"
  cleanup_generated_skill_orphans "$CODEX_SKILLS_DIR" ".generated-from-claude" "$src_dir" "legacy Codex mirror"
}

sync_legacy_mirrors_if_requested() {
  if [ "${SYNC_CODEX_LEGACY_MIRROR:-0}" != "1" ]; then
    log "skipped .codex/agents strict mirror (native overlay; set SYNC_CODEX_LEGACY_MIRROR=1 for legacy regeneration)"
    log "skipped .codex/skills strict mirror (shared core lives in .agents/skills; .codex/skills is native overlay)"
    return 0
  fi

  warn "SYNC_CODEX_LEGACY_MIRROR=1 is enabled; refreshing explicit legacy snapshots while preserving native overlays"
  sync_agents
  sync_skills
}

# Regenerate only the protocol when validating its Codex-specific adapter
# transform, without touching other generated adapters in a working tree.
if [ "${SYNC_CODEX_PROTOCOL_ONLY:-0}" = "1" ]; then
  sync_pir2_protocol
  log "done (protocol only)"
  exit 0
fi

write_codex_config
build_codex_agents_md
copy_codexized_with_header "${CLAUDE_DIR}/format.md" "${CODEX_DIR}/format.md" ".claude/format.md"
copy_codexized_with_header "${CLAUDE_DIR}/pir-handoff.md" "${CODEX_DIR}/pir-handoff.md" ".claude/pir-handoff.md"
copy_codexized_with_header "${CLAUDE_DIR}/user-feedback-protocol.md" "${CODEX_DIR}/user-feedback-protocol.md" ".claude/user-feedback-protocol.md"
copy_codexized_with_header "${CLAUDE_DIR}/ui-ux-principles.md" "${CODEX_DIR}/ui-ux-principles.md" ".claude/ui-ux-principles.md"
copy_codexized_with_header "${CLAUDE_DIR}/agent-delegation.md" "${CODEX_DIR}/agent-delegation.md" ".claude/agent-delegation.md"
sync_pir2_protocol
copy_codexized_with_header "${CLAUDE_DIR}/dev-server.md" "${CODEX_DIR}/dev-server.md" ".claude/dev-server.md"
copy_codexized_with_header "${CLAUDE_DIR}/subagent-permissions.md" "${CODEX_DIR}/subagent-permissions.md" ".claude/subagent-permissions.md"
sync_legacy_mirrors_if_requested

log "done"
