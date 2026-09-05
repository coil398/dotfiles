#!/usr/bin/env bash
# Sync Codex config from dotfiles SSOT to Codex-native dotfiles targets.
#
# SSOT:
#   - $DOT_DIR/mcp-servers.json          (MCP servers)
#   - $DOT_DIR/AGENTS.md                 (shared global instructions)
#   - $DOT_DIR/.codex/codex-native-supplement.md (Codex-native global supplement)
#   - $DOT_DIR/.agents/skills/*          (shared skill definitions)
#   - $DOT_DIR/.claude/format.md         (referenced instructions)
#   - $DOT_DIR/.codex/skills/pir2/references/handoff-protocol.md (native handoff source)
#   - $DOT_DIR/.claude/user-feedback-protocol.md (referenced instructions)
#   - $DOT_DIR/.claude/ui-ux-principles.md     (referenced instructions)
#   - $DOT_DIR/.codex/skills/pir2/references/protocol.md (native workflow source)
#   - $DOT_DIR/.claude/dev-server.md           (referenced instructions)
#   - $DOT_DIR/.claude/subagent-permissions.md (referenced instructions)
#   - $DOT_DIR/.claude/agents/*.md       (legacy mirror input only; disabled by default)
#
# Generated (AUTO-GENERATED, do not hand-edit):
#   - $DOT_DIR/.codex/config.toml
#   - $DOT_DIR/.codex/AGENTS.md           (AGENTS.md + Codex native supplement)
#   - $DOT_DIR/.codex/format.md
#   - $DOT_DIR/.codex/pir-handoff.md
#   - $DOT_DIR/.codex/user-feedback-protocol.md
#   - $DOT_DIR/.codex/ui-ux-principles.md
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
#   - $DOT_DIR/.codex/agent-delegation.md (Codex-native support document)
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
CODEX_NATIVE_SUPPLEMENT_SRC="${CODEX_DIR}/codex-native-supplement.md"
CODEX_BASE_CONFIG="${CODEX_DIR}/config.base.toml"
CODEX_CONFIG="${CODEX_DIR}/config.toml"
CODEX_AGENTS_DIR="${CODEX_DIR}/agents"
CODEX_SKILLS_DIR="${CODEX_DIR}/skills"
SHARED_SKILLS_DIR="${DOT_DIR}/.agents/skills"

log()  { echo "[sync-codex] $*" >&2; }
warn() { echo "[sync-codex] warn: $*" >&2; }

if ! command -v jq >/dev/null 2>&1; then
  warn "required dependency missing: jq"
  exit 1
fi

# Windows-native jq emits CRLF line terminators, which leak \r into generated
# TOML keys/values (e.g. [mcp_servers."codex\r"]) and break key matching.
# Wrap jq to strip CR from its output so generation is byte-clean on any OS.
# Defined AFTER the availability check above so `command -v jq` still tests the
# real binary, not this function.
jq() { command jq "$@" | tr -d '\r'; }

if [ ! -f "$MCP_SRC" ]; then warn "required SSOT missing: $MCP_SRC"; exit 1; fi
if [ ! -f "$AGENTS_SRC" ]; then warn "required SSOT missing: $AGENTS_SRC"; exit 1; fi
if [ ! -f "$CODEX_NATIVE_SUPPLEMENT_SRC" ]; then warn "required SSOT missing: $CODEX_NATIVE_SUPPLEMENT_SRC"; exit 1; fi
if [ ! -f "$CODEX_BASE_CONFIG" ]; then warn "required SSOT missing: $CODEX_BASE_CONFIG"; exit 1; fi
if ! command -v uv >/dev/null 2>&1; then
  warn "required dependency missing: uv (TOML validation requires Python 3.13)"
  exit 1
fi

mkdir -p "$CODEX_DIR" "$CODEX_AGENTS_DIR" "$CODEX_SKILLS_DIR"

toml_quote() {
  jq -Rn --arg s "$1" '$s'
}

toml_array() {
  jq -c '.' | sed 's/,/, /g'
}

shell_quote() {
  # Bash's %q output is consumed by the command hook's shell.  Keep this
  # separate from toml_quote: shell quoting protects the path first, then the
  # complete command is encoded as a TOML string.
  printf '%q' "$1"
}

