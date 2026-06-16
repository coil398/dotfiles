#!/usr/bin/env bash
# Sync Codex config from dotfiles SSOT to dotfiles/.codex/.
#
# SSOT:
#   - $DOT_DIR/mcp-servers.json          (MCP servers)
#   - $DOT_DIR/.claude/settings.json     (permissions deny → filesystem section)
#   - $DOT_DIR/.claude/CLAUDE.md         (global instructions)
#   - $DOT_DIR/.claude/format.md         (referenced instructions)
#   - $DOT_DIR/.claude/pir-handoff.md    (referenced instructions)
#   - $DOT_DIR/.claude/agent-delegation.md     (referenced instructions)
#   - $DOT_DIR/.claude/pir2-protocol.md        (referenced instructions)
#   - $DOT_DIR/.claude/dev-server.md           (referenced instructions)
#   - $DOT_DIR/.claude/subagent-permissions.md (referenced instructions)
#   - $DOT_DIR/.claude/agents/*.md       (agent definitions, mirrored)
#   - $DOT_DIR/.claude/skills/*          (skill definitions, mirrored)
#
# Generated (AUTO-GENERATED, do not hand-edit):
#   - $DOT_DIR/.codex/config.toml
#   - $DOT_DIR/.codex/AGENTS.md
#   - $DOT_DIR/.codex/format.md
#   - $DOT_DIR/.codex/pir-handoff.md
#   - $DOT_DIR/.codex/agent-delegation.md
#   - $DOT_DIR/.codex/pir2-protocol.md
#   - $DOT_DIR/.codex/dev-server.md
#   - $DOT_DIR/.codex/subagent-permissions.md
#   - $DOT_DIR/.codex/agents/<name>.md
#   - $DOT_DIR/.codex/skills/<name>/
#
# Re-running is idempotent.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

MCP_SRC="${DOT_DIR}/mcp-servers.json"
CLAUDE_DIR="${DOT_DIR}/.claude"
CODEX_DIR="${DOT_DIR}/.codex"
CODEX_BASE_CONFIG="${CODEX_DIR}/config.base.toml"
CODEX_CONFIG="${CODEX_DIR}/config.toml"
CODEX_AGENTS_DIR="${CODEX_DIR}/agents"
CODEX_SKILLS_DIR="${CODEX_DIR}/skills"
SETTINGS_SRC="${CLAUDE_DIR}/settings.json"

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
if [ ! -f "$CODEX_BASE_CONFIG" ]; then warn "missing $CODEX_BASE_CONFIG"; exit 0; fi

mkdir -p "$CODEX_DIR" "$CODEX_AGENTS_DIR" "$CODEX_SKILLS_DIR"

toml_quote() {
  jq -Rn --arg s "$1" '$s'
}

toml_array() {
  jq -c '.' | sed 's/,/, /g'
}

_extract_deny_patterns() {
  [ -f "$SETTINGS_SRC" ] || return 0
  # `Read(<glob>)` の glob 部分のみ抽出。
  # 文字列スライス `[5:-1]` で先頭 5 文字 ("Read(") と末尾 1 文字 (")") を除去する。
  jq -r '
    .permissions.deny // [] |
    map(select(startswith("Read("))) |
    map(.[5:-1]) |
    .[]
  ' "$SETTINGS_SRC"
}

# `default_permissions` is a TOML top-level key. It must appear before any
# `[section]` header, otherwise TOML attaches it to the most recent table
# (e.g. `mcp_servers."sequential-thinking".default_permissions`), which then
# fails deserialization much later with a confusing untagged-enum error.
build_default_permissions_line_toml() {
  local deny_patterns
  deny_patterns="$(_extract_deny_patterns)"
  [ -z "$deny_patterns" ] && return 0
  echo
  echo "# ---- AUTO-GENERATED permissions selector (codex 0.128.0+) ----"
  echo 'default_permissions = "dotfiles-default"'
}

