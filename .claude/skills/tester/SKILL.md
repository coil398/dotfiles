---
name: tester
description: 実装済みコードの動作を検証する。既存テストの実行とアドホックな動作確認を行い VERDICT: PASS/FAIL を返す。ユーザーが /tester と入力したら必ずこのスキルを使う。
---

# Tester — 動作検証

実装済みコードの動作を検証します。

**検証対象（省略時は直近の実装）**: $ARGUMENTS

---

## ステップ 0: メモリパスの解決

```bash
claude_dir="${HOME}/.claude/projects/$(pwd | sed 's|/|-|g')/memory"
echo "$claude_dir"
```

---

## ステップ 1: 動作検証

`tester` サブエージェントを起動してください。

- Agent ツールで `tester` エージェントを起動する
- model: `sonnet`
- プロンプトに以下を含める:
  - PROJECT_MEMORY_DIR（ステップ0で取得したパス）
  - 検証対象（`$ARGUMENTS` で指定された内容、または直近の実装内容）
  - 「これは手動トリガーのテストです。変更ファイルを確認し、テストを実行してください。」

---

## ステップ 2: 結果の提示

tester の VERDICT と検証結果をそのままユーザーに提示してください。
