---
name: pir2
description: コーディングタスクを Plan → Implement → Review → Retrospect の4フェーズで実行する。複雑なタスク・設計が必要なタスク・品質保証が重要なタスクに使う。ユーザーが /pir2 と入力したら必ずこのスキルを使う。
---

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

## ステップ 0.5: ブレインストーミング（状況に応じて実施）

タスクの仕様を評価し、以下のいずれかに該当する場合は `/brainstorm` スキルを実行してからステップ1へ進んでください：

- 要件が曖昧で複数の解釈が可能
- アーキテクチャ上の選択肢が複数あり、どれを選ぶかユーザーに確認が必要
- ユーザーとの対話を通じて設計を固めたほうが手戻りリスクを減らせると判断される

該当しない場合（タスクが明確、既存の設計がある、`docs/brainstorm/` に関連する設計ドキュメントが存在する）は**スキップ**してください。

---

## ステップ 1: プランニング (Opus)

`planner` サブエージェントを使って実装プランを作成してください。

- Agent ツールで `planner` エージェントを起動する
- model: `opus`
- プロンプト: PROJECT_MEMORY_DIR と上記タスクを渡す。`docs/brainstorm/` に設計ドキュメントがある場合はそのパスも渡す

プランを受け取ったら、`docs/plans/` ディレクトリがなければ作成し、以下の形式でドキュメントを保存してください：

**保存先**: `docs/plans/YYYY-MM-DD-<feature>.md`（YYYY-MM-DD は今日の日付）

```markdown
# [タスク名] 実装記録

_作成: YYYY-MM-DD | ステータス: 進行中_

## 目標

[タスクの概要]

## 実装計画

[plannerが作成したステップ一覧を [ ] チェックボックス形式で記載]

---

## 実装ログ

<!-- 各ステップ完了時に追記される -->
```

---

**INNER_LOOP_COUNT = 0、OUTER_LOOP_COUNT = 0 から始めてください。**

## ステップ 2: 実装 (Sonnet)

`implementer` サブエージェントを使ってプランを実装してください。

- Agent ツールで `implementer` エージェントを起動する
- model: `sonnet`
- プロンプト: PROJECT_MEMORY_DIR とステップ1で作成したプランを渡す

実装完了レポートを受け取ったら、ドキュメントを更新してください：

1. 計画セクションの `[ ]` を `[x]` に変更
2. 実装ログセクションに追記：

```markdown
### 実装完了

- 変更ファイル: [一覧]
- 実装内容: [概要]
```

---

## ステップ 3: レビュー (Sonnet)

`reviewer` サブエージェントを使って実装をレビューしてください。

- Agent ツールで `reviewer` エージェントを起動する
- model: `sonnet`
- プロンプト: PROJECT_MEMORY_DIR とステップ2の実装完了レポートを渡す（変更ファイル一覧を含む）

`VERDICT: PASS` または `VERDICT: FAIL` を受け取ってください。

---

## ステップ 4: レビューループ (最大3回)

**INNER_LOOP_COUNT = 0 から始めてください。**

`VERDICT: FAIL` の場合:

1. INNER_LOOP_COUNT を 1 増やす
2. INNER_LOOP_COUNT が 3 に達した場合（INNER_LOOP_COUNT = 3）はループを終了し、**ステップ5（テスト）へ強制移行する**
3. `implementer` サブエージェントを再度起動する
   - プロンプト: PROJECT_MEMORY_DIR・レビューの指摘事項（「次のアクション」セクション）・元のプランを渡す
4. 実装完了後、ドキュメントの実装ログに追記する
5. `reviewer` サブエージェントを再度起動する
   - プロンプト: PROJECT_MEMORY_DIR・最新の実装完了レポートを渡す（変更ファイル一覧を含む）
6. 再び `VERDICT` を確認し、FAIL なら繰り返す

`VERDICT: PASS` になったらステップ5へ進んでください。

---

## ステップ 5: テスト (Sonnet)

`tester` サブエージェントを使って実装の動作を検証してください。

- Agent ツールで `tester` エージェントを起動する
- model: `sonnet`
- プロンプト: PROJECT_MEMORY_DIR・ステップ2の実装完了レポート（変更ファイル一覧を含む）・元のプランを渡す

`VERDICT: PASS` の場合:

ドキュメントのヘッダーを更新してステップ6へ進んでください：

```markdown
_作成: YYYY-MM-DD | ステータス: **完了** YYYY-MM-DD_
```

末尾に以下を追加：

```markdown
> **このドキュメントは内容を確認後に削除してください。**
> `rm docs/plans/YYYY-MM-DD-<feature>.md`
```

`VERDICT: FAIL` の場合:

1. OUTER_LOOP_COUNT を 1 増やす
2. OUTER_LOOP_COUNT が 3 に達した場合（OUTER_LOOP_COUNT = 3）はループを終了し、**ステップ6（振り返り）へ進む**（失敗として記録）
3. INNER_LOOP_COUNT を 0 にリセット
4. `implementer` サブエージェントを再度起動する
   - プロンプト: PROJECT_MEMORY_DIR・テスターの「次のアクション」セクション・元のプランを渡す
5. 実装完了後、ドキュメントの実装ログに追記する
6. `reviewer` サブエージェントを再度起動する
   - プロンプト: PROJECT_MEMORY_DIR・最新の実装完了レポートを渡す（変更ファイル一覧を含む）
7. INNER_LOOP_COUNT を管理しながら内側ループ（ステップ4と同様、max 3回）を実行する
8. 内側ループ PASS 後、再び `tester` を起動してテストを実行する
9. 再び `VERDICT` を確認し、FAIL なら OUTER_LOOP_COUNT をチェックしてから繰り返す

---

## ステップ 6: 振り返り (常に実行)

`retrospector` サブエージェントを起動してください:

- Agent ツールで `retrospector` エージェントを起動する
- model: `INNER_LOOP_COUNT が 0 かつ OUTER_LOOP_COUNT が 0 の場合は sonnet`、いずれかが 1 以上の場合は `opus`
- プロンプト: 以下の情報をすべて渡す
  - PROJECT_MEMORY_DIR（ステップ0で取得したパス）
  - INNER_LOOP_COUNT
  - OUTER_LOOP_COUNT
  - すべてのレビュー指摘事項（各ループのレビュー結果）
  - テスターの指摘事項
  - 最終的な VERDICT

---

## ステップ 7: 最終サマリーの提示

以下の内容をユーザーに提示してください:

```
## PIR² 完了サマリー

### タスク
[タスクの説明]

### 実装記録
docs/plans/YYYY-MM-DD-<feature>.md

### 変更ファイル
[実装完了レポートから抜粋]

### レビュー結果
- 最終 VERDICT: [PASS/FAIL]
- 内側ループ回数: [INNER_LOOP_COUNT]
- [主な指摘事項があれば記載]

### テスト結果
- テスト VERDICT: [PASS/FAIL]
- 外側ループ回数: [OUTER_LOOP_COUNT]

### 振り返り
[retrospectorの改善内容の要約]
```