generated_header_present() {
  local file="$1"
  [ -f "$file" ] &&
    head -n 5 "$file" | grep -Eq '(AUTO-GENERATED|LEGACY-GENERATED) by (dotfiles/)?etc/sync-codex\.sh'
}

resolve_link_target() {
  local link="$1" raw parent
  raw="$(readlink "$link")" || return 1
  case "$raw" in
    /*) printf '%s' "$raw" ;;
    *)
      parent="$(cd -P "$(dirname "$link")" && pwd)" || return 1
      printf '%s/%s' "$parent" "$raw"
      ;;
  esac
}

publication_target() {
  local dest="$1" target hops=0

  if [ -d "$dest" ]; then
    warn "refusing to publish generated output to directory: $dest"
    return 1
  fi
  if [ ! -L "$dest" ]; then
    printf '%s' "$dest"
    return 0
  fi

  target="$dest"
  while [ -L "$target" ]; do
    hops=$((hops + 1))
    if [ "$hops" -gt 32 ]; then
      warn "refusing to publish through symlink cycle: $dest"
      return 1
    fi
    target="$(resolve_link_target "$target")" || {
      warn "refusing to resolve generated symlink: $dest"
      return 1
    }
  done

  if ! generated_header_present "$target"; then
    warn "refusing to overwrite non-generated symlink target: $dest -> $target"
    return 1
  fi
  printf '%s' "$target"
}

publish_temp() {
  local tmp="$1" dest="$2" target

  if ! target="$(publication_target "$dest")"; then
    rm -f "$tmp"
    return 1
  fi
  if [ -f "$target" ] && cmp -s "$tmp" "$target"; then
    rm -f "$tmp"
    return 0
  fi
  if ! mv -f "$tmp" "$target"; then
    rm -f "$tmp"
    warn "failed to publish generated output: $dest"
    return 1
  fi
}

atomic_publish() {
  # Callers must materialize the complete producer output and check its
  # status before handing the temporary file to this publication step.
  local dest="$1" tmp="$2"
  publish_temp "$tmp" "$dest"
}

build_hooks_section_toml() {
  local shell_path hook_command
  if ! shell_path="$(shell_quote "${DOT_DIR}/etc/sync-codex.sh")"; then
    return 1
  fi
  if ! hook_command="$(toml_quote "bash ${shell_path}")"; then
    warn "failed to encode Codex hook command"
    return 1
  fi
  echo
  echo "# ---- AUTO-GENERATED hooks (dotfiles SSOT) ----"
  echo "[[hooks.PostToolUse]]"
  echo 'matcher = "Edit|Write|MultiEdit"'
  echo
  echo "[[hooks.PostToolUse.hooks]]"
  echo 'type = "command"'
  printf 'command = %s\n' "$hook_command"
}

# Return a stable absolute path for an existing file.  Cwd::abs_path is already
# a required Perl core dependency of the Codex adapter tooling and resolves the
# final file symlink as well as symlinked parent directories.
canonical_file_path() {
  perl -MCwd=abs_path -e '
    my $path = abs_path($ARGV[0]);
    defined $path or exit 1;
    print $path;
  ' "$1"
}

skill_path_seen() {
  local needle="$1" seen="$2" item
  while IFS= read -r item; do
    [ "$item" = "$needle" ] && return 0
  done <<< "$seen"
  return 1
}

# Preserve user-owned [[skills.config]] tables while replacing only the block
# emitted by this adapter.  The explicit end marker makes generated and
# user-owned tables unambiguous.  Existing marker-only blocks are treated as
# the adapter's legacy generated block during one migration pass.
preserve_skills_config_toml() {
  PRESERVED_SKILL_PATHS=""
  [ -f "$CODEX_CONFIG" ] || return 0
  local skills_config path_line raw_path skill_path canonical
  skills_config="$(awk '
    /^# ---- AUTO-GENERATED shared skill suppression/ { generated=1; capture=0; next }
    /^# ---- END AUTO-GENERATED shared skill suppression/ { generated=0; capture=0; next }
    generated {
      if ($0 ~ /^\[\[skills\.config\]\]$/) { next }
      if ($0 ~ /^\[/) { generated=0 }
      else { next }
    }
    /^\[\[skills\.config\]\]$/ { capture=1; print; next }
    capture && /^\[/ { capture=0 }
    capture { print }
  ' "$CODEX_CONFIG")"
  skills_config="$(printf '%s' "$skills_config" | perl -0pe 's/\n+\z/\n/')"
  if [ -n "$skills_config" ]; then
    while IFS= read -r path_line; do
      raw_path="${path_line#path = }"
      case "$raw_path" in
        \"*\") skill_path="$(printf '%s' "$raw_path" | jq -r . 2>/dev/null || true)" ;;
        \'*\') skill_path="${raw_path:1:${#raw_path}-2}" ;;
        *) continue ;;
      esac
      [ -n "$skill_path" ] || continue
      if [ -f "$skill_path" ]; then
        canonical="$(canonical_file_path "$skill_path")" || canonical="$skill_path"
      else
        canonical="$skill_path"
      fi
      PRESERVED_SKILL_PATHS="${PRESERVED_SKILL_PATHS}${PRESERVED_SKILL_PATHS:+$'\n'}${canonical}"
    done <<< "$(printf '%s' "$skills_config" | awk '/^path[[:space:]]*=/ { sub(/^[^=]*=[[:space:]]*/, ""); print }')"
  fi
  [ -n "$skills_config" ] || return 0
  echo "# ---- preserved per-machine skills configuration (user-owned) ----"
  printf '%s\n' "$skills_config"
  echo
}

