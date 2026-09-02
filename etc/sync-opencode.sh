#!/usr/bin/env bash
# Sync OpenCode config from dotfiles SSOT to ~/.config/opencode/.
#
# SSOT:
#   - $DOT_DIR/mcp-servers.json          (MCP servers)
#   - $DOT_DIR/.claude/settings.json     (permissions)
#   - $DOT_DIR/AGENTS.md                 (shared global instructions)
#   - $DOT_DIR/.agents/skills/*          (shared skill definitions)
#   - $DOT_DIR/.claude/agents/*.md       (agent definitions)
#   - $DOT_DIR/.opencode/plugins/*       (OpenCode native plugins, hooks 相当)
#
# Generated (AUTO-GENERATED, do not hand-edit):
#   - ~/.config/opencode/opencode.json
#   - ~/.config/opencode/agents/<name>.md
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
AGENTS_SRC_DIR="${DOT_DIR}/.claude/agents"
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
  warn "jq not found, skipping sync"
  exit 0
fi
if [ ! -f "$MCP_SRC" ];      then warn "missing $MCP_SRC"; exit 0; fi
if [ ! -f "$AGENTS_SRC" ];   then warn "missing $AGENTS_SRC"; exit 0; fi
if [ ! -f "$SETTINGS_SRC" ]; then warn "missing $SETTINGS_SRC"; exit 0; fi

mkdir -p "$TARGET_DIR" "$TARGET_AGENTS_DIR"
if [ -d "$PLUGIN_SRC_DIR" ]; then
  mkdir -p "$TARGET_PLUGINS_DIR"
