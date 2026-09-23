#!/usr/bin/env bash
# Sync OpenCode config from dotfiles SSOT to ~/.config/opencode/.
#
# SSOT:
#   - $DOT_DIR/mcp-servers.json          (MCP servers)
#   - $DOT_DIR/.claude/settings.json     (permissions)
#   - $DOT_DIR/AGENTS.md                 (shared global instructions)
#   - $DOT_DIR/.agents/skills/*          (shared skill definitions)
#   - $DOT_DIR/.opencode/plugins/*       (OpenCode native plugins, hooks 相当)
#
# Generated (AUTO-GENERATED, do not hand-edit):
#   - ~/.config/opencode/opencode.json
#   - ~/.config/opencode/plugins/<name>
#
# Usage:
#   bash etc/sync-opencode.sh            # generate
#   bash etc/sync-opencode.sh --check    # no write; exit non-zero if outputs would change
#
# Re-running is idempotent.

set -euo pipefail

CHECK_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --check) CHECK_ONLY=1 ;;
    *) echo "[sync-opencode] error: unknown argument '$arg'" >&2; exit 2 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

MCP_SRC="${DOT_DIR}/mcp-servers.json"
AGENTS_SRC="${DOT_DIR}/AGENTS.md"
SETTINGS_SRC="${DOT_DIR}/.claude/settings.json"
PLUGIN_SRC_DIR="${DOT_DIR}/.opencode/plugins"

TARGET_DIR="${HOME}/.config/opencode"
TARGET_JSON="${TARGET_DIR}/opencode.json"
TARGET_AGENTS_DIR="${TARGET_DIR}/agents"
TARGET_PLUGINS_DIR="${TARGET_DIR}/plugins"

log()  { echo "[sync-opencode] $*"; }
warn() { echo "[sync-opencode] warn: $*" >&2; }
die()  { echo "[sync-opencode] error: $*" >&2; exit 1; }

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
if [ ! -f "$AGENTS_SRC" ];   then warn "required SSOT missing: $AGENTS_SRC"; exit 1; fi
if [ ! -f "$SETTINGS_SRC" ]; then warn "required SSOT missing: $SETTINGS_SRC"; exit 1; fi

if [ "$CHECK_ONLY" = "0" ]; then
  mkdir -p "$TARGET_DIR"
  if [ -d "$PLUGIN_SRC_DIR" ]; then
    mkdir -p "$TARGET_PLUGINS_DIR"
  fi
