#!/usr/bin/env bash
# Sync OpenCode config from dotfiles SSOT to ~/.config/opencode/.
#
# SSOT:
#   - $DOT_DIR/mcp-servers.json          (MCP servers)
#   - $DOT_DIR/.claude/settings.json     (permissions)
#   - $DOT_DIR/.claude/agents/*.md       (agent definitions)
#
# Generated (AUTO-GENERATED, do not hand-edit):
#   - ~/.config/opencode/opencode.json
#   - ~/.config/opencode/agents/<name>.md
#
# Re-running is idempotent.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

MCP_SRC="${DOT_DIR}/mcp-servers.json"
SETTINGS_SRC="${DOT_DIR}/.claude/settings.json"
AGENTS_SRC_DIR="${DOT_DIR}/.claude/agents"

TARGET_DIR="${HOME}/.config/opencode"
TARGET_JSON="${TARGET_DIR}/opencode.json"
TARGET_AGENTS_DIR="${TARGET_DIR}/agents"

log()  { echo "[sync-opencode] $*"; }
warn() { echo "[sync-opencode] warn: $*" >&2; }

# ---- 依存チェック ----
if ! command -v jq >/dev/null 2>&1; then
  warn "jq not found, skipping sync"
  exit 0
fi
if [ ! -f "$MCP_SRC" ];      then warn "missing $MCP_SRC"; exit 0; fi
if [ ! -f "$SETTINGS_SRC" ]; then warn "missing $SETTINGS_SRC"; exit 0; fi

mkdir -p "$TARGET_DIR" "$TARGET_AGENTS_DIR"

