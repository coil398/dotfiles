---
name: debug
description: エラーや不具合を診断して修正する。症状・エラーメッセージを受け取り根本原因を特定してから修正する。ユーザーが /debug と入力したら必ずこのスキルを使う。
---

# Debug — 診断 → 実装 → レビュー

エラーや不具合を診断し修正します。

**症状**: $ARGUMENTS

---

## ステップ 0: プロジェクトメモリパスの確認

```bash
claude_dir="${HOME}/.claude/projects/$(pwd | sed 's|/|-|g')/memory"
echo "$claude_dir"
```

取得したパスを `PROJECT_MEMORY_DIR` として以降のすべてのステップで使用してください。

---

## ステップ 1: 診断・修正プラン (Opus)

`planner` サブエージェントを起動してください。

- Agent ツールで `planner` エージェントを起動する
- model: `opus`
- プロンプトに以下を含める:
  - PROJECT_MEMORY_DIR
  - 症状・エラーメッセージ（$ARGUMENTS）
  - 「これはデバッグタスクです。まず原因を特定し、次に修正プランを作成してください。」
  - 「プランの冒頭に『## 診断: [根本原因]』セクションを追加してください。」

プランを受け取ったら次のステップへ進んでください。

---

## ステップ 2: 実装 (Sonnet)

`implementer` サブエージェントを起動してください。

- Agent ツールで `implementer` エージェントを起動する
- model: `sonnet`
- プロンプト: PROJECT_MEMORY_DIR とステップ1の修正プランを渡す

実装完了レポートを受け取ったら次のステップへ進んでください。

---

## ステップ 3: レビュー (Sonnet)

`reviewer` サブエージェントを起動してください。

- Agent ツールで `reviewer` エージェントを起動する
- model: `sonnet`
- プロンプト: PROJECT_MEMORY_DIR と実装完了レポート（変更ファイル一覧を含む）を渡す

`VERDICT: PASS` または `VERDICT: FAIL` を受け取ってください。

---

## ステップ 4: レビューループ (最大2回)

**LOOP_COUNT = 0 から始めてください。**

`VERDICT: FAIL` の場合:

1. LOOP_COUNT を 1 増やす
2. LOOP_COUNT が 2 に達した場合はループを終了してステップ5へ進む
3. `implementer` を再起動する
   - プロンプト: PROJECT_MEMORY_DIR・レビューの「次のアクション」セクション・元のプランを渡す
4. `reviewer` を再起動して VERDICT を確認する
5. FAIL なら繰り返す

`VERDICT: PASS` になったらステップ5へ進んでください。

---

## ステップ 5: 最終サマリーの提示

```
## Debug 完了サマリー

### 症状
[入力された症状]

### 診断
[根本原因]

### 変更ファイル
[実装完了レポートから抜粋]

### レビュー結果
- 最終 VERDICT: [PASS/FAIL]
- ループ回数: [LOOP_COUNT]
- [主な指摘事項があれば記載]
```
