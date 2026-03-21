# IR — Implement → Review

軽量ワークフローを実行します。プランニング・振り返りなしで、小さいタスクに使います。

**タスク**: $ARGUMENTS

---

## ステップ 0: プロジェクトメモリパスの確認

```bash
claude_dir="${HOME}/.claude/projects/$(pwd | sed 's|/|-|g')/memory"
echo "$claude_dir"
```

取得したパスを `PROJECT_MEMORY_DIR` として以降のすべてのステップで使用してください。

---

## ステップ 1: 実装 (Sonnet)

`implementer` サブエージェントを起動してください。

- Agent ツールで `implementer` エージェントを起動する
- model: `sonnet`
- プロンプト: PROJECT_MEMORY_DIR と以下を渡す
  - タスク内容（$ARGUMENTS）
  - 「プランなしで直接実装してください」

実装完了レポートを受け取ったら次のステップへ進んでください。

---

## ステップ 2: レビュー (Sonnet)

`reviewer` サブエージェントを起動してください。

- Agent ツールで `reviewer` エージェントを起動する
- model: `sonnet`
- プロンプト: PROJECT_MEMORY_DIR と実装完了レポート（変更ファイル一覧を含む）を渡す

`VERDICT: PASS` または `VERDICT: FAIL` を受け取ってください。

---

## ステップ 3: レビューループ (最大2回)

**LOOP_COUNT = 0 から始めてください。**

`VERDICT: FAIL` の場合:

1. LOOP_COUNT を 1 増やす
2. LOOP_COUNT が 2 に達した場合はループを終了してステップ4へ進む
3. `implementer` を再起動する
   - プロンプト: PROJECT_MEMORY_DIR・レビューの「次のアクション」セクション・元のタスクを渡す
4. `reviewer` を再起動して VERDICT を確認する
5. FAIL なら繰り返す

`VERDICT: PASS` になったらステップ4へ進んでください。

---

## ステップ 4: 最終サマリーの提示

```
## IR 完了サマリー

### タスク
[タスクの説明]

### 変更ファイル
[実装完了レポートから抜粋]

### レビュー結果
- 最終 VERDICT: [PASS/FAIL]
- ループ回数: [LOOP_COUNT]
- [主な指摘事項があれば記載]
```
