---
name: "tester"
description: "実装済みコードの動作を検証する。既存テストの実行とアドホックな動作確認を行い VERDICT: PASS/FAIL を返す。「テストして」「動作確認して」「ちゃんと動く？」「test it」といった要望や、実装直後の検証にも使う。ユーザーが /tester と入力したら必ずこのスキルを使う。"
argument-hint: "[検証対象の説明]"
---

# Tester — 動作検証

実装済みコードの動作を検証します。このスキル本体（= メイン Codex）がオーケストレーターとなり、`list_agents` で実行中の体数を確認してから `spawn_agent` で `agent_type="tester"` を起動します。subagentから別の制御 role を起動せず、起動責任はスキル本体に集約されます。

**検証対象（省略時は直近の実装）**: $ARGUMENTS

---

## ステップ 0: メモリパスの解決

```bash
project_memory_dir="${HOME}/.codex/projects/$(pwd | sed 's|/|-|g')/memory"
echo "$project_memory_dir"
```

---

## ステップ 1: 動作検証

スキル本体（メイン Codex）が `tester` role を `spawn_agent` で起動してください。

- model は `.codex/agents/tester.toml` の role 定義に委ね、呼び出し側では上書きしないでください。
- プロンプトに以下を含める:
  - PROJECT_MEMORY_DIR（ステップ0で取得したパス）
  - 検証対象（`$ARGUMENTS` で指定された内容、または直近の実装内容）
  - 「これは手動トリガーのテストです。変更ファイルを確認し、テストを実行してください。」
  - 「テスト結果を報告した後、テストデータのクリーンアップはユーザーから明示的に指示されるまで実行しないこと。」

---

## ステップ 2: 結果の提示

tester の VERDICT と検証結果をそのままユーザーに提示してください。