fi
# ---- ステップ 5: MCP 形式変換 ----
# claudeCodeOnly / codexOnly / cursorOnly / devinOnly のサーバーを除外し、OpenCode 向け形式に変換する。
# - command (string) + args (array) → command (array)
# - env → environment（キー名変換）
# - 空の env は environment キー自体を省略
# - type が明示されていれば優先、なければ url の有無で推定
build_mcp_section() {
  jq '
    .mcpServers
    | with_entries(
        select(.value.claudeCodeOnly != true)
        | select(.value.codexOnly != true)
        | select(.value.cursorOnly != true)
        | select(.value.devinOnly != true)
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

# build_permission_section: OpenCode 向け permission ポリシー生成
# - bash: allow 既定 + 危険操作のみ ask（承認プロンプト地獄の解消）。
#   Claude Code 側の白リスト方式（.claude/settings.json#permissions.allow）とは哲学が異なるため
#   allow リストは OpenCode には流さない
# - edit: allow 既定
# - read: settings.json の Read deny（node_modules 等の context 保護）のみ変換して維持
# - external_directory: allow 既定。OpenCode の既定は ask で、"always" 承認はセッション限りのため、
#   cwd 外参照（~/.config/opencode, ~/ai-ltm-data, ~/.claude/skills 等）で毎回承認が発生する。
#   ホーム配下は信頼する前提なので ~/** を許可して恒久解消する
build_permission_section() {
  local read_denies
  read_denies="$(jq '
    .permissions.deny // []
    | map(select(startswith("Read(")))
    | map(ltrimstr("Read(") | rtrimstr(")"))
  ' "$SETTINGS_SRC")"

  jq -n --argjson read_denies "$read_denies" '
    {
      bash: {
        "*": "allow",
        "rm -rf *": "ask",
        "rm -fr *": "ask",
        "sudo *": "ask",
        "su *": "ask",
        "git push *": "ask",
        "git reset --hard *": "ask",
        "git clean *": "ask"
      },
      edit: "allow",
      read: (($read_denies | map({(.): "deny"}) | add) // {}),
      external_directory: {
        "~/**": "allow"
      }
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

# ---- ステップ 8: opencode.json 組み立て ----
write_opencode_json() {
  local mcp_json="$1" perm_json="$2" tools_json="$3"

  local tmp
  tmp="$(mktemp)"

  # lsp: true — OpenCode は lsp キー省略時（デフォルト）に全 LSP サーバー無効のため
  # 明示有効化する（公式 docs: "LSP is disabled by default"）
  if [ "$(echo "$tools_json" | jq 'length')" = "0" ]; then
    # tools セクション省略
    jq -n \
      --argjson mcp  "$mcp_json" \
      --argjson perm "$perm_json" \
    '{
       "$schema": "https://opencode.ai/config.json",
       mcp: $mcp,
       permission: $perm,
       lsp: true
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
       tools: $tools,
       lsp: true
     }' > "$tmp"
  fi

  jq empty "$tmp"  # 純粋 JSON のうちに構文確認

  # Prepend JSONC header comment (OpenCode supports JSONC)
  local tmp_with_header
  tmp_with_header="$(mktemp)"
  {
    echo '// AUTO-GENERATED by dotfiles/etc/sync-opencode.sh from SSOT'
    echo '// (mcp-servers.json + AGENTS.md + .claude/settings.json).'
    echo '// Do not edit by hand. Re-run: bash etc/sync-opencode.sh'
    cat "$tmp"
  } > "$tmp_with_header"

  publish "$tmp_with_header" "$TARGET_JSON"
  rm -f "$tmp"
  [ "$CHECK_ONLY" = "1" ] || log "wrote $TARGET_JSON"
}

# 以前このscriptが生成した agent を削除する（AUTO-GENERATED ヘッダが無い手書きファイルは残す）
cleanup_generated_agents() {
  for f in "${TARGET_AGENTS_DIR}"/*.md; do
    [ -f "$f" ] || continue
    head -1 "$f" | grep -q '^<!-- AUTO-GENERATED by etc/sync-opencode.sh' || continue
    if [ "$CHECK_ONLY" = "1" ]; then
      die "check failed: generated agent would be removed: $(basename "$f")"
    fi
    rm -f "$f"
    log "removed generated agent: $(basename "$f")"
  done
}

# ---- OpenCode plugin 同期（hooks 相当。native overlay の repo 側 SSOT からベリファイコピー）----
# OpenCode は ~/.config/opencode/plugins/ の JS/TS を自動ロードし、
# tool.execute.before/after や session.idle 等で Claude Code hooks 相当を実現する。
copy_plugins() {
  if [ ! -d "$PLUGIN_SRC_DIR" ]; then
    return 0
  fi
  for f in "${PLUGIN_SRC_DIR}"/*; do
    [ -f "$f" ] || continue
    case "$f" in
      *.js|*.ts|*.mjs) ;;
      *) continue ;;
    esac
    local base out_tmp
    base="$(basename "$f")"
    out_tmp="$(mktemp)"
    {
      printf '// AUTO-GENERATED by etc/sync-opencode.sh from .opencode/plugins/%s. Do not edit.\n' "$base"
      cat "$f"
    } > "$out_tmp"
    publish "$out_tmp" "${TARGET_PLUGINS_DIR}/${base}"
    [ "$CHECK_ONLY" = "1" ] || log "copied plugin $base"
  done
}

# 孤児 plugin 削除（AUTO-GENERATED ヘッダが無い手書きファイルは残す）
cleanup_orphan_plugins() {
  if [ ! -d "$TARGET_PLUGINS_DIR" ]; then
    return 0
  fi
  for f in "${TARGET_PLUGINS_DIR}"/*; do
    [ -f "$f" ] || continue
    if ! head -1 "$f" | grep -q '^// AUTO-GENERATED by etc/sync-opencode.sh'; then
      continue
    fi
    local base
    base="$(basename "$f")"
    if [ ! -f "${PLUGIN_SRC_DIR}/${base}" ]; then
      if [ "$CHECK_ONLY" = "1" ]; then
        die "check failed: orphan plugin would be removed: $base"
      fi
      rm -f "$f"
      log "removed orphan plugin: $base"
    fi
  done
}

# ---- AGENTS.md 生成（OpenCode は AGENTS.md があると CLAUDE.md を override する）----
# Shared AGENTS.md 全文を取り込み、末尾に OpenCode 専用の読み替えルールを追記する。
build_agents_md() {
  local src="$AGENTS_SRC"
  local dst="${TARGET_DIR}/AGENTS.md"

  if [ ! -f "$src" ]; then
    die "required SSOT missing: $src"
  fi

  local tmp
  tmp="$(mktemp)"

  {
    cat <<'HEADER'
<!-- AUTO-GENERATED by dotfiles/etc/sync-opencode.sh from AGENTS.md.
     Do not edit by hand. Re-run: bash etc/sync-opencode.sh
     OpenCode reads AGENTS.md instead of CLAUDE.md (override behavior, not merge).
     Source: https://github.com/anomalyco/opencode/blob/main/packages/opencode/src/session/instruction.ts -->

HEADER
    cat "$src"
    cat <<'FOOTER'

---

# OpenCode 専用補足ルール（dotfiles SSOT 由来）

共有の目的・承認・完了条件は上のAGENTSと選択した共有Skillに従う。実行機構だけをOpenCodeの公開ツールと有効な設定へ合わせる。

## サブエージェント起動の読み替え

委譲には実在する `task` tool と、OpenCodeが提供する標準の担当を使う。担当名・モデル名・引数は実際の定義と公開schemaで確認し、別runtimeの `Agent` / `Task` / collaboration 引数をそのまま渡さない。

共有Skillが親の直接実行を許していれば、その経路も使える。ユーザーが指定した独立性・並列性・モデル・外部CLI実行は維持し、利用不能なら満たせない要件を具体的に報告する。記録用のTask管理APIがないだけで実装を止めず、必要な状態は会話や既存の計画に保持する。

## スキルの発見経路

共有原本は `~/.agents/skills/*/SKILL.md`。Claude互換入口は `~/.claude/skills/*/SKILL.md`。repo側の対応する配置も発見対象であり、選択した実体の `SKILL.md` と必要な参照だけを読む。homeの共有リンクは `etc/link.sh` が `~/.agents/skills` に配置する。

同名の共有原本とClaude入口がある場合は、実在確認した `.agents/skills/<name>/SKILL.md` を明示的に読み、共有手順を使う。これはloaderの優先順位を保証する設定ではない。Claude側しかない場合は、その入口が要求する固有機能を下の条件で確認する。

このadapterは `opencode.json` のskills登録を生成しない。発見・有効化の問題では実体pathと `permission.skill` を確認する。名前・description以外の未対応frontmatterを、そのまま実行権限と解釈しない。

## スキルの適用条件

スキル名や工程数だけで利用を一律禁止しない。対象の共有Skillにある通常・直接・逐次の経路を、実在するツールで実行する。計画・監査だけの依頼はその範囲で終了し、実装依頼は必要な検証まで進める。

Claude Agent Teams、専用background API、指定モデルなどの固有機能が必須の経路は、対応を実測してから使う。Skill自身が代替経路を定めていればその条件に従う。代替不可の必須機能を利用できない場合は、その要件を未達として依存操作だけを止め、独立した許可済み作業を続ける。background処理を無条件にnohupへ置き換えない。

スキル・plugin更新は `check-updates` の対象選択とスクリプト、dotfiles同期は `dotfiles-autosync` の中央engineに従う。個別のpullへ置き換えたり、名前だけで非対応としない。

## 権限と固有機能

- 委譲時のread-only指示は行動上の境界であり、技術的な隔離ではない。実際のpermission・MCP権限と行動上の制約を守る。
- Claudeのsettings.json形式のhooksをOpenCode設定へ書かない。既存OpenCode pluginの原本は `.opencode/plugins/`、配布先は `~/.config/opencode/plugins/`。ガードが効かないと仮定せず、実装と実測で確認する。
- `TaskCreate`、`TeamCreate`、statusLineなど他runtime固有の機能名をOpenCodeのAPIとして扱わない。対応するnative機能があるかを必要な場面で確認する。
- MCPのper-tool制御や子の権限は有効設定・ツール・公式仕様で確認する。別runtimeの制約や過去のissueを根拠に一律のallow/denyを仮定しない。

## モデルと設定の原本

有効なOpenCode設定を使い、モデル・認証・承認の変更を指示整理のついでに行わない。モデル一覧を指示本文へ複製しない。

生成物は直接編集せず、対応するdotfiles原本を修正して `bash etc/sync-opencode.sh` で反映する。詳細な接続と配布は `AI-WORKFLOW-SPEC.md`、公開仕様は [OpenCode agents](https://opencode.ai/docs/agents/) と [skills](https://opencode.ai/docs/skills/) を必要なときに確認する。
FOOTER
  } > "$tmp"

  publish "$tmp" "$dst"
  [ "$CHECK_ONLY" = "1" ] || log "wrote $dst"
}

# ---- メイン処理 ----
MCP_JSON="$(build_mcp_section)"
PERM_JSON="$(build_permission_section)"
TOOLS_JSON="$(build_tools_section)"

write_opencode_json "$MCP_JSON" "$PERM_JSON" "$TOOLS_JSON"

cleanup_generated_agents

# plugin 同期（hooks 相当）
copy_plugins
cleanup_orphan_plugins

# AGENTS.md 生成
build_agents_md

if [ "$CHECK_ONLY" = "1" ]; then
  log "check passed"
  exit 0
fi

log "done"
