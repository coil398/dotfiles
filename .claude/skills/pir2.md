# PIR² — Plan → Implement → Review → Retrospect

PIR²ワークフローを実行します。以下の手順を**順番に**実行してください。

**タスク**: $ARGUMENTS

---

## ステップ 0: プロジェクトメモリパスの確認

以下の Bash コマンドで現在のプロジェクトメモリパスを取得し、`PROJECT_MEMORY_DIR` として以降のすべてのステップで使用してください:

```bash
claude_dir="${HOME}/.claude/projects/$(pwd | sed 's|/|-|g')/memory"
echo "$claude_dir"
```

以降の各サブエージェントへのプロンプトには必ず `PROJECT_MEMORY_DIR=[パス]` を含めてください。

---

## ステップ 1: プランニング (Opus)

`planner` サブエージェントを使って実装プランを作成してください。

- Agent ツールで `planner` エージェントを起動する
- model: `opus`
- プロンプト: PROJECT_MEMORY_DIR と上記タスクを渡す

プランを受け取ったら次のステップへ進んでください。

---

## ステップ 2: 実装 (Sonnet)

`implementer` サブエージェントを使ってプランを実装してください。

- Agent ツールで `implementer` エージェントを起動する
- model: `sonnet`
- プロンプト: PROJECT_MEMORY_DIR とステップ1で作成したプランを渡す

実装完了レポートを受け取ったら次のステップへ進んでください。

---

## ステップ 3: レビュー (Sonnet)

`reviewer` サブエージェントを使って実装をレビューしてください。

- Agent ツールで `reviewer` エージェントを起動する
- model: `sonnet`
- プロンプト: PROJECT_MEMORY_DIR とステップ2の実装完了レポートを渡す（変更ファイル一覧を含む）

`VERDICT: PASS` または `VERDICT: FAIL` を受け取ってください。

---

## ステップ 4: レビューループ (最大3回)

**LOOP_COUNT = 0 から始めてください。**

`VERDICT: FAIL` の場合:

1. LOOP_COUNT を 1 増やす
2. LOOP_COUNT が 3 に達した場合（LOOP_COUNT = 3）はループを終了し、**ステップ5（retrospector）へ進む**
3. `implementer` サブエージェントを再度起動する
   - プロンプト: PROJECT_MEMORY_DIR・レビューの指摘事項（「次のアクション」セクション）・元のプランを渡す
4. 実装完了後、`reviewer` サブエージェントを再度起動する
   - プロンプト: PROJECT_MEMORY_DIR・最新の実装完了レポートを渡す（変更ファイル一覧を含む）
5. 再び `VERDICT` を確認し、FAIL なら繰り返す

`VERDICT: PASS` になったらステップ5へ進んでください。

---

## ステップ 5: 振り返り (常に実行)

`retrospector` サブエージェントを起動してください:

- Agent ツールで `retrospector` エージェントを起動する
- model: LOOP_COUNT が 0 の場合は `sonnet`、1 以上の場合は `opus`
- プロンプト: 以下の情報をすべて渡す
  - PROJECT_MEMORY_DIR（ステップ0で取得したパス）
  - LOOP_COUNT
  - すべてのレビュー指摘事項（各ループのレビュー結果）
  - 最終的な VERDICT

---

## ステップ 6: 最終サマリーの提示

以下の内容をユーザーに提示してください:

```
## PIR² 完了サマリー

### タスク
[タスクの説明]

### 変更ファイル
[実装完了レポートから抜粋]

### レビュー結果
- 最終 VERDICT: [PASS/FAIL]
- ループ回数: [LOOP_COUNT]
- [主な指摘事項があれば記載]

### 振り返り
[retrospectorの改善内容の要約]
```
