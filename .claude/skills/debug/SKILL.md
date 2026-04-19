---
name: debug
description: エラーや不具合を診断して修正する。症状・エラーメッセージを受け取り根本原因を特定してから修正する。「動かない」「壊れた」「エラーが出る」「なぜか失敗する」やスタックトレース・エラーログが貼られたときにも使う。ユーザーが /debug と入力したら必ずこのスキルを使う。
argument-hint: [症状やエラーメッセージ]
---

# Debug — 診断 → 実装 → レビュー

エラーや不具合を診断し修正します。このスキル本体（= メイン Claude）がオーケストレーターとなり、`explorer` / `planner` / `implementer` / `reviewer` を `Agent` ツールで順に起動します。サブエージェント内からの Agent 呼び出しは Claude Code の設計上不可能なため、起動責任はスキル本体に集約されます。

**症状**: $ARGUMENTS

---

## ステップ 0: プロジェクトメモリパスの確認

```bash
claude_dir="${HOME}/.claude/projects/$(pwd | sed 's|/|-|g')/memory"
echo "PROJECT_MEMORY_DIR=$claude_dir"
echo "PROJECT_ROOT=$(pwd)"
run_ts="$(date +%Y%m%d-%H%M%S)"
run_feature="$(echo "$ARGUMENTS" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
[ -z "$run_feature" ] && run_feature="task"
RUN_DIR="${claude_dir}/pir_runs/${run_ts}-${run_feature}"
mkdir -p "$RUN_DIR"
echo "RUN_DIR=$RUN_DIR"
```

取得したパスを `PROJECT_MEMORY_DIR` および `RUN_DIR` として以降のすべてのステップで使用してください。

---

## ステップ 1: 探索 (explorer)

planner はプラン策定専任でありコードベース探索はできない。スキル本体（メイン Claude）が `explorer` サブエージェントを `Agent` ツールで起動し、症状の周辺コードを調査させてください。

- model は explorer 側の定義に従う
- プロンプトに以下を含める:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `EXPLORATION_INDEX=01`
  - 「探索レポート本体は `{RUN_DIR}/exploration-01.md` に書き出し、チャットには要約のみ返してください」
  - 症状・エラーメッセージ（$ARGUMENTS）
  - 「症状に関連するコード・エントリポイント・エラーメッセージの発生源を特定し、呼び出し経路と関連する既存実装パターンを含む探索レポートを返す」
  - 必要に応じて WebFetch/WebSearch で外部ドキュメント（ライブラリ挙動・類似 Issue 等）も裏取りする

探索レポート要約を受け取ったら次のステップへ進んでください。

---

## ステップ 2: 診断・修正プラン (Opus)

スキル本体（メイン Claude）が `planner` サブエージェントを `Agent` ツールで起動してください。

- model: `opus`
- プロンプトに以下を含める:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - 症状・エラーメッセージ（$ARGUMENTS）
  - `{RUN_DIR}/exploration-*.md` のパス一覧（planner は本文を自分で Read する）
  - 「これはデバッグタスクです。探索レポートをもとに根本原因を特定し、修正プランを作成してください。」
  - 「プランの冒頭に『## 診断: [根本原因]』セクションを追加してください。」
  - 「プランレポート本体は `{RUN_DIR}/plan.md` に書き出し、チャットには要約＋EXPLORATION_NEEDED の有無のみ返してください」

プラン要約を受け取ったら次のステップへ進んでください。

---

## ステップ 2.5: 能動的再探索ループ（最大5回）

planner の返り値要約に `### EXPLORATION_NEEDED` セクションがあり、かつ箇条書き項目（`- topic`）が1件以上含まれる（`- なし` 単独でない）場合、追加探索 → planner 再起動を繰り返す。

`REPLAN_COUNT = 0` から開始。

### 収束判定ロジック