# Disable a shared skill only when the same skill is already present as a
# native Codex skill.  The two explicit shared roots are machine-aware; no
# unrelated filesystem roots are searched.  Canonical paths deduplicate a
# repository skill and a home copy when one is a symlink to the other.
build_skill_config_section_toml() {
  local native_skill_file name shared_root shared_file canonical encoded_path count=0
  local seen="${PRESERVED_SKILL_PATHS:-}"
  local -a shared_roots=("$SHARED_SKILLS_DIR")
  if [ -n "${HOME:-}" ]; then
    shared_roots+=("${HOME}/.agents/skills")
  fi

  for native_skill_file in "$CODEX_SKILLS_DIR"/*/SKILL.md; do
    [ -f "$native_skill_file" ] || continue
    name="$(basename "$(dirname "$native_skill_file")")"

    for shared_root in "${shared_roots[@]}"; do
      shared_file="${shared_root}/${name}/SKILL.md"
      [ -f "$shared_file" ] || continue
      canonical="$(canonical_file_path "$shared_file")" || continue
      if skill_path_seen "$canonical" "$seen"; then
        continue
      fi

      if [ "$count" -eq 0 ]; then
        echo
        echo "# ---- AUTO-GENERATED shared skill suppression (native Codex wins) ----"
      fi
      if ! encoded_path="$(toml_quote "$canonical")"; then
        warn "failed to encode shared skill path: $canonical"
        return 1
      fi
      printf '[[skills.config]]\npath = %s\nenabled = false\n\n' "$encoded_path"
      seen="${seen}${seen:+$'\n'}${canonical}"
      count=$((count + 1))
    done
  done
  if [ "$count" -gt 0 ]; then
    echo "# ---- END AUTO-GENERATED shared skill suppression ----"
    echo
  fi
}

# Hook trust is runtime state, not generated source. Preserve every existing
# [hooks.state.*] table verbatim so Codex can re-check the stored hash against
# the current hook. Never synthesize a trusted_hash for a new or changed hook.
preserve_hooks_state_toml() {
  [ -f "$CODEX_CONFIG" ] || return 0
  local hooks_state
  hooks_state="$(awk '
    /^\[hooks\.state(\.|\])/ { capture=1; print; next }
    capture && /^\[/ { capture=0 }
    capture { print }
  ' "$CODEX_CONFIG")"
  # 末尾の空行を除去（perl で BSD/GNU 両対応）。
  hooks_state="$(printf '%s' "$hooks_state" | perl -0pe 's/\n+\z/\n/')"
  [ -n "$hooks_state" ] || return 0
  echo "# ---- preserved per-machine hook trust state (runtime-owned; not generated) ----"
  printf '%s\n' "$hooks_state"
  echo
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
      local npx_args bearer_token env_length
      local codex_only claude_code_only open_code_only
      local encoded_url encoded_bearer_token encoded_command
      local encoded_tool_name encoded_approval_mode
      if ! server="$(jq -c --arg name "$name" '.mcpServers[$name]' "$MCP_SRC")"; then
        warn "failed to read MCP server '$name'"
        return 1
      fi

      if ! codex_only="$(printf '%s' "$server" | jq -r '.codexOnly // false')" ||
         ! claude_code_only="$(printf '%s' "$server" | jq -r '.claudeCodeOnly // false')" ||
         ! open_code_only="$(printf '%s' "$server" | jq -r '.openCodeOnly // false')"; then
        warn "failed to inspect MCP server '$name'"
        return 1
      fi
      if [ "$codex_only" = "false" ] &&
         { [ "$claude_code_only" = "true" ] || [ "$open_code_only" = "true" ]; }; then
        continue
      fi

      if ! table_name="$(toml_quote "$name")"; then
        warn "failed to encode MCP server name '$name'"
        return 1
      fi
      if ! type="$(printf '%s' "$server" | jq -r '.type // (if .url then "remote" else "local" end)')"; then
        warn "failed to inspect MCP server '$name' type"
        return 1
      fi

      echo
      printf '[mcp_servers.%s]\n' "$table_name"
      echo "enabled = true"

      if [ "$type" = "remote" ]; then
        if ! url="$(printf '%s' "$server" | jq -r '.url // empty')"; then
          warn "failed to read remote MCP server '$name' url"
          return 1
        fi
        if [ -z "$url" ]; then
          warn "remote MCP server '$name' has no url, skipping"
          continue
        fi
        if ! encoded_url="$(toml_quote "$url")"; then
          warn "failed to encode remote MCP server '$name' url"
          return 1
        fi
        printf 'url = %s\n' "$encoded_url"
        if printf '%s' "$server" | jq -e '.bearer_token_env_var? // empty' >/dev/null; then
          if ! bearer_token="$(printf '%s' "$server" | jq -r '.bearer_token_env_var')" ||
             ! encoded_bearer_token="$(toml_quote "$bearer_token")"; then
            warn "failed to encode remote MCP server '$name' bearer token environment variable"
            return 1
          fi
          printf 'bearer_token_env_var = %s\n' "$encoded_bearer_token"
        fi
      else
        if ! command="$(printf '%s' "$server" | jq -r '.command // empty')"; then
          warn "failed to read local MCP server '$name' command"
          return 1
        fi
        if [ -z "$command" ]; then
          warn "local MCP server '$name' has no command, skipping"
          continue
        fi
        if [ "$command" = "npx" ]; then
          # Codex prepends its own helper paths and may inherit WSL Windows PATH
          # entries. npm/npx shebangs use `/usr/bin/env node`, and that lookup can
          # fail before reaching the Linux node binary. Run through bash login
          # command resolution so user shell PATH setup is applied for Codex only.
          if ! npx_args="$(printf '%s' "$server" | jq -r '.args // [] | map(@sh) | join(" ")')"; then
            warn "failed to read npx MCP server '$name' arguments"
            return 1
          fi
          npx_shell_command="exec npx $npx_args"
          if ! args="$(jq -nc --arg cmd "$npx_shell_command" '["-lc", $cmd]' | toml_array)"; then
            warn "failed to encode npx MCP server '$name' arguments"
            return 1
          fi
          if ! encoded_command="$(toml_quote "bash")"; then
            warn "failed to encode npx MCP server '$name' command"
            return 1
          fi
          printf 'command = %s\n' "$encoded_command"
          printf 'args = %s\n' "$args"
        else
          if ! args="$(printf '%s' "$server" | jq '.args // []' | toml_array)"; then
            warn "failed to encode MCP server '$name' arguments"
            return 1
          fi
          if ! encoded_command="$(toml_quote "$command")"; then
            warn "failed to encode MCP server '$name' command"
            return 1
          fi
          printf 'command = %s\n' "$encoded_command"
          printf 'args = %s\n' "$args"
        fi

        if ! env_json="$(printf '%s' "$server" | jq -c '.env // {}')" ||
           ! env_length="$(printf '%s' "$env_json" | jq 'length')"; then
          warn "failed to read MCP server '$name' environment"
          return 1
        fi
        if [ "$env_length" != "0" ]; then
          # Note: rendered into an intermediate variable to avoid bash 3.2's
          # brace-expansion bug, where literal '{ ... , ... }' inside a single-
          # quoted filter nested in "$(...)" gets mis-expanded into two words.
          if ! env_rendered="$(printf '%s' "$env_json" | jq -r 'to_entries | map("\(.key) = \(.value | @json)") | "{ " + join(", ") + " }"')"; then
            warn "failed to encode MCP server '$name' environment"
            return 1
          fi
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
          if ! encoded_tool_name="$(toml_quote "$tool_name")" ||
             ! encoded_approval_mode="$(toml_quote "$approval_mode")"; then
            warn "failed to encode Codex approval mode for MCP tool '$name/$tool_name'"
            return 1
          fi
          printf '[mcp_servers.%s.tools.%s]\n' "$table_name" "$encoded_tool_name"
          printf 'approval_mode = %s\n' "$encoded_approval_mode"
        done
    done

    preserve_skills_config_toml
    build_skill_config_section_toml
    build_hooks_section_toml
    preserve_hooks_state_toml
  } > "$tmp"

  # TOML 構文検証。macOS標準Pythonのバージョン差を避け、uvで3.13を固定する。
  if ! toml_err="$(uv run --python 3.13 python -c 'import sys, tomllib; tomllib.load(open(sys.argv[1], "rb"))' "$tmp" 2>&1)"; then
    warn "generated TOML is invalid, aborting (tmp: $tmp)"
    warn "uv Python TOML error: $toml_err"
    return 1
  fi

  if ! publish_temp "$tmp" "$CODEX_CONFIG"; then
    return 1
  fi
  log "wrote $CODEX_CONFIG"
}

copy_with_header() {
  local src="$1" dst="$2" label="$3" tmp
  [ -f "$src" ] || return 0
  tmp="$(mktemp "${dst}.tmp.XXXXXX")"
  if ! printf '<!-- AUTO-GENERATED by etc/sync-codex.sh from %s. Do not edit. -->\n\n' "$label" > "$tmp"; then
    rm -f "$tmp"
    warn "failed to generate $dst"
    return 1
  fi
  if ! cat "$src" >> "$tmp"; then
    rm -f "$tmp"
    warn "failed to generate $dst"
    return 1
  fi
  atomic_publish "$dst" "$tmp"
  log "wrote $dst"
}

copy_codexized_with_header() {
  local src="$1" dst="$2" label="$3" tmp
  [ -f "$src" ] || return 0
  tmp="$(mktemp "${dst}.tmp.XXXXXX")"
  if ! printf '<!-- AUTO-GENERATED by etc/sync-codex.sh from %s. Do not edit. -->\n\n' "$label" > "$tmp"; then
    rm -f "$tmp"
    warn "failed to generate $dst"
    return 1
  fi
  if ! codexize_stream < "$src" >> "$tmp"; then
    rm -f "$tmp"
    warn "failed to generate $dst"
    return 1
  fi
  atomic_publish "$dst" "$tmp"
  log "wrote $dst"
}

codexize_native_skill_paths_stream() {
  local native_skill_file name
  local -a sed_args=()

  for native_skill_file in "$CODEX_SKILLS_DIR"/*/SKILL.md; do
    [ -f "$native_skill_file" ] || continue
    name="$(basename "$(dirname "$native_skill_file")")"
    # Skill names are directory basenames.  Restrict the interpolation used in
    # the sed expression to the Codex skill-name alphabet.
    case "$name" in
      *[!A-Za-z0-9_-]*) continue ;;
    esac
    sed_args+=( -e "s#~/.agents/skills/${name}/#~/.codex/skills/${name}/#g" )
    sed_args+=( -e "s#~/.agents/skills/${name}\$#~/.codex/skills/${name}#g" )
    sed_args+=( -e "s#\\\${HOME}/\\.agents/skills/${name}/#\\\${HOME}/.codex/skills/${name}/#g" )
    sed_args+=( -e "s#\\\${HOME}/\\.agents/skills/${name}\$#\\\${HOME}/.codex/skills/${name}#g" )
  done

  if [ "${#sed_args[@]}" -eq 0 ]; then
    cat
  else
    sed "${sed_args[@]}"
  fi
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
    -e "s#\${HOME}/\\.claude/CLAUDE\\.md#\${HOME}/.codex/AGENTS.md#g" \
    -e "s#\${HOME}/\\.claude/agents#\${HOME}/.codex/agents#g" \
    -e "s#\${HOME}/\\.claude/skills#\${HOME}/.agents/skills#g" \
    -e "s#\${HOME}/\\.claude/projects#\${HOME}/.codex/memories#g" \
    -e "s#\${HOME}/\\.claude/#\${HOME}/.codex/#g" \
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
    -e 's/claude-fable-5-1/gpt-5.6-sol/g' \
    -e 's/claude-sonnet-4-6/gpt-5.6-luna/g' |
    sed -E \
      -e 's/(^|[^[:alnum:]_-])haiku([^[:alnum:]_-]|$)/\1gpt-5.6-luna\2/g' \
      -e 's/(^|[^[:alnum:]_-])sonnet([^[:alnum:]_-]|$)/\1gpt-5.6-luna\2/g' \
      -e 's/(^|[^[:alnum:]_-])opus([^[:alnum:]_-]|$)/\1gpt-5.6-sol\2/g' \
      -e 's/(^|[^[:alnum:]_-])fable([^[:alnum:]_-]|$)/\1gpt-5.6-sol\2/g' |
    codexize_native_skill_paths_stream
}

