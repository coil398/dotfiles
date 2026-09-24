#!/usr/bin/env bash
# Sync Devin CLI config from dotfiles SSOT to the Devin user config dir.
#
# SSOT:
#   - $DOT_DIR/mcp-servers.json          (MCP servers)
#   - $DOT_DIR/.claude/settings.json     (permissions)
#
# Generated (AUTO-GENERATED, do not hand-edit):
#   - <devin-config>/mcp_config.json
#   - <devin-config>/deny-guard.py   (copy of $DOT_DIR/etc/devin-deny-guard.py)
#
# Merged (managed keys only; machine-local keys preserved):
#   - <devin-config>/config.json   (permissions + read_config_from + managed hooks:
#                                   Stop = jev, PreToolUse = deny-guard)
#
# The deny guard evaluates permissions.deny rules in a PreToolUse hook and
# returns decision=block + reason, so the agent keeps its turn instead of the
# whole turn dying on "Permission denied" (hook block returns the reason to
# the agent since v3000.6.2). The deny entries stay in permissions as the
# backstop (Read(...) denies also drive sandbox path hiding).
#
# <devin-config> is ~/.config/devin (macOS/Linux) or %APPDATA%\devin (Windows).
# link.sh additionally symlinks <devin-config>/AGENTS.md -> $DOT_DIR/AGENTS.md.
#
# Usage:
#   bash etc/sync-devin.sh            # generate
#   bash etc/sync-devin.sh --check    # no write; exit non-zero if outputs would change
#
# Re-running is idempotent. Servers added manually via `devin mcp add -s user`
# are wiped on re-sync because mcp_config.json is fully managed — the same
# design as etc/sync-mcp.sh (user scope is SSOT-managed).
#
# Permission conversion notes (.claude/settings.json -> Devin syntax):
#   - Bash(<cmd> *) / Bash(<cmd>:*) / Bash(<cmd>) -> Exec(<cmd>).
#     Claude's exact-match Bash(x) becomes Devin's prefix match Exec(x),
#     which is slightly broader (Exec(pwd) also allows `pwd -L`).
#   - Read(glob) is passed through. Edit(glob) -> Write(glob).
#   - Bare tool names map to Devin's lowercase tools: Read/Grep/Glob/Edit.
#   - mcp__* rules pass through unchanged.
#   - WebFetch / WebSearch and unrecognised entries are dropped: Devin's
#     Fetch() is URL-scoped and has no whole-tool equivalent.
#
# read_config_from: claude:false / cursor:false are forced on. Devin would
# otherwise read ~/.claude/CLAUDE.md (global) plus .claude/ and .cursor/rules
# (project) on top of the AGENTS.md SSOT, double-loading the same guidance.

set -euo pipefail

CHECK_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --check) CHECK_ONLY=1 ;;
    *) echo "[sync-devin] error: unknown argument '$arg'" >&2; exit 2 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

MCP_SRC="${DOT_DIR}/mcp-servers.json"
SETTINGS_SRC="${DOT_DIR}/.claude/settings.json"

TARGET_DIR="${HOME}/.config/devin"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    if [ -n "${APPDATA:-}" ] && command -v cygpath >/dev/null 2>&1; then
      TARGET_DIR="$(cygpath -u "$APPDATA")/devin"
    fi
    ;;
esac
TARGET_MCP_JSON="${TARGET_DIR}/mcp_config.json"
TARGET_CONFIG_JSON="${TARGET_DIR}/config.json"

log()  { echo "[sync-devin] $*"; }
warn() { echo "[sync-devin] warn: $*" >&2; }
die()  { echo "[sync-devin] error: $*" >&2; exit 1; }

# publish <src_tmp> <dst>: --check 時は書き込まず一致比較のみ行う
publish() {
  local src="$1" dst="$2"
  if [ -L "$dst" ] || [ -d "$dst" ]; then
    rm -f "$src"
    die "refusing to publish generated output to symlink or directory: $dst"
  fi
  if [ "$CHECK_ONLY" = "1" ]; then
    if [ ! -f "$dst" ] || ! cmp -s "$src" "$dst"; then
      rm -f "$src"
      die "check failed: $dst would change (or is missing)"
    fi
    rm -f "$src"
    log "check ok $dst"
    return 0
  fi
  mv -f "$src" "$dst"
}

