---
name: retro
description: retrospector を単体で実行してパターンを汎化しエージェント定義を改善する。振り返り・ふりかえり・retrospective・改善サイクル・エージェント定義の見直し・パターン分析をしたいときに使う。ユーザーが /retro と入力したら必ずこのスキルを使う。
argument-hint: [対象プロジェクトのパス]
---

# Retro — パターン汎化・エージェント改善

蓄積されたログをもとにパターンを汎化し、エージェント定義を改善します。

**対象プロジェクト（省略時は現在のディレクトリ）**: $ARGUMENTS

---

## ステップ 0: メモリパスの解決

以下のコマンドでパスを取得してください:

```bash
claude_dir="${HOME}/.claude/projects/$(pwd | sed 's|/|-|g')/memory"
echo "PROJECT_MEMORY_DIR=$claude_dir"
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