fi
# ---- ステップ 4: モデル名変換 ----
# OpenCode は anthropic/<id> 形式で claude-* を受理する。フル claude-* ID は
# プレフィックスを付けるだけで変更不要。ただしバラのエイリアス（sonnet/opus）は
# Claude Code ハーネス固有の機能で OpenCode / Anthropic API は解決できないため、
# ここで具体 ID にマップする。Sonnet/Opus/Fable の新メジャーが出たらこのマップ 1 箇所だけ更新する。
map_model_name() {
  local m="${1:-}"
  [ -z "$m" ] && return 0
  # 既にプロバイダプレフィックス（"/"を含む）が付いていればそのまま
  case "$m" in
    */*) printf '%s' "$m"; return 0 ;;
  esac
  # Claude Code 固有のバラのエイリアスを具体 ID へ解決（OpenCode は解決不可）
  case "$m" in
    sonnet) printf '%s' 'anthropic/claude-sonnet-5'; return 0 ;;
    opus)   printf '%s' 'anthropic/claude-opus-4-8'; return 0 ;;
    fable)  printf '%s' 'anthropic/claude-fable-5-1'; return 0 ;;
    fable5) printf '%s' 'anthropic/claude-fable-5-1'; return 0 ;;
    fable5.1|fable-5-1|claude-fable-5-1) printf '%s' 'anthropic/claude-fable-5-1'; return 0 ;;
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
# claudeCodeOnly / codexOnly のサーバーを除外し、OpenCode 向け形式に変換する。
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

  publish "$out_tmp" "$dst"
  rm -f "$fm_tmp" "$body_tmp"
  [ "$CHECK_ONLY" = "1" ] || log "converted $base"
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
    echo '// (mcp-servers.json + AGENTS.md + .claude/settings.json + .claude/agents/*.md).'
    echo '// Do not edit by hand. Re-run: bash etc/sync-opencode.sh'
    cat "$tmp"
  } > "$tmp_with_header"

  publish "$tmp_with_header" "$TARGET_JSON"
  rm -f "$tmp"
  [ "$CHECK_ONLY" = "1" ] || log "wrote $TARGET_JSON"
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
      if [ "$CHECK_ONLY" = "1" ]; then
        die "check failed: orphan agent would be removed: $base"
      fi
      rm -f "$f"
      log "removed orphan agent: $base"
    fi
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

# 孤児 plugin 削除（agent と同じ手書き保護ルール）
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
    warn "missing $src, skipping AGENTS.md generation"
    return 0
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

このセクションは OpenCode 起動時にのみ効く。共通ルールの SSOT は dotfiles の `AGENTS.md` と `.agents/skills/*`。

## サブエージェント起動の読み替え

上述の `AGENTS.md` および `~/.agents/skills/*/SKILL.md` 内に登場するツール固有表記は、OpenCode 文脈では以下に読み替えること:

| 出現する表記 | OpenCode での実体 |
|------------|------------------|
| `Agent` ツール / `Agent` で起動 / `Agent` ツールで `<role>` を起動 | OpenCode の **`task` tool** で同名のサブエージェントを起動する。`subagent_type=<name>` 指定はそのまま担当名として使う |
| Claude Code のバージョン参照（例: 「v2.1.172〜」「Claude Code vN」） | OpenCode 無関係のため無視してよい |
| `TaskCreate` / `TaskUpdate` / `TaskList` 等のタスクツール | OpenCode 非対応のため**スキップ**する（タスク追跡は会話文脈で代替） |
| `mcp__<server>__<tool>` 形式の MCP ツール名 | OpenCode では **`<server>_<tool>`**（シングルアンダースコア）形式 |
| 「サブエージェントは MCP ツールを呼べない」等の制約記述 | Claude Code 固有制約。OpenCode ではサブエージェントも MCP ツールを呼べるため、MCP 必須ステップを上位へ不必要にエスカレーションしない |
| Bash / task の `run_in_background: true`・timeout パラメータ前提の手順 | OpenCode には当該パラメータが存在しない。background 前提手順（codex-runner 等）は nohup デタッチ等 bash 単体で再現するか中止する |

サブエージェント定義は `~/.config/opencode/agents/<name>.md` に変換生成されており、`mode: subagent` が付与済みなのでそのまま `task` tool から呼び出せる。生成時に frontmatter の `tools:` 制限は引き継がない。そのため「tools に X を持たない」という本文の権限線引きは実効性がなくプロンプト遵守に依存する。

## スキルの発見経路

`opencode.json` に `skills` キーは書かない。OpenCode の外部スキル自動発見（`~/.agents/skills/*/SKILL.md` と `~/.claude/skills/*/SKILL.md`）に全依存しており、`link.sh` が張る `~/.agents -> dotfiles/.agents` symlink が切れると全共有スキルが沈黙する点に注意。

## 動作対象外スキル（OpenCode で起動しない）

以下のスキルは hooks、Agent Teams、background サブエージェント等の非対応機能、または多段オーケストレーションに依存するため、OpenCode セッションでは**起動しないこと**。ユーザー指示で起動が要求された場合は「OpenCode 環境では非対応」と明示してから処理を中止する:

- `/pir2` `/pir2async` `/ir` `/debug` `/writing-plan` `/epic` — Plan/Implement/Review 多段オーケストレーション系
- `/pir2codex` — codex-runner + Codex CLI 前提（`.claude/skills` 由来）
- `/reviewer` `/review-pr` `/refactor-advisor` `/retro` — レビュー系（reviewer エージェントの並列起動を前提）
- `/codex` — codex-runner を background サブエージェントとして起動する前提（task tool に background 実行がない）
- `/check-updates` — git 管理スキルの bulk pull（対象外運用。必要なら個別に pull する）

## 動作可能スキル（OpenCode でも使用可）

- **単独完結**: `/ai-diary` `/ai-ltm` `/field-notes` `/dotfiles-autosync` `/ai-design-system`
- **task tool 委譲ありで使用可**: `/chat`（explorer / tech-validator / general-purpose 委譲）、`/brainstorm`（explorer 委譲）、`/walkthrough`（explorer 委譲。ただし本文の Codex 専用モデルピン gpt-5.4-mini/gpt-5.5 と `--team` フラグは無効）、`/research`（explorer / thinker / hypothesizer 委譲）、`/deepthink`（deliberator / synthesizer / gate / explorer 委譲）、`/tester`（tester agent 委譲）、`/sentinel-review`（sentinel-iac 委譲）、`/instruction-refactor`（explorer 委譲）、`/unity-mcp-skill`（Unity MCP 操作）

## hooks / settings.json 提案の扱い

retrospector 等が Claude Code の `hooks.PreToolUse` 追加や `.claude/settings.json` permission 追記の提案を出すことがある。OpenCode には settings.json 形式の hooks はないが、**plugin（`~/.config/opencode/plugins/`）で `tool.execute.before` / `tool.execute.after` / `session.idle` 等により PreToolUse / PostToolUse / Stop 相当が実現可能**である。同等のガードを OpenCode でも入れる価値がある場合は、`.claude/settings.json` を直接編集せず、dotfiles の `.opencode/plugins/`（SSOT）に plugin として実装して `sync-opencode.sh` で配布すること。

## モデル選定の注意

- Anthropic Pro/Max サブスクは OpenCode から使用不可。Anthropic モデルを使うには API キー（従量課金）必須
- 設定は `opencode.json#model` で指定（例: `anthropic/claude-sonnet-5`）。sync-opencode.sh はバラ alias を `sonnet→anthropic/claude-sonnet-5`、`opus→anthropic/claude-opus-4-8`、`fable`/`fable5`/`claude-fable-5-1`→`anthropic/claude-fable-5-1` にマップする

## 互換性ギャップの諦め

以下は OpenCode で**意図的に互換化していない**ため、共通 AGENTS.md や skill の対応指示があっても OpenCode 環境では諦めること:

- hooks (`PreToolUse` / `PostToolUse` / `Stop`) — settings.json 形式の hooks 記述は非対応。ただし同等機能は plugin（`tool.execute.before/after`、`session.idle`）で実現済み。`~/.config/opencode/plugins/` のガードが効かない前提で動かないこと
- statusLine — OpenCode 非対応
- Agent Teams (`TeamCreate` / `SendMessage`) — OpenCode 非対応（pir2async 等のチーム化経路は常に無効）
- MCP の per-tool permission — OpenCode 側 Issue #6892 のため default allow
- サブエージェントの tools 制限 — sync で引き継がないため本文記述の実効性なし

詳細は dotfiles の `README.md`（OpenCode 統合セクション）と `etc/sync-opencode.sh` を参照。
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

# agent 変換
for f in "$AGENTS_SRC_DIR"/*.md; do
  [ -f "$f" ] || continue
  convert_agent_file "$f"
done

# 孤児 agent 削除
cleanup_orphan_agents

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
