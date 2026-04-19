---
name: retro
description: retrospector を単体で実行してパターンを汎化しエージェント定義を改善する。振り返り・ふりかえり・retrospective・改善サイクル・エージェント定義の見直し・パターン分析をしたいときに使う。`--meta` フラグでワークフロー骨格を改善するメタ自己改善モードを起動できる。ユーザーが /retro と入力したら必ずこのスキルを使う。
argument-hint: [--meta] [対象プロジェクトのパス]
---

# Retro — パターン汎化・エージェント改善

蓄積されたログをもとにパターンを汎化し、エージェント定義を改善します。このスキル本体（= メイン Claude）がオーケストレーターとなり、`retrospector` を `Agent` ツールで起動します。サブエージェント内からの Agent 呼び出しは Claude Code の設計上不可能なため、起動責任はスキル本体に集約されます。
`--meta`（または `meta`）フラグが指定された場合、ワークフロー骨格そのものを改善するメタ自己改善モードを起動します。

引数: $ARGUMENTS

---

## ステップ 0a: 引数解釈

`$ARGUMENTS` を bash で解釈し、メタモードフラグとプロジェクトパスを分離してください:

```bash
ARGS="$ARGUMENTS"
META_MODE=false
PROJECT_PATH=""

for token in $ARGS; do
  case "$token" in
    --meta|meta)
      META_MODE=true
      ;;
    *)
      if [ -z "$PROJECT_PATH" ]; then
        PROJECT_PATH="$token"
      fi
      ;;
  esac
done

echo "META_MODE=$META_MODE"
echo "PROJECT_PATH=${PROJECT_PATH:-$(pwd)}"
```

- `META_MODE=true` の場合はステップ0b・1・2を実行する
- `META_MODE=false` の場合は従来どおりステップ0b・1・2を実行する（プロセスは retrospector 側で分岐）

後方互換: 従来どおり第1引数にプロジェクトパスだけを渡す呼び出しは引き続き動作する。

---

## ステップ 0b: メモリパスの解決

`PROJECT_PATH` を基点にメモリパスを解決してください（指定がなければ現在のディレクトリ）:

```bash
target_path="${PROJECT_PATH:-$(pwd)}"
claude_dir="${HOME}/.claude/projects/$(echo "$target_path" | sed 's|/|-|g')/memory"
echo "PROJECT_MEMORY_DIR=$claude_dir"
echo "PROJECT_ROOT=$target_path"
```

---

## ステップ 1: retrospector の起動

スキル本体（メイン Claude）が `retrospector` サブエージェントを `Agent` ツールで起動してください。

- model: `opus`
- プロンプトに以下を含める:
  - `PROJECT_MEMORY_DIR`（ステップ0bで取得したパス）
  - `PROJECT_ROOT`（ステップ0bで取得したパス）
  - `META_MODE=[true|false]`（ステップ0aで決定した値）
  - `INNER_LOOP_COUNT=0`
  - `OUTER_LOOP_COUNT=0`
  - `VERDICT=MANUAL`
  - 通常モード時: 「これは手動トリガーの振り返りです。蓄積されたログを全件読み込み、パターンの汎化を積極的に行ってください。」
  - メタモード時: 「これはメタ自己改善モードの手動トリガーです。レジストリの未処理メタ改善推奨フラグを読み込み、ワークフロー骨格の改善提案を作成してください。バックアップ・ユーザー承認・個別ファイル指定の commit を必ず行ってください。」

---

## ステップ 2: 結果の提示

retrospector の振り返りレポート（通常モードなら振り返りレポート、メタモードならメタ自己改善レポート）をそのままユーザーに提示してください。

メタモード実行時に retrospector からユーザー承認を求める問いかけが含まれていた場合、ユーザーの応答をそのまま retrospector に差し戻して処理を継続してください（必要に応じて再度 retrospector を起動します）。