planner の返り値要約テキストの `### EXPLORATION_NEEDED` セクションを見る:
- 見出しが存在しない、または直下が「なし」「- なし」のみ → **収束**。ステップ 3 へ進む
- `- topic` 形式の項目が1件以上列挙されている → 追加探索へ

### ループ本体

1. `REPLAN_COUNT += 1`
2. `REPLAN_COUNT > 5` に到達した場合、ループを強制終了してステップ 3 へ進む。最終サマリー（ステップ6）に「**planner が依然追加探索を要求中（ハードキャップ5回到達）**: [topic 一覧]」と明記する
3. planner が出した各 topic ごとに explorer を起動する（topic が独立なら最大3体並列）:
   - `EXPLORATION_INDEX` は `{RUN_DIR}/exploration-*.md` 既存ファイルの最大連番 + 1 から割り振る
   - プロンプトには topic 本文と共に「この topic の調査に集中する。既存探索レポート（`{RUN_DIR}/exploration-*.md` 参照可）の重複調査は不要」と指示
4. 追加探索が完了したら planner を再起動する:
   - プロンプトは初回と同じだが、`{RUN_DIR}/exploration-*.md` のパス一覧に新しく追加されたものも含める
   - `plan.md` は上書き更新される（planner は同じパスに Write する）
5. planner の新しい返り値要約の EXPLORATION_NEEDED をチェック → 収束していればステップ 3 へ、まだ要求が残っていれば 1. に戻る

---

## ステップ 3: 実装 (Sonnet)

スキル本体（メイン Claude）が `implementer` サブエージェントを `Agent` ツールで起動してください。

- model: `sonnet`
- プロンプト:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `IMPL_INDEX=01`（初回。再実装時は呼び出し元がインクリメント）
  - `{RUN_DIR}/plan.md` のパス（implementer が Read する）
  - 「実装完了レポート本体は `{RUN_DIR}/implementation-{IMPL_INDEX}.md` に書き出し、チャットには要約のみ返してください」

実装要約を受け取ったら次のステップへ進んでください。

---

## ステップ 4: レビュー (Sonnet)

スキル本体（メイン Claude）が `reviewer` サブエージェントを `Agent` ツールで起動してください。

- model: `sonnet`
- プロンプト:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `REVIEW_INDEX=01`（初回。再レビュー時はインクリメント）
  - `{RUN_DIR}/plan.md` のパス
  - `{RUN_DIR}/implementation-{最新 IMPL_INDEX}.md` のパス
  - 「レビューレポート本体は `{RUN_DIR}/review-{REVIEW_INDEX}.md` に書き出し、チャットには VERDICT + 要約のみ返してください」

`VERDICT: PASS` または `VERDICT: FAIL` を受け取ってください。

---

## ステップ 5: レビューループ (最大2回)

**LOOP_COUNT = 0 から始めてください。**

`VERDICT: FAIL` の場合:

1. `LOOP_COUNT += 1`
2. `LOOP_COUNT >= 2` に達した場合はループを終了してステップ6へ進む
3. `implementer` を再起動する（`IMPL_INDEX` をインクリメント、`{RUN_DIR}/review-{最新}.md` のパスをレビュー指摘事項として渡す、`{RUN_DIR}/plan.md` のパスも渡す）
4. `reviewer` を再起動して VERDICT を確認する（`REVIEW_INDEX` をインクリメント、最新の `{RUN_DIR}/implementation-{最新}.md` のパスを渡す）
5. FAIL なら繰り返す

`VERDICT: PASS` になったらステップ6へ進んでください。

---

## ステップ 5.5: メモリへの記録

`PROJECT_MEMORY_DIR` 配下にタスクの振り返り材料を追記します:

- まず `mkdir -p {PROJECT_MEMORY_DIR}` でディレクトリを作成
- パス: `{PROJECT_MEMORY_DIR}/pir_skill_log.md`
- フォーマット: `## [タスク名] — [気づき・課題・パターン]`

---

## ステップ 6: 最終サマリーの提示

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

### 作業ディレクトリ
{RUN_DIR}
```