sync_pir2_protocol() {
  local src="${CODEX_DIR}/skills/pir2/references/protocol.md"
  local dst="${CODEX_DIR}/pir2-protocol.md" tmp
  [ -f "$src" ] || return 0

  tmp="$(mktemp "${dst}.tmp.XXXXXX")"
  if ! printf '%s\n\n' '<!-- AUTO-GENERATED by etc/sync-codex.sh from .codex/skills/pir2/references/protocol.md. Do not edit. -->' > "$tmp"; then
    rm -f "$tmp"
    warn "failed to generate $dst"
    return 1
  fi
  if ! cat "$src" >> "$tmp"; then
    rm -f "$tmp"
    warn "failed to generate $dst"
    return 1
  fi
  atomic_publish "$dst" "$tmp"
  log "wrote $dst"
}

codexize_file_in_place() {
  local file="$1" tmp
  [ -f "$file" ] || return 0
  tmp="$(mktemp "${file}.tmp.XXXXXX")"
  codexize_stream < "$file" > "$tmp"
  publish_temp "$tmp" "$file"
}

build_codex_agents_md() {
  local dst="${CODEX_DIR}/AGENTS.md" tmp

  tmp="$(mktemp "${dst}.tmp.XXXXXX")"
  if ! cat <<'HEADER' > "$tmp"; then
<!-- AUTO-GENERATED by etc/sync-codex.sh from AGENTS.md and
     .codex/codex-native-supplement.md.
     Do not edit by hand. Re-run: bash etc/sync-codex.sh
     Codex reads the shared core and Codex-native supplement through this
     generated file. -->

HEADER
    rm -f "$tmp"
    warn "failed to generate $dst"
    return 1
  fi
  if ! cat "$AGENTS_SRC" >> "$tmp"; then
    rm -f "$tmp"
    warn "failed to generate $dst"
    return 1
  fi
  if ! printf '\n' >> "$tmp"; then
    rm -f "$tmp"
    warn "failed to generate $dst"
    return 1
  fi
  if ! cat "$CODEX_NATIVE_SUPPLEMENT_SRC" >> "$tmp"; then
    rm -f "$tmp"
    warn "failed to generate $dst"
    return 1
  fi
  atomic_publish "$dst" "$tmp"

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
      if ! printf '%s\n' "$line" >> "$tmp"; then
        rm -f "$tmp"
        warn "failed to generate $file"
        return 1
      fi
      continue
    fi

    if [ "$fence_count" -eq 1 ] && [[ "$line" =~ ^([A-Za-z0-9_-]+):[[:space:]]*(.*)$ ]]; then
      local key="${BASH_REMATCH[1]}"
      local value="${BASH_REMATCH[2]}"
      local encoded_value
      if ! encoded_value="$(quote_yaml_scalar "$value")"; then
        rm -f "$tmp"
        warn "failed to encode frontmatter value in $file"
        return 1
      fi
      if ! printf '%s: %s\n' "$key" "$encoded_value" >> "$tmp"; then
        rm -f "$tmp"
        warn "failed to generate $file"
        return 1
      fi
    else
      if ! printf '%s\n' "$line" >> "$tmp"; then
        rm -f "$tmp"
        warn "failed to generate $file"
        return 1
      fi
    fi
  done < "$file"

  publish_temp "$tmp" "$file"
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
  # Every Codex subagent starts at Luna; worker-delegation owns measured
  # Terra/Sol escalation and the runner receives any explicit override.
  printf '%s' "gpt-5.6-luna"
}

