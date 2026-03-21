# Retro — パターン汎化・エージェント改善

蓄積されたログをもとにパターンを汎化し、エージェント定義を改善します。

**対象プロジェクト（省略時は現在のディレクトリ）**: $ARGUMENTS

---

## ステップ 0: メモリパスの解決

以下のコマンドでパスを取得してください:

```bash
# 対象ディレクトリの決定
TARGET_DIR="${ARGUMENTS:-$(pwd)}"

# プロジェクトメモリパス
PROJECT_MEMORY_DIR="${HOME}/.claude/projects/$(echo $TARGET_DIR | sed 's|/|-|g')/memory"

echo "PROJECT_MEMORY_DIR: $PROJECT_MEMORY_DIR"
```

---

## ステップ 1: retrospector の起動 (Opus)

`retrospector` サブエージェントを起動してください。

- Agent ツールで `retrospector` エージェントを起動する
- model: `opus`
- プロンプトに以下を含める:
  - PROJECT_MEMORY_DIR（ステップ0で取得したパス）
  - LOOP_COUNT: 0（手動実行のためループなし）
  - VERDICT: MANUAL（手動実行トリガー）
  - 「これは手動トリガーの振り返りです。蓄積されたログを全件読み込み、パターンの汎化を積極的に行ってください。」

---

## ステップ 2: 結果の提示

retrospector の振り返りレポートをそのままユーザーに提示してください。
