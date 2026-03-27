---
name: pir2
description: コーディングタスクを Plan → Implement → Review → Retrospect の4フェーズで実行する。複雑なタスク・設計が必要なタスク・品質保証が重要なタスク、大きな機能追加・リファクタリング・アーキテクチャ変更に使う。「ちゃんと作りたい」「しっかり実装して」「品質重視で」といった要望にも対応する。ユーザーが /pir2 と入力したら必ずこのスキルを使う。
argument-hint: [タスクの説明]
---

# PIR² — Plan → Implement → Review → Retrospect

PIR²ワークフローを実行します。以下の手順を順番に実行してください。

**タスク**: $ARGUMENTS

---

## ステップ 1: プロジェクトメモリパスの確認

以下の Bash コマンドで現在のプロジェクトメモリパスとプロジェクトルートを取得し、以降のすべてのステップで使用してください:

```bash
claude_dir="${HOME}/.claude/projects/$(pwd | sed 's|/|-|g')/memory"
echo "PROJECT_MEMORY_DIR=$claude_dir"
echo "PROJECT_ROOT=$(pwd)"
```

以降の各サブエージェントへのプロンプトには必ず `PROJECT_MEMORY_DIR=[パス]` を含めてください。

---

## ステップ 2: ブレインストーミング（状況に応じて実施）

タスクの仕様を評価し、以下のいずれかに該当する場合は `/brainstorm` スキルを実行してからステップ3へ進んでください：

- 要件が曖昧で複数の解釈が可能
- アーキテクチャ上の選択肢が複数あり、どれを選ぶかユーザーに確認が必要
- ユーザーとの対話を通じて設計を固めたほうが手戻りリスクを減らせると判断される

該当しない場合（タスクが明確、既存の設計がある、`docs/brainstorm/` に関連する設計ドキュメントが存在する）はスキップしてください。

---

## ステップ 3: planner 起動（探索・プラン策定・実装・レビュー・テスト・ウォークスルー）

`planner` エージェントを起動してください。planner がオーケストレーターとして、探索からウォークスルーまでを一貫して制御します。

- Agent ツールで `planner` エージェントを起動する
- model: `opus`
- プロンプト: PROJECT_MEMORY_DIR・タスク内容を渡す。`docs/brainstorm/` に設計ドキュメントがある場合はそのパスも渡す

planner から統合レポートを受け取ってください。統合レポートには以下が含まれます:
- 実装プラン
- 実装結果（変更ファイル一覧）
- レビュー・テスト結果（VERDICT、INNER_LOOP_COUNT、OUTER_LOOP_COUNT）
- ウォークスルー

統合レポートを受け取ったら、`docs/plans/` ディレクトリがなければ作成し、以下の形式でドキュメントを保存してください：

**保存先**: `docs/plans/YYYY-MM-DD-<feature>.md`（YYYY-MM-DD は今日の日付）

ファイルを保存したら、すぐに以下の形式でパスをユーザーに提示してください：

```
プラン: docs/plans/YYYY-MM-DD-<feature>.md
```

```markdown
# [タスク名] 実装記録

_作成: YYYY-MM-DD | ステータス: 完了 YYYY-MM-DD_

## 目標

[タスクの概要]

## 実装計画

- [x] ステップ1: [ステップ名]
- [x] ステップ2: [ステップ名]
...

---

## 設計詳細

[plannerの統合レポートから実装プランセクションを転記]

---

## 実装ログ

### 実装完了

- 変更ファイル: [統合レポートの変更ファイル一覧]
- 実装内容: [概要]

---

> このドキュメントは内容を確認後に削除してください。
> `rm docs/plans/YYYY-MM-DD-<feature>.md`
```

統合レポートから INNER_LOOP_COUNT と OUTER_LOOP_COUNT を取得し、以降のステップで使用してください。

---

## ステップ 4: 振り返り (常に実行)

`retrospector` サブエージェントを起動してください:

- Agent ツールで `retrospector` エージェントを起動する
- model: `INNER_LOOP_COUNT が 0 かつ OUTER_LOOP_COUNT が 0 の場合は sonnet`、いずれかが 1 以上の場合は `opus`
- プロンプト: 以下の情報をすべて渡す
  - PROJECT_MEMORY_DIR（ステップ1で取得したパス）
  - PROJECT_ROOT（ステップ1で取得したパス）
  - INNER_LOOP_COUNT
  - OUTER_LOOP_COUNT
  - 統合レポートのレビュー・テスト結果セクション（指摘事項を含む）
  - 最終的な VERDICT

---

## ステップ 5: 最終サマリーの提示

以下の内容をユーザーに提示してください:

```
## PIR² 完了サマリー

### タスク
[タスクの説明]

### 実装記録
docs/plans/YYYY-MM-DD-<feature>.md

### 変更ファイル
[統合レポートから抜粋]

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

---

## ステップ 6: ウォークスルーの提示

planner の統合レポートに含まれる「ウォークスルー」セクションをユーザーに提示してください。

ウォークスルーが不十分な場合（コード片がない、理由が書かれていない等）は、変更ファイルを Read して補完してから提示すること。