build_permissions_section_toml() {
  local deny_patterns
  deny_patterns="$(_extract_deny_patterns)"
  [ -z "$deny_patterns" ] && return 0

  echo
  echo "# ---- AUTO-GENERATED filesystem deny from .claude/settings.json ----"
  # codex 0.131.0+ schema (verified empirically against codex 0.138.0 on this
  # machine; see also https://developers.openai.com/codex/permissions and
  # openai/codex Discussion #23920):
  #   - The profile referenced by `default_permissions` is defined here.
  #   - The scoped-root key is `":workspace_roots"`. The older `":project_roots"`
  #     is NOT recognized by 0.131.0+ and is silently ignored with a warning
  #     ("Configured filesystem path :project_roots is not recognized ... and
  #     will be ignored"). Earlier codex (~0.128.x) used `:project_roots`.
  #   - The access value for deny rules is `"deny"`. The old `"none"` value was
  #     dropped as a breaking change in 0.131.0. Feeding `"none"` to a glob path
  #     makes codex abort at startup with the misleading message:
  #       "filesystem glob path `...` only supports `deny` access; use an exact
  #        path or trailing `/**` for `deny` subtree access".
  #     (The message fires for ANY non-`deny` value on a glob path; switching to
  #     `"deny"` resolves it. Both trailing-`/**` subtree globs like
  #     `**/node_modules/**` and file globs like `**/*.lock` load reliably as
  #     `"deny"` — no `glob_scan_max_depth` needed.)
  #   - Parent table `[permissions.<name>]` is declared explicitly.
  #   - Skip emitting the intermediate `[permissions.<name>.filesystem]` table on
  #     its own line — when present without any direct keys it tickles an
  #     `untagged enum FilesystemPermissionToml` deserialize error. Go straight
  #     to `[permissions.<name>.filesystem.":workspace_roots"]`.
  #
  # NOTE: codex merges the project-local `<cwd>/.codex/config.toml` on top of
  # `$CODEX_HOME/config.toml`. Inside this dotfiles repo the same generated file
  # is loaded as both, so a stale/invalid block here breaks `codex` even when
  # run from the repo root. Keep this section valid for the installed codex.
  echo '[permissions.dotfiles-default]'
  echo
  echo '[permissions.dotfiles-default.filesystem.":workspace_roots"]'
  echo '"." = "write"'
  while IFS= read -r glob; do
    [ -z "$glob" ] && continue
    printf '%s = "deny"\n' "$(toml_quote "$glob")"
  done <<< "$deny_patterns"
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
    echo "# Edit .codex/config.base.toml or the Claude-side SSOT files instead."

    # Top-level keys must be written before any `[section]` header. We emit
    # `default_permissions` here (before base.toml, which starts top-level keys
    # then opens `[projects.*]` and other tables).
    build_default_permissions_line_toml

    echo
    cat "$CODEX_BASE_CONFIG"
    echo
    echo "# ---- AUTO-GENERATED MCP servers from mcp-servers.json ----"

    jq -r '.mcpServers | keys[]' "$MCP_SRC" | while IFS= read -r name; do
      local server type table_name command args env_json env_rendered url
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
        args="$(printf '%s' "$server" | jq '.args // []' | toml_array)"
        printf 'command = %s\n' "$(toml_quote "$command")"
        printf 'args = %s\n' "$args"

        env_json="$(printf '%s' "$server" | jq -c '.env // {}')"
        if [ "$(printf '%s' "$env_json" | jq 'length')" != "0" ]; then
          # Note: rendered into an intermediate variable to avoid bash 3.2's
          # brace-expansion bug, where literal '{ ... , ... }' inside a single-
          # quoted filter nested in "$(...)" gets mis-expanded into two words.
          env_rendered="$(printf '%s' "$env_json" | jq -r 'to_entries | map("\(.key) = \(.value | @json)") | "{ " + join(", ") + " }"')"
          printf 'env = %s\n' "$env_rendered"
        fi
      fi
    done

    build_permissions_section_toml
    build_hooks_section_toml
  } > "$tmp"

  # TOML 構文検証（python3 が実際に動作する場合のみ）。
  # Windows の App Execution Alias スタブは command -v では「あり」と判定されるが
  # 実行すると非ゼロ終了するため、空実行で実際に動くかを確認する。
  if python3 -c '' >/dev/null 2>&1; then
    if ! toml_err="$(python3 -c 'import sys, tomllib; tomllib.load(open(sys.argv[1], "rb"))' "$tmp" 2>&1)"; then
      warn "generated TOML is invalid, aborting (tmp: $tmp)"
      warn "python3 error: $toml_err"
      return 1
    fi
  else
    warn "python3 not available (or non-functional), skipping TOML syntax validation"
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

