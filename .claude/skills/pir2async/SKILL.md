---
name: pir2async
description: PIR²のAgent Teams版。implementerとreviewerをチーム化し直接対話させることで、伝言ゲームの情報ロスを排除する実験的ワークフロー。通常の/pir2との品質比較用。
argument-hint: [タスクの説明]
---

# PIR² Async — Agent Teams 版 Plan → Implement → Review → Retrospect

PIR²ワークフローのAgent Teams実験版です。implementerとreviewerをチーム化し、直接対話でレビューループを回します。
以下の手順を**順番に**実行してください。

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

該当しない場合はスキップしてください。

---

## ステップ 3: プランニング (Opus)

`planner` サブエージェントを使って実装プランのみを作成してください。

- Agent ツールで `planner` エージェントを起動する
- model: `opus`
- プロンプト: PROJECT_MEMORY_DIR と上記タスクを渡す。以下の指示を必ず含める:
  「フェーズ1（探索とプラン策定）のみを実行し、プラン出力フォーマットで返してください。フェーズ2以降（実装・レビュー・テスト・ウォークスルー）は実行しないでください。pir2async がチームで実装・レビューを制御します。」

プランを受け取ったら、`docs/plans/` に `YYYY-MM-DD-<feature>.md` として保存し、ユーザーに提示してください。
フォーマットは通常の PIR² と同じ（目標・実装計画・設計詳細・実装ログ）。

---

**INNER_LOOP_COUNT = 0、OUTER_LOOP_COUNT = 0 から始めてください。**

## ステップ 4: 実装+レビュー チーム起動

ここが通常の PIR² との違いです。implementer と reviewer を **Agent Teams** として起動し、直接対話させます。

### 4-1: チーム作成

TeamCreate ツールでチームを作成してください:

```
team_name: "impl-review"
description: "実装とレビューのチーム。implementerが実装し、reviewerが直接レビューしてフィードバックする。"
```

### 4-2: チームメイト起動

以下の2つの Agent を**並列で**起動してください。両方とも `team_name: "impl-review"` を指定します。

#### implementer (name: "implementer")

```
subagent_type: implementer
team_name: impl-review
name: implementer
model: sonnet
```

プロンプト:

```
あなたは impl-review チームの implementer です。

PROJECT_MEMORY_DIR=[パス]

## タスク
以下のプランに基づいて実装してください:
[ステップ3のプラン全文]

## チームでの作業手順

1. プランに基づいて実装を行う
2. 実装が完了したら、チームメイトの "reviewer" に SendMessage で以下を送る:
   - 変更したファイル一覧
   - 実装内容の概要
   - 「レビューお願いします」
3. reviewer から修正指示が来たら、その指示に従って修正する
4. 修正完了後、再度 reviewer に SendMessage でレビュー依頼する
5. reviewer から「VERDICT: PASS」を受け取ったら、チームリードに SendMessage で以下を送る:
   - 最終的な変更ファイル一覧
   - 実装内容の概要
   - レビューループの回数
   - 「実装+レビュー完了」

## 重要
- reviewer との直接対話でレビューループを回すこと
- チームリードへの報告は PASS 後のみ
- プラン外の変更は行わない
```

#### reviewer (name: "reviewer")

```
subagent_type: reviewer
team_name: impl-review
name: reviewer
model: sonnet
```

プロンプト:

```
あなたは impl-review チームの reviewer です。

PROJECT_MEMORY_DIR=[パス]

## チームでの作業手順

1. チームメイトの "implementer" からレビュー依頼メッセージを待つ
2. メッセージを受け取ったら、変更ファイルを Read して通常のレビュー観点でレビューする
3. レビュー結果を implementer に SendMessage で直接送る:
   - VERDICT: PASS または VERDICT: FAIL
   - FAIL の場合: 問題一覧と具体的な修正指示
   - PASS の場合: 良好点があれば記載
4. FAIL の場合、implementer からの修正完了メッセージを待って再レビューする
5. レビューループは最大3回まで。3回 FAIL したら最後の VERDICT を記録してチームリードに報告する

## レビュー観点
通常の reviewer と同じ:
1. バグ・正確性（ロジックエラー、エッジケース、null処理）
2. セキュリティ（インジェクション、OWASP Top 10）
3. パフォーマンス（N+1、不要なアロケーション）
4. 保守性（複雑度、重複、テストカバレッジ）
5. テストの質
6. 命名規則・構造の一貫性

## 判定基準
- PASS: Critical・High の問題がない場合
- FAIL: Critical または High の問題が1件以上ある場合

## 重要
- implementer と直接対話すること（チームリード経由ではない）
- レビューログを PROJECT_MEMORY_DIR/pir_reviewer_log.md に記録する
```

### 4-3: チーム完了待ち

implementer から「実装+レビュー完了」の報告を待ちます。報告を受け取ったら:

1. INNER_LOOP_COUNT を報告されたレビューループ回数で更新する
2. ドキュメントの実装ログに追記する
3. 両チームメイトに shutdown_request を送る
4. ステップ 5 へ進む

---

## ステップ 5: テスト (Sonnet)

通常の PIR² と同じ。`tester` サブエージェントを使って実装の動作を検証してください。

- Agent ツールで `tester` エージェントを起動する（チーム外、通常の Agent）
- model: `sonnet`
- プロンプト: PROJECT_MEMORY_DIR・実装完了レポート（変更ファイル一覧を含む）・元のプランを渡す

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
2. OUTER_LOOP_COUNT が 3 に達した場合はループを終了し、ステップ6へ進む（失敗として記録）
3. INNER_LOOP_COUNT を 0 にリセット
4. **ステップ 4 に戻る**（impl-review チームを再作成して実装+レビューループを再実行）
5. テスターの「次のアクション」セクションを implementer への追加指示としてプロンプトに含める

---

## ステップ 6: 振り返り (常に実行)

通常の PIR² と同じ。`retrospector` サブエージェントを起動してください:

- Agent ツールで `retrospector` エージェントを起動する
- model: `INNER_LOOP_COUNT が 0 かつ OUTER_LOOP_COUNT が 0 の場合は sonnet`、いずれかが 1 以上の場合は `opus`
- プロンプト: 以下の情報をすべて渡す
  - PROJECT_MEMORY_DIR
  - PROJECT_ROOT
  - INNER_LOOP_COUNT
  - OUTER_LOOP_COUNT
  - すべてのレビュー指摘事項
  - テスターの指摘事項
  - 最終的な VERDICT
  - **ワークフロー種別: pir2async**（通常の pir2 との比較用に記録）

---

## ステップ 7: 最終サマリーの提示

以下の内容をユーザーに提示してください:

```
## PIR² Async 完了サマリー

### タスク
[タスクの説明]

### ワークフロー
pir2async (Agent Teams版 — implementer+reviewer チーム化)

### 実装記録
docs/plans/YYYY-MM-DD-<feature>.md

### 変更ファイル
[実装完了レポートから抜粋]

### レビュー結果
- 最終 VERDICT: [PASS/FAIL]
- レビューループ回数 (チーム内): [INNER_LOOP_COUNT]
- [主な指摘事項があれば記載]

### テスト結果
- テスト VERDICT: [PASS/FAIL]
- 外側ループ回数: [OUTER_LOOP_COUNT]

### 振り返り
[retrospectorの改善内容の要約]

### 通常版 PIR² との比較ポイント
- レビューループ回数の違い
- 指摘の質・粒度の違い
- チーム内対話で解決された問題（あれば）
```
