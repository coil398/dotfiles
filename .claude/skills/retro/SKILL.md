---
name: retro
description: retrospector を単体で実行してパターンを汎化しエージェント定義を改善する。振り返り・ふりかえり・retrospective・改善サイクル・エージェント定義の見直し・パターン分析をしたいときに使う。`--meta` フラグでワークフロー骨格を改善するメタ自己改善モードを、`--dream` フラグで pir_pattern_registry を統合・整理する Dreaming モードを起動できる。ユーザーが /retro と入力したら必ずこのスキルを使う。
argument-hint: [--meta] [--dream] [対象プロジェクトのパス]
---

# Retro — パターン汎化・エージェント改善

蓄積されたログをもとにパターンを汎化し、エージェント定義を改善します。このスキル本体（= メイン Claude）がオーケストレーターとなり、`retrospector` を `Agent` ツールで起動します。サブエージェントも v2.1.172 以降は `Agent` ツールでネスト起動できますが、起動責任（制御フロー）はスキル本体に集約する設計とし、サブからのネスト起動は read-only の探索（explorer）に限ります。
`--meta`（または `meta`）フラグが指定された場合、ワークフロー骨格そのものを改善するメタ自己改善モードを起動します。

引数: $ARGUMENTS

---

## ステップ 0a: 引数解釈

`$ARGUMENTS` を bash で解釈し、メタモードフラグとプロジェクトパスを分離してください:

```bash
ARGS="$ARGUMENTS"
META_MODE=false
DREAM_MODE=false
PROJECT_PATH=""

for token in $ARGS; do
  case "$token" in
    --meta|meta)
      META_MODE=true
      ;;
    --dream|dream)
      DREAM_MODE=true
      ;;
    *)
      if [ -z "$PROJECT_PATH" ]; then
        PROJECT_PATH="$token"
      fi
      ;;
  esac
done

echo "META_MODE=$META_MODE"
echo "DREAM_MODE=$DREAM_MODE"
echo "PROJECT_PATH=${PROJECT_PATH:-$(pwd)}"
```

- `DREAM_MODE=true` の場合は meta-retrospector を Dreaming モードで起動する（最優先。`--meta` と同時指定された場合も Dreaming を優先）
- `META_MODE=true` の場合はステップ0b・1・2を実行する
- `META_MODE=false` かつ `DREAM_MODE=false` の場合は従来どおりステップ0b・1・2を実行する（プロセスは retrospector 側で分岐）

後方互換: 従来どおり第1引数にプロジェクトパスだけを渡す呼び出しは引き続き動作する。

---

## ステップ 0b: メモリパスの解決

`PROJECT_PATH` を基点にメモリパスを解決してください（指定がなければ現在のディレクトリ）:

```bash
target_path="${PROJECT_PATH:-$(pwd)}"
# sanitized-cwd 計算は ~/.claude/skills/pir2/references/sanitized-cwd.md を SSOT とする
# （Claude Code harness の sanitize 仕様変更時はこの SSOT のみを更新し、9 ファイルに横展開）
# 入力ソースは pwd 系ではなく target_path 系（retro は引数で対象パスを受け取るため）
sanitized_cwd="$(echo "$target_path" | sed 's|[^a-zA-Z0-9]|-|g')"
claude_dir="${HOME}/.claude/projects/${sanitized_cwd}/memory"
echo "PROJECT_MEMORY_DIR=$claude_dir"
echo "PROJECT_ROOT=$target_path"
```

---

## ステップ 1: agent 選択と起動

`DREAM_MODE` / `META_MODE` の値に応じて起動する agent を選択する:

- `DREAM_MODE=true`: `meta-retrospector` を起動（Dreaming モード。registry の統合・整理。最優先）
- `META_MODE=true`: `meta-retrospector` を起動（メタ自己改善専任）
- いずれも `false` または未指定: `retrospector` を起動（通常モード専任）

スキル本体（メイン Claude）が選択した agent サブエージェントを `Agent` ツールで起動してください。

共通プロンプトパラメータ（どの agent にも含める）:
- `PROJECT_MEMORY_DIR`（ステップ0bで取得したパス）
- `PROJECT_ROOT`（ステップ0bで取得したパス）
- `META_MODE=[true|false]`（ステップ0aで決定した値）
- `DREAM_MODE=[true|false]`（ステップ0aで決定した値）
- `EXPERIMENTAL_PATH=${HOME}/.claude/skills/pir2/references/experimental.md`
- `OBSERVATION_LOG_PATH=${HOME}/.claude/memory/experimental_observations.md`（観測ログの記録先・git 管理外）
- `INNER_LOOP_COUNT=0`
- `OUTER_LOOP_COUNT=0`
- `VERDICT=MANUAL`

追加メッセージ（agent / モード別）:
- `retrospector`（通常モード）: 「これは手動トリガーの振り返りです。蓄積されたログを全件読み込み、パターンの汎化を積極的に行ってください。`EXPERIMENTAL_PATH` が存在する場合は必ず読み、Active な実験の観測・推薦更新が必要か判断してください。新規の再利用単位が見つかった場合は、単体 skill で十分か、独立 agent に切るべきか、Codex plugin として `/plugin-creator` へ渡すべきかも判定してください。」
- `meta-retrospector`（メタモード）: 「これはメタ自己改善モードの手動トリガーです。レジストリの未処理メタ改善推奨フラグを読み込み、ワークフロー骨格の改善提案を作成してください。バックアップ・ユーザー承認・個別ファイル指定の commit を必ず行ってください。」
- `meta-retrospector`（Dreaming モード）: 「これは registry の Dreaming 統合モードです。Dreaming プロセス（D1〜D5）のみを実行してください。pir_pattern_registry.md 全件を読み、重複エントリの統合と陳腐化した観察中エントリの整理を行い、旧版を meta_retro_backups にバックアップしてから新版を生成してください。新版への差し替えは必ずユーザー承認を得てから行い、`## [メタ改善推奨]` セクションは保持してください。」

---

## ステップ 2: 結果の提示

retrospector の振り返りレポート（通常モードなら振り返りレポート、メタモードならメタ自己改善レポート）をそのままユーザーに提示してください。

メタモード実行時に meta-retrospector からユーザー承認を求める問いかけが含まれていた場合、ユーザーの応答をそのまま meta-retrospector に差し戻して処理を継続してください（必要に応じて再度 meta-retrospector を起動します）。