# ---- 依存チェック ----
if ! command -v jq >/dev/null 2>&1; then
  warn "required dependency missing: jq"
  exit 1
fi
if [ ! -f "$MCP_SRC" ];      then warn "required SSOT missing: $MCP_SRC"; exit 1; fi
if [ ! -f "$SETTINGS_SRC" ]; then warn "required SSOT missing: $SETTINGS_SRC"; exit 1; fi

if [ "$CHECK_ONLY" = "0" ]; then
  mkdir -p "$TARGET_DIR"
fi

# ---- MCP 形式変換 ----
# claudeCodeOnly / openCodeOnly / codexOnly / cursorOnly のサーバーを除外し、
# Devin 向け形式に変換する。
# - remote: {url, transport} + headers/oauth*/disabled を pass-through
# - local : {command, args, env}（空 env は省略）+ disabled
build_mcp_section() {
  jq '
    .mcpServers
    | with_entries(
        select(.value.claudeCodeOnly != true)
        | select(.value.openCodeOnly != true)
        | select(.value.codexOnly != true)
        | select(.value.cursorOnly != true)
        | .value as $v
        | .value |= (
            ($v.type // (if $v.url then "remote" else "local" end)) as $t
            | if $t == "remote" then
                {url: $v.url, transport: ($v.transport // "http")}
                + ($v | {headers, oauthClientId, oauthClientSecret, oauthResource, disabled}
                       | with_entries(select(.value != null)))
              else
                {command: $v.command}
                + (if $v.args then {args: $v.args} else {} end)
                + (if (($v.env // {}) | length) > 0 then {env: $v.env} else {} end)
                + (if $v.disabled then {disabled: true} else {} end)
              end
          )
      )
    | {mcpServers: .}
  ' "$MCP_SRC"
}

# ---- Permission 形式変換 ----
# Claude Code の permission 文字列を Devin 形式に変換する。
# 認識できないエントリ（WebFetch / WebSearch / 壊れた文字列）は empty で落とす。
build_permission_section() {
  jq '
    def conv:
      if startswith("Bash(") and endswith(")") then
        (.[5:-1] | sub(" \\*$"; "") | sub(":\\*$"; "")) as $cmd
        | "Exec(\($cmd))"
      elif startswith("Read(") then .
      elif startswith("Write(") then .
      elif startswith("Edit(") and endswith(")") then "Write(\(.[5:-1]))"
      elif startswith("mcp__") then .
      elif . == "Read" then "read"
      elif . == "Grep" then "grep"
      elif . == "Glob" then "glob"
      elif . == "Edit" then "edit"
      elif . == "Write" then "edit"
      else empty end;
    .permissions as $p
    | {
        allow: ([$p.allow[]? | conv] | unique),
        deny:  ([$p.deny[]?  | conv] | unique),
        ask:   ([$p.ask[]?   | conv] | unique)
      }
    | if (.ask | length) == 0 then del(.ask) else . end
  ' "$SETTINGS_SRC"
}

# ---- mcp_config.json 組み立て ----
write_mcp_config() {
  local mcp_json="$1"
  local tmp
  tmp="$(mktemp)"

  printf '%s\n' "$mcp_json" > "$tmp"
  jq empty "$tmp"  # 純粋 JSON のうちに構文確認

  # Devin config files support // comments (JSONC)
  local tmp_with_header
  tmp_with_header="$(mktemp)"
  {
    echo '// AUTO-GENERATED by dotfiles/etc/sync-devin.sh from mcp-servers.json.'
    echo '// Do not edit by hand; `devin mcp add -s user` entries are wiped on re-sync.'
    echo '// Re-run: bash etc/sync-devin.sh'
    cat "$tmp"
  } > "$tmp_with_header"

  publish "$tmp_with_header" "$TARGET_MCP_JSON"
  rm -f "$tmp"
  [ "$CHECK_ONLY" = "1" ] || log "wrote $TARGET_MCP_JSON"
}

# ---- deny-guard.py 配備 ----
# hook が参照する実体は devin-config 配下に置く (checkout の移動に依存しない)。
write_deny_guard() {
  local tmp
  tmp="$(mktemp)"
  cp "${SCRIPT_DIR}/devin-deny-guard.py" "$tmp"
  publish "$tmp" "${TARGET_DIR}/deny-guard.py"
  [ "$CHECK_ONLY" = "1" ] || log "wrote ${TARGET_DIR}/deny-guard.py"
}

# ---- config.json マージ ----
# Devin 自身が org_id / shell / theme_mode 等を書き込むファイルなので、
# managed keys（permissions / read_config_from / managed hooks）だけを上書きし、
# それ以外の既存キーはすべて保持する。ファイルが無ければ managed keys のみで作る。
write_config() {
  local perm_json="$1"
  local tmp stop_cmd guard_cmd
  tmp="$(mktemp)"
  stop_cmd="$(python3 -c 'import shlex,sys; print("sh " + shlex.quote(sys.argv[1]) + " devin")' "${DOT_DIR}/jev-hooks/hook.sh")"
  guard_cmd="$(python3 -c 'import shlex,sys; print("python3 " + shlex.quote(sys.argv[1]))' "${TARGET_DIR}/deny-guard.py")"

  if [ -f "$TARGET_CONFIG_JSON" ]; then
    # Devin writes plain JSON here; hand-added // comments would break jq.
    if ! jq empty "$TARGET_CONFIG_JSON" 2>/dev/null; then
      rm -f "$tmp"
      die "cannot parse $TARGET_CONFIG_JSON as JSON (remove // comments or fix syntax); refusing to merge"
    fi
    jq --argjson perm "$perm_json" --arg stop_cmd "$stop_cmd" --arg guard_cmd "$guard_cmd" '
      .permissions = $perm
      | .read_config_from = ((.read_config_from // {}) + {claude: false, cursor: false})
      | .hooks = ((.hooks // {}) + {
          Stop: ([.hooks.Stop[]? |
            if ([.hooks[]?.command // ""] | any(contains("jev-hooks/hook.sh")))
            then .hooks |= map(select((.command // "") | contains("jev-hooks/hook.sh") | not)) | select(.hooks | length > 0)
            else . end] + [
            {
              matcher: "",
              hooks: [
                {type: "command", command: $stop_cmd, timeout: 10}
              ]
            }
          ]),
          PreToolUse: ([.hooks.PreToolUse[]? |
            if ([.hooks[]?.command // ""] | any(contains("deny-guard")))
            then .hooks |= map(select((.command // "") | contains("deny-guard") | not)) | select(.hooks | length > 0)
            else . end] + [
            {
              matcher: "",
              hooks: [
                {type: "command", command: $guard_cmd, timeout: 5}
              ]
            }
          ])
        })
    ' "$TARGET_CONFIG_JSON" > "$tmp"
  else
    jq -n --argjson perm "$perm_json" --arg stop_cmd "$stop_cmd" --arg guard_cmd "$guard_cmd" '{
      permissions: $perm,
      read_config_from: {claude: false, cursor: false},
      hooks: {
        Stop: [
          {
            matcher: "",
            hooks: [
              {type: "command", command: $stop_cmd, timeout: 10}
            ]
          }
        ],
        PreToolUse: [
          {
            matcher: "",
            hooks: [
              {type: "command", command: $guard_cmd, timeout: 5}
            ]
          }
        ]
      }
    }' > "$tmp"
  fi

  jq empty "$tmp"  # 構文確認

  publish "$tmp" "$TARGET_CONFIG_JSON"
  [ "$CHECK_ONLY" = "1" ] || log "merged managed keys into $TARGET_CONFIG_JSON"
}

MCP_JSON="$(build_mcp_section)"
PERM_JSON="$(build_permission_section)"

write_mcp_config "$MCP_JSON"
write_deny_guard
write_config "$PERM_JSON"

[ "$CHECK_ONLY" = "1" ] || log "done (user scope)"