codex_agent_reasoning_effort() {
  printf '%s' "max"
}

convert_agent_to_toml() {
  local src="$1" dst="$2" name description body model reasoning_effort tmp source_basename
  local encoded_name encoded_description encoded_model encoded_effort encoded_body
  name="$(extract_agent_frontmatter_value "$src" "name")"
  description="$(extract_agent_frontmatter_value "$src" "description")"
  if [ -z "$name" ]; then
    name="$(basename "$src" .md)"
  fi
  if [ -z "$description" ]; then
    description="Codex custom agent generated from $(basename "$src")."
  fi
  if ! description="$(printf '%s' "$description" | codexize_stream)"; then
    warn "failed to generate agent description: $dst"
    return 1
  fi
  if ! body="$(extract_agent_body "$src" | codexize_stream)"; then
    warn "failed to generate agent body: $dst"
    return 1
  fi
  model="$(codex_agent_model "$name")"
  reasoning_effort="$(codex_agent_reasoning_effort "$name")"

  if ! encoded_name="$(toml_quote "$name")"; then
    warn "failed to encode agent name: $dst"
    return 1
  fi
  if ! encoded_description="$(toml_quote "$description")"; then
    warn "failed to encode agent description: $dst"
    return 1
  fi
  if ! encoded_model="$(toml_quote "$model")"; then
    warn "failed to encode agent model: $dst"
    return 1
  fi
  if ! encoded_effort="$(toml_quote "$reasoning_effort")"; then
    warn "failed to encode agent reasoning effort: $dst"
    return 1
  fi
  if ! encoded_body="$(printf '%s' "$body" | jq -Rs .)"; then
    warn "failed to encode agent instructions: $dst"
    return 1
  fi

  if ! source_basename="$(basename "$src")"; then
    warn "failed to determine source name for $dst"
    return 1
  fi
  tmp="$(mktemp "${dst}.tmp.XXXXXX")"
  if ! printf '%s\n' "# LEGACY-GENERATED by etc/sync-codex.sh from .claude/agents/$source_basename (legacy snapshot; not a native overlay). Do not edit." > "$tmp"; then
    rm -f "$tmp"
    warn "failed to generate $dst"
    return 1
  fi
  if ! printf 'name = %s\n' "$encoded_name" >> "$tmp"; then
    rm -f "$tmp"
    warn "failed to generate $dst"
    return 1
  fi
  if ! printf 'description = %s\n' "$encoded_description" >> "$tmp"; then
    rm -f "$tmp"
    warn "failed to generate $dst"
    return 1
  fi
  if ! printf 'model = %s\n' "$encoded_model" >> "$tmp"; then
    rm -f "$tmp"
    warn "failed to generate $dst"
    return 1
  fi
  if ! printf 'model_reasoning_effort = %s\n' "$encoded_effort" >> "$tmp"; then
    rm -f "$tmp"
    warn "failed to generate $dst"
    return 1
  fi
  if ! printf 'developer_instructions = %s\n' "$encoded_body" >> "$tmp"; then
    rm -f "$tmp"
    warn "failed to generate $dst"
    return 1
  fi
  atomic_publish "$dst" "$tmp"

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
copy_codexized_with_header "${CODEX_DIR}/skills/pir2/references/handoff-protocol.md" "${CODEX_DIR}/pir-handoff.md" ".codex/skills/pir2/references/handoff-protocol.md"
copy_codexized_with_header "${CLAUDE_DIR}/user-feedback-protocol.md" "${CODEX_DIR}/user-feedback-protocol.md" ".claude/user-feedback-protocol.md"
copy_codexized_with_header "${CLAUDE_DIR}/ui-ux-principles.md" "${CODEX_DIR}/ui-ux-principles.md" ".claude/ui-ux-principles.md"
sync_pir2_protocol
copy_codexized_with_header "${CLAUDE_DIR}/dev-server.md" "${CODEX_DIR}/dev-server.md" ".claude/dev-server.md"
copy_codexized_with_header "${CLAUDE_DIR}/subagent-permissions.md" "${CODEX_DIR}/subagent-permissions.md" ".claude/subagent-permissions.md"
sync_legacy_mirrors_if_requested

log "done"