sync_agents() {
  local src_dir="${CLAUDE_DIR}/agents"
  [ -d "$src_dir" ] || return 0

  for f in "$src_dir"/*.md; do
    [ -f "$f" ] || continue
    copy_with_header "$f" "${CODEX_AGENTS_DIR}/$(basename "$f")" ".claude/agents/$(basename "$f")"
  done

  for f in "$CODEX_AGENTS_DIR"/*.md; do
    [ -f "$f" ] || continue
    if ! head -1 "$f" | grep -q '^<!-- AUTO-GENERATED by etc/sync-codex.sh'; then
      continue
    fi
    if [ ! -f "${src_dir}/$(basename "$f")" ]; then
      rm -f "$f"
      log "removed orphan agent: $(basename "$f")"
    fi
  done
}

sync_skills() {
  local src_dir="${CLAUDE_DIR}/skills"
  [ -d "$src_dir" ] || return 0

  for d in "$src_dir"/*; do
    [ -d "$d" ] || continue
    local name dst marker
    name="$(basename "$d")"
    dst="${CODEX_SKILLS_DIR}/${name}"
    marker="${dst}/.codex-generated-from-claude"

    if [ -e "$dst" ] && [ ! -f "$marker" ]; then
      warn "not overwriting non-generated skill: $dst"
      continue
    fi

    rm -rf "$dst"
    mkdir -p "$dst"
    cp -a "$d"/. "$dst"/
    rm -rf "$dst/.git"
    normalize_codex_skill_frontmatter "$dst/SKILL.md"
    touch "$marker"
    log "mirrored skill: $name"
  done

  for d in "$CODEX_SKILLS_DIR"/*; do
    [ -d "$d" ] || continue
    [ -f "$d/.codex-generated-from-claude" ] || continue
    if [ ! -d "${src_dir}/$(basename "$d")" ]; then
      rm -rf "$d"
      log "removed orphan skill: $(basename "$d")"
    fi
  done
}

write_codex_config
copy_with_header "${CLAUDE_DIR}/CLAUDE.md" "${CODEX_DIR}/AGENTS.md" ".claude/CLAUDE.md"
copy_with_header "${CLAUDE_DIR}/format.md" "${CODEX_DIR}/format.md" ".claude/format.md"
copy_with_header "${CLAUDE_DIR}/pir-handoff.md" "${CODEX_DIR}/pir-handoff.md" ".claude/pir-handoff.md"
copy_with_header "${CLAUDE_DIR}/agent-delegation.md" "${CODEX_DIR}/agent-delegation.md" ".claude/agent-delegation.md"
copy_with_header "${CLAUDE_DIR}/pir2-protocol.md" "${CODEX_DIR}/pir2-protocol.md" ".claude/pir2-protocol.md"
copy_with_header "${CLAUDE_DIR}/dev-server.md" "${CODEX_DIR}/dev-server.md" ".claude/dev-server.md"
copy_with_header "${CLAUDE_DIR}/subagent-permissions.md" "${CODEX_DIR}/subagent-permissions.md" ".claude/subagent-permissions.md"
sync_agents
sync_skills

log "done"