# ---- ステップ 4: モデル名変換 ----
# OpenCode は anthropic/<id> 形式で claude-* を受理する。
# 新モデル追加時もこの関数の変更は不要（claude-* プレフィックスが変わらない限り）。
map_model_name() {
  local m="${1:-}"
  [ -z "$m" ] && return 0
  # 既にプロバイダプレフィックス（"/"を含む）が付いていればそのまま
  case "$m" in
    */*) printf '%s' "$m"; return 0 ;;
  esac
  # claude- で始まるなら anthropic/ を付ける
  case "$m" in
    claude-*) printf 'anthropic/%s' "$m"; return 0 ;;
  esac
  # 不明モデル: そのまま出力 + 警告
  warn "unknown model id '$m', emitting as-is"
  printf '%s' "$m"
}

# ---- ステップ 5: MCP 形式変換 ----
# claudeCodeOnly:true のサーバーを除外し、OpenCode 向け形式に変換する。
# - command (string) + args (array) → command (array)
# - env → environment（キー名変換）
# - 空の env は environment キー自体を省略
# - type が明示されていれば優先、なければ url の有無で推定
build_mcp_section() {
  jq '
    .mcpServers
    | with_entries(
        select(.value.claudeCodeOnly != true)
        | .value as $v
        | .value |= (
            # type 推定: 明示 type を優先、なければ url/command で推定
            ($v.type // (if $v.url then "remote" else "local" end)) as $t
            | if $t == "remote" then
                {
                  type: "remote",
                  url: $v.url,
                  enabled: true
                }
              else
                # type が "stdio" などの未知値でも "local" にフォールバック
                {
                  type: "local",
                  command: ([$v.command] + ($v.args // [])),
                  environment: ($v.env // {}),
                  enabled: true
                }
                | if (.environment | length) == 0 then del(.environment) else . end
              end
          )
      )
  ' "$MCP_SRC"
}

# ---- ステップ 6: Permission 形式変換 ----

# build_permission_section: bash/edit/read パーミッション変換
# 入力: .claude/settings.json#permissions.{allow,deny}
# 出力: opencode.json#permission 形式
# - Bash(<pat>) → permission.bash."<pat-normalized>": "allow"|"deny"
# - Edit(<glob>) / Write(<glob>) → permission.edit."<glob>": "allow"|"deny"
# - Read(<glob>) → permission.read."<glob>": "allow"|"deny"
# - mcp__*、Skill(...)、引数なし Read/Grep/Glob/WebSearch/WebFetch は省略
build_permission_section() {
  jq -n \
    --argjson allow "$(jq '.permissions.allow // []' "$SETTINGS_SRC")" \
    --argjson deny  "$(jq '.permissions.deny  // []' "$SETTINGS_SRC")" \
  '
    def normalize_bash_pat:
      # "Bash(...)" の中身を正規化: "<inner>:*" 形式を "<inner> *" に変換
      if test("^.*:\\*$") then sub(":\\*$"; " *") else . end;

    def classify($verdict):
      capture("^(?<kind>Bash|Edit|Write|Read)\\((?<pat>.*)\\)$") as $m
      | if $m.kind == "Bash" then
          { section: "bash", key: ($m.pat | normalize_bash_pat), val: $verdict }
        elif ($m.kind == "Edit" or $m.kind == "Write") then
          { section: "edit", key: $m.pat, val: $verdict }
        elif $m.kind == "Read" then
          { section: "read", key: $m.pat, val: $verdict }
        else empty end;

    def collect($list; $verdict):
      $list
      | map(
          if test("^mcp__") then empty
          elif . == "Skill" or test("^Skill\\(") then empty
          elif . == "Read" or . == "Grep" or . == "Glob"
            or . == "WebSearch" or . == "WebFetch" then empty
          elif test("^(Bash|Edit|Write|Read)\\(") then classify($verdict)
          else empty end
        );

    ([
      (collect($allow; "allow")[]),
      (collect($deny;  "deny")[])
    ]) as $entries
    | {
        bash: ({"*": "ask"} + (
          [$entries[] | select(.section == "bash") | {(.key): .val}] | add // {}
        )),
        edit: ({"*": "ask"} + (
          [$entries[] | select(.section == "edit") | {(.key): .val}] | add // {}
        )),
        read: (
          [$entries[] | select(.section == "read") | {(.key): .val}] | add // {}
        )
      }
      | if (.read | length) == 0 then del(.read) else . end
  '
}

# build_tools_section: MCP の意図的 deny がある場合のみ tools セクションを生成
# 現状 settings.json に mcp__ deny は無いため空オブジェクトを返す。
# 将来 permissions.deny に "mcp__<server>_*" が現れたら、
# この関数で {"<servername>_*": false} 形式を出力するよう拡張する。
build_tools_section() {
  echo '{}'
}

# ---- ステップ 7: Agent frontmatter 変換 (pure bash + awk) ----

# frontmatter ブロック（最初の --- と次の --- の間）を取り出す
extract_frontmatter() {
  awk '
    BEGIN { count = 0 }
    /^---[[:space:]]*$/ { count++; if (count == 2) exit; next }
    count == 1 { print }
  ' "$1"
}

# 本文（2 つ目の --- 以降）を取り出す
extract_body() {
  awk '
    BEGIN { count = 0 }
    /^---[[:space:]]*$/ { count++; next }
    count >= 2 { print }
  ' "$1"
}

# frontmatter から特定キーのスカラー値を抽出（先頭一致、リスト・複数行は未対応）
# tools のような list-style フィールドは無視（出力対象外なので問題なし）
extract_scalar_key() {
  local file="$1" key="$2"
  awk -v k="$key" '
    BEGIN { found = 0 }
    found == 0 && $0 ~ ("^" k ":[ \t]") {
      sub("^" k ":[ \t]+", "")
      print
      found = 1
      exit
    }
  ' "$file"
}

convert_agent_file() {
  local src="$1"
  local base
  base="$(basename "$src")"
  local dst="${TARGET_AGENTS_DIR}/${base}"

  # frontmatter 不在チェック（ファイル先頭が --- でない場合はスキップ）
  if ! head -1 "$src" | grep -q '^---[[:space:]]*$'; then
    warn "no frontmatter in $src, skipping"
    return 0
  fi

  local fm_tmp body_tmp
  fm_tmp="$(mktemp)"
  body_tmp="$(mktemp)"
  extract_frontmatter "$src" > "$fm_tmp"
  extract_body        "$src" > "$body_tmp"

  local description model_raw model_mapped
  description="$(extract_scalar_key "$fm_tmp" "description")"
  model_raw="$(extract_scalar_key "$fm_tmp" "model")"
  model_mapped="$(map_model_name "$model_raw")"

  # description が空なら "(no description)" にフォールバック
  [ -z "$description" ] && description="(no description)"

  local out_tmp
  out_tmp="$(mktemp)"
  {
    printf '<!-- AUTO-GENERATED by etc/sync-opencode.sh from .claude/agents/%s. Do not edit. -->\n' "$base"
    printf -- '---\n'
    printf 'description: %s\n' "$description"
    printf 'mode: subagent\n'
    if [ -n "$model_mapped" ]; then
      printf 'model: %s\n' "$model_mapped"
    fi
    printf -- '---\n'
    cat "$body_tmp"
  } > "$out_tmp"

  mv -f "$out_tmp" "$dst"
  rm -f "$fm_tmp" "$body_tmp" "$out_tmp"
  log "converted $base"
}

# ---- ステップ 8: opencode.json 組み立て ----
write_opencode_json() {
  local mcp_json="$1" perm_json="$2" tools_json="$3"

  local tmp
  tmp="$(mktemp)"

  if [ "$(echo "$tools_json" | jq 'length')" = "0" ]; then
    # tools セクション省略
    jq -n \
      --argjson mcp  "$mcp_json" \
      --argjson perm "$perm_json" \
    '{
       "$schema": "https://opencode.ai/config.json",
       mcp: $mcp,
       permission: $perm
     }' > "$tmp"
  else
    jq -n \
      --argjson mcp   "$mcp_json" \
      --argjson perm  "$perm_json" \
      --argjson tools "$tools_json" \
    '{
       "$schema": "https://opencode.ai/config.json",
       mcp: $mcp,
       permission: $perm,
       tools: $tools
     }' > "$tmp"
  fi

  jq empty "$tmp"  # 純粋 JSON のうちに構文確認

  # Prepend JSONC header comment (OpenCode supports JSONC)
  local tmp_with_header
  tmp_with_header="$(mktemp)"
  {
    echo '// AUTO-GENERATED by dotfiles/etc/sync-opencode.sh from SSOT'
    echo '// (mcp-servers.json + .claude/settings.json + .claude/agents/*.md).'
    echo '// Do not edit by hand. Re-run: bash etc/sync-opencode.sh'
    cat "$tmp"
  } > "$tmp_with_header"

  mv -f "$tmp_with_header" "$TARGET_JSON"
  rm -f "$tmp"
  log "wrote $TARGET_JSON"
}

# 孤児 agent 削除（SSOT に存在しない AUTO-GENERATED ファイルのみ）
cleanup_orphan_agents() {
  for f in "${TARGET_AGENTS_DIR}"/*.md; do
    [ -f "$f" ] || continue
    # AUTO-GENERATED ヘッダが無いファイル（手書きファイル）は誤削除しない
    if ! head -1 "$f" | grep -q '^<!-- AUTO-GENERATED by etc/sync-opencode.sh'; then
      continue
    fi
    local base
    base="$(basename "$f")"
    # SSOT に対応ファイルが無ければ削除
    if [ ! -f "${AGENTS_SRC_DIR}/${base}" ]; then
      rm -f "$f"
      log "removed orphan agent: $base"
    fi
  done
}

# ---- メイン処理 ----
MCP_JSON="$(build_mcp_section)"
PERM_JSON="$(build_permission_section)"
TOOLS_JSON="$(build_tools_section)"

write_opencode_json "$MCP_JSON" "$PERM_JSON" "$TOOLS_JSON"

# agent 変換
for f in "$AGENTS_SRC_DIR"/*.md; do
  [ -f "$f" ] || continue
  convert_agent_file "$f"
done

# 孤児 agent 削除
cleanup_orphan_agents

log "done"
