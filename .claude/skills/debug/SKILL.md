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
sh ~/.claude/lib/pir-preflight.sh "$ARGUMENTS"
```

出力フォーマット（5 行の `KEY=VALUE`）:
- `PROJECT_MEMORY_DIR=...`
- `PROJECT_ROOT=...`
- `RUN_DIR=...`
- `HANDOFF_PATH=...`
- `RESUME_MODE=new|resume|passive-notice`

`RESUME_MODE` に応じて挙動を分岐（詳細プロトコル: `~/.claude/pir-handoff.md`）:

- `resume`: planner に `HANDOFF_PATH` を渡し「未チェック項目のみ」と指示。handoff.md を上書きしない
- `passive-notice`: 「💡 前回の handoff が残っています: `$HANDOFF_PATH`」と表示し通常フロー
- `new`: 通常フロー。planner 完了直後にスキル本体が handoff.md 初期版を Write

retrospector 後、スキル本体は全 `[x]` なら handoff.md を削除、残項目ありなら「最終更新」を更新する。

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

## ステップ 2.8: handoff.md 初期版生成（`RESUME_MODE=new` の場合のみ）

`RESUME_MODE=resume` / `passive-notice` ならスキップ。`RESUME_MODE=passive-notice` だった場合は「💡 前回の handoff が残っています: `$HANDOFF_PATH`（`引継いで` で resume 可能）」とユーザーに表示。

`RESUME_MODE=new` の場合のみ:

1. `{RUN_DIR}/plan.md` を Read し、修正ステップを抽出
2. `$HANDOFF_PATH` に `~/.claude/pir-handoff.md` の「フォーマット」節に従って Write:
   - `最終更新` / `タスク` / `残 TODO`（各ステップを `- [ ] <ステップ名>`）/ `関連 artifact`

---

## ステップ 3: 実装 (Sonnet)

スキル本体（メイン Claude）が `implementer` サブエージェントを `Agent` ツールで起動してください。

- model: `sonnet`
- プロンプト:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `IMPL_INDEX=01`（初回。再実装時は呼び出し元がインクリメント）
  - `{RUN_DIR}/plan.md` のパス（implementer が Read する）
  - （`RESUME_MODE` が `new` または `resume` の場合のみ）`HANDOFF_PATH=$HANDOFF_PATH` と「実装完了した項目を handoff.md で `[x]` 化し、新規発見の TODO は追記すること。詳細: `~/.claude/pir-handoff.md`」
  - 「実装完了レポート本体は `{RUN_DIR}/implementation-{IMPL_INDEX}.md` に書き出し、チャットには要約のみ返してください」

実装要約を受け取ったら次のステップへ進んでください。

---

## ステップ 4: レビュー (Sonnet ハイブリッド並列)

### 4-1: REVIEWER_SET 決定（planner 系：全 5 観点がデフォルト）

`REVIEWER_SET` を決定する:

1. **ユーザーフラグのパース**: `$ARGUMENTS` に `--reviewers=<roles>` が含まれていればカンマ区切りを観点集合として採用（未知 role は無視）。`--all-reviewers` が含まれていれば全 5 観点を採用。両方指定時は `--reviewers=` を優先。フラグ抽出後の残りをタスク説明として扱う
2. **フラグ未指定時のデフォルト**: 全 5 観点 `[correctness, consistency, quality, security, architecture]`（planner が動くタスクは設計判断を含むため）
3. 決定した `REVIEWER_SET` を最終サマリーに記録

### 4-2: reviewer を並列起動

スキル本体（メイン Claude）が `reviewer` サブエージェントを `Agent` ツールで **REVIEWER_SET の観点数ぶん並列起動** してください。1メッセージ内に Agent ツール呼び出しを **観点数ぶん** 並べて同時発火させること（逐次起動は禁止）。各体は `REVIEWER_ROLE` を変えて担当観点を分割する:

> ⚠️ **完了条件チェック（厳守）**: このステップを完了したと判定する前に、以下を満たしているか必ず自己確認すること。1 つでも No なら違反であり、起動メッセージを送信せず構成し直す。
> - [ ] 同一の `<function_calls>` ブロックの中に Agent ツール呼び出しが `len(REVIEWER_SET)` 個ぶん並んでいるか？
> - [ ] 「とりあえず 1 体起動して残りは次のターンで」のような分割発火になっていないか？
> - [ ] 「軽いタスクだから 1 体でいい」「直前のレビューで 1 観点しか問題が出なかったから今回も 1 観点でいい」という独自判断で観点を減らしていないか？

- `REVIEWER_ROLE=correctness`: バグ・正確性 / パフォーマンス / リグレッション
- `REVIEWER_ROLE=consistency`: 命名規則・構造一貫性 / 同一ロジック全適用網羅性 / 類似ファイル群波及網羅性
- `REVIEWER_ROLE=quality`: 保守性（局所スコープ）/ テストの質 / データアクセス重複 / スコープ逸脱
- `REVIEWER_ROLE=security`: セキュリティ（OWASP）/ 認可・認証 / シークレット漏洩 / 依存脆弱性
- `REVIEWER_ROLE=architecture`: レイヤリング / 循環依存 / 責務逸脱 / 抽象粒度

各体の起動パラメータ:

- model: `sonnet`
- プロンプト（共通。`REVIEWER_ROLE` のみ変える）:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `REVIEW_INDEX=01`（初回。再レビュー時はインクリメント。起動する全体で同じ番号を共有する）
  - `REVIEWER_ROLE=[correctness|consistency|quality|security|architecture]`（体ごとに変える。REVIEWER_SET に含まれる観点のみ）
  - `{RUN_DIR}/plan.md` のパス
  - `{RUN_DIR}/implementation-{最新 IMPL_INDEX}.md` のパス
  - 「レビューレポート本体は `{RUN_DIR}/review-{REVIEW_INDEX}-{REVIEWER_ROLE}.md` に書き出し、チャットには VERDICT + 要約のみ返してください」

### VERDICT 集約

**今回起動した reviewer** の VERDICT を以下のルールで集約する:

- **全体 VERDICT = PASS**: 起動した全員が `VERDICT: PASS`
- **全体 VERDICT = FAIL**: 1体でも `VERDICT: FAIL`

---

## ステップ 5: レビューループ (最大2回)

**LOOP_COUNT = 0 から始めてください。**

全体 `VERDICT: FAIL` の場合:

1. `LOOP_COUNT += 1`
2. `LOOP_COUNT >= 2` に達した場合はループを終了してステップ6へ進む
3. `implementer` を再起動する（`IMPL_INDEX` をインクリメント、**FAIL を返した全 reviewer の `{RUN_DIR}/review-{最新}-{ROLE}.md` パスを全て**レビュー指摘事項として渡す、`{RUN_DIR}/plan.md` のパスも渡す。マージ要約は作らず、implementer に各レポートを直接 Read させる）
4. `reviewer` を **同じ REVIEWER_SET で**並列で再起動して VERDICT を確認する（`REVIEW_INDEX` をインクリメント、最新の `{RUN_DIR}/implementation-{最新}.md` のパスを渡す。PASS を返した観点も再レビューする。観点集合は初回選定を維持し途中で追加・削除しない）
5. 全体 FAIL なら繰り返す

全体 `VERDICT: PASS` になったらステップ6へ進んでください。

---

## ステップ 5.5: メモリへの記録

`PROJECT_MEMORY_DIR` 配下にタスクの振り返り材料を追記します:

- まず `mkdir -p {PROJECT_MEMORY_DIR}` でディレクトリを作成
- パス: `{PROJECT_MEMORY_DIR}/pir_skill_log.md`
- フォーマット: `## [タスク名] — [気づき・課題・パターン]`

---

## ステップ 5.8: handoff.md 完了判定と後処理

`$HANDOFF_PATH` が存在する場合のみ:

1. Read して「残 TODO」の `[ ]` / `[x]` を数える
2. 全 `[x]` なら `Bash(rm "$HANDOFF_PATH")` で削除、最終サマリーに「🎉 handoff 完了削除」と記載
3. 残項目ありなら `最終更新` を更新、最終サマリーに「⏭️ handoff に未完 N 項目残置: `$HANDOFF_PATH`」と記載

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
- REVIEWER_SET: [起動した観点のカンマ区切り、例: correctness,consistency,quality,security,architecture]
- 観点別の VERDICT: [REVIEWER_SET に含まれる観点のみ]
- [主な指摘事項があれば記載]

### 作業ディレクトリ
{RUN_DIR}
```
