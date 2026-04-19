---
name: pir2async
description: PIR²のAgent Teams版。implementerとreviewerをチーム化し直接対話させることで、伝言ゲームの情報ロスを排除する実験的ワークフロー。通常の/pir2との品質比較用。ユーザーが /pir2async と入力したら必ずこのスキルを使う。
argument-hint: [タスクの説明]
---

# PIR² Async — Agent Teams 版 Plan → Implement → Review → Retrospect

PIR²ワークフローのAgent Teams実験版です。implementerとreviewerをチーム化し、直接対話でレビューループを回します。このスキル本体（= メイン Claude）がオーケストレーターとなり、`explorer` / `planner` / `tester` / `retrospector` を `Agent` ツールで起動し、`implementer` と `reviewer` は Agent Teams としてチーム化して起動します。サブエージェント内からの Agent 呼び出しは Claude Code の設計上不可能なため、起動責任はスキル本体に集約されます。
以下の手順を**順番に**実行してください。

**タスク**: $ARGUMENTS

---

## ステップ 1: プロジェクトメモリパスの確認

以下の Bash コマンドで現在のプロジェクトメモリパスとプロジェクトルートを取得し、以降のすべてのステップで使用してください:

```bash
sh ~/.claude/lib/ensure-pir-permissions.sh
sanitized_cwd="$(pwd | sed 's|/|-|g')"
claude_dir="${HOME}/.claude/projects/${sanitized_cwd}/memory"
echo "PROJECT_MEMORY_DIR=$claude_dir"
echo "PROJECT_ROOT=$(pwd)"
run_ts="$(date +%Y%m%d-%H%M%S)"
run_feature="$(echo "$ARGUMENTS" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
[ -z "$run_feature" ] && run_feature="task"
RUN_DIR="${HOME}/.ai-pir-runs/${sanitized_cwd}/${run_ts}-${run_feature}"
mkdir -p "$RUN_DIR"
echo "RUN_DIR=$RUN_DIR"
HANDOFF_PATH="${HOME}/.ai-pir-runs/${sanitized_cwd}/handoff.md"
case "${ARGUMENTS:-}" in
  *引継い*|*続き*|*resume*|*Resume*|*RESUME*|*handoff*|*Handoff*|*HANDOFF*|*"carry on"*)
    RESUME_MODE="resume" ;;
  *)
    if [ -f "$HANDOFF_PATH" ]; then RESUME_MODE="passive-notice"; else RESUME_MODE="new"; fi ;;
esac
echo "HANDOFF_PATH=$HANDOFF_PATH"
echo "RESUME_MODE=$RESUME_MODE"
```

`RESUME_MODE` に応じて挙動を分岐させる（詳細プロトコル: `~/.claude/pir-handoff.md`）:

- `resume`: ブレストフェーズをスキップ。planner への入力に `HANDOFF_PATH=$HANDOFF_PATH` を含めて「未チェック項目のみ」と指示。handoff.md を上書きしない
- `passive-notice`: 「💡 前回の handoff が残っています: `$HANDOFF_PATH`」と表示し通常フローで続行（handoff は触らない）
- `new`: 通常フロー。planner 完了直後にスキル本体が handoff.md 初期版を Write

retrospector 後、スキル本体は全 `[x]` なら handoff.md を削除、残項目ありなら「最終更新」を更新する。

以降の各サブエージェントへのプロンプトには必ず `PROJECT_MEMORY_DIR=[パス]` および `RUN_DIR=[パス]` を含めてください。

---

## ステップ 2: ブレインストーミング（状況に応じて実施）

タスクの仕様を評価し、以下のいずれかに該当する場合は brainstorm スキルを実行してからステップ3へ進んでください：

- 要件が曖昧で複数の解釈が可能
- アーキテクチャ上の選択肢が複数あり、どれを選ぶかユーザーに確認が必要
- ユーザーとの対話を通じて設計を固めたほうが手戻りリスクを減らせると判断される

実行方法: Skill ツールで `skill: "brainstorm"` を呼び出す。実行後、ユーザーとの対話で固まった設計をステップ4の planner へのプロンプトに含めてください。

該当しない場合はスキップしてください。

---

## ステップ 3: 探索 (explorer)

planner はプラン策定専任でありコードベース探索はできない。スキル本体（メイン Claude）が `explorer` サブエージェントを `Agent` ツールで起動してください。

- 最低1体起動。調査領域が独立しているなら最大3体まで並列起動可
- プロンプトに以下を含める:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `EXPLORATION_INDEX=NN`（初回=`01`、並列起動時はスキル本体が `01`/`02`/`03` と割り振る）
  - 「探索レポート本体は `{RUN_DIR}/exploration-{NN}.md` に書き出し、チャットには要約のみ返してください」
  - タスク内容
  - 同一ドメイン・同一レイヤーの既存実装パターン、再利用可能な既存ユーティリティ、フレームワークが自動処理する機能などの調査観点
  - 必要なら公式 README / doc の WebFetch/WebSearch による裏取りを明示
- 追加探索時は `EXPLORATION_INDEX` を既存 `{RUN_DIR}/exploration-*.md` の最大値+1 に設定する

探索レポート要約を受け取ったら次のステップへ進んでください。

---

## ステップ 4: プランニング (Opus)

スキル本体（メイン Claude）が `planner` サブエージェントを `Agent` ツールで起動してください。

- model: `opus`
- プロンプト:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - タスク内容
  - `{RUN_DIR}/exploration-*.md` のパス一覧（planner は本文を自分で Read する）
  - 「プランレポート本体は `{RUN_DIR}/plan.md` に書き出し、チャットには要約＋EXPLORATION_NEEDED の有無のみ返してください。プラン策定のみを実行してください。実装・レビュー・テストは pir2async がチームで制御します。」

プラン要約を受け取ったら、`{RUN_DIR}/plan.md` を Read して `docs/plans/` に `YYYY-MM-DD-<feature>.md` として保存し、ユーザーに提示してください。
フォーマットは通常の PIR² と同じ（目標・実装計画・設計詳細・実装ログ）。

---

## ステップ 4.5: 能動的再探索ループ（最大5回）

planner の返り値要約に `### EXPLORATION_NEEDED` セクションがあり、かつ箇条書き項目（`- topic`）が1件以上含まれる（`- なし` 単独でない）場合、追加探索 → planner 再起動を繰り返す。

`REPLAN_COUNT = 0` から開始。

### 収束判定ロジック

planner の返り値要約テキストの `### EXPLORATION_NEEDED` セクションを見る:
- 見出しが存在しない、または直下が「なし」「- なし」のみ → **収束**。ステップ 5 へ進む
- `- topic` 形式の項目が1件以上列挙されている → 追加探索へ

### ループ本体

1. `REPLAN_COUNT += 1`
2. `REPLAN_COUNT > 5` に到達した場合、ループを強制終了してステップ 5 へ進む。最終サマリー（ステップ8）に「**planner が依然追加探索を要求中（ハードキャップ5回到達）**: [topic 一覧]」と明記する
3. planner が出した各 topic ごとに explorer を起動する（topic が独立なら最大3体並列）:
   - `EXPLORATION_INDEX` は `{RUN_DIR}/exploration-*.md` 既存ファイルの最大連番 + 1 から割り振る
   - プロンプトには topic 本文と共に「この topic の調査に集中する。既存探索レポート（`{RUN_DIR}/exploration-*.md` 参照可）の重複調査は不要」と指示
4. 追加探索が完了したら planner を再起動する:
   - プロンプトは初回と同じだが、`{RUN_DIR}/exploration-*.md` のパス一覧に新しく追加されたものも含める
   - `plan.md` は上書き更新される（planner は同じパスに Write する）
5. planner の新しい返り値要約の EXPLORATION_NEEDED をチェック → 収束していればステップ 5 へ、まだ要求が残っていれば 1. に戻る

> **注**: 「既存パターン逸脱の事前申告」のユーザー承認判定はループ収束後、ステップ 5 の直前に1回だけ行う（ループ中の中間プランに対しては承認を求めない）。

---

## ステップ 4.8: handoff.md 初期版生成（`RESUME_MODE=new` の場合のみ）

`RESUME_MODE=resume` / `passive-notice` ならスキップ。`RESUME_MODE=passive-notice` だった場合はこの時点でユーザーに「💡 前回の handoff が残っています: `$HANDOFF_PATH`（`引継いで` で resume 可能）」と表示してから次ステップへ。

`RESUME_MODE=new` の場合のみ実行:

1. `{RUN_DIR}/plan.md` を Read し、実装ステップ項目を抽出
2. `$HANDOFF_PATH` に `~/.claude/pir-handoff.md` の「フォーマット」節に従って Write:
   - `最終更新`: 現在時刻 + `run: $(basename $RUN_DIR)`
   - `タスク`: ユーザー指示の一行要約
   - `残 TODO`: 各実装ステップを `- [ ] <ステップ名>` 形式に変換
   - `関連 artifact`: `最新 plan: {RUN_DIR}/plan.md`

---

**INNER_LOOP_COUNT = 0、OUTER_LOOP_COUNT = 0 から始めてください。**

## ステップ 5: 実装+レビュー チーム起動

ここが通常の PIR² との違いです。implementer と reviewer を **Agent Teams** として起動し、直接対話させます。

### 5-1: チーム作成

TeamCreate ツールでチームを作成してください:

```
team_name: "impl-review"
description: "実装とレビューのチーム。implementerが実装し、reviewerが直接レビューしてフィードバックする。"
```

### 5-2: チームメイト起動

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
RUN_DIR=[パス]
IMPL_INDEX=01
（`RESUME_MODE` が `new` または `resume` の場合のみ）HANDOFF_PATH=[$HANDOFF_PATH]

## タスク
以下のパスのプランを Read して実装してください:
{RUN_DIR}/plan.md

`HANDOFF_PATH` が渡された場合は実装完了した項目を `[x]` 化し、新規発見の TODO は `残 TODO` に追記してください（詳細: `~/.claude/pir-handoff.md`）。

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
   - `{RUN_DIR}/implementation-01.md` の書き出し完了
   - `{RUN_DIR}/review-{最終}.md` の書き出し完了
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
RUN_DIR=[パス]

## チームでの作業手順

1. チームメイトの "implementer" からレビュー依頼メッセージを待つ
2. メッセージを受け取ったら、変更ファイルを Read して通常のレビュー観点でレビューする
3. レビュー結果を `{RUN_DIR}/review-{NN}.md` に Write で書き出す（NN は初回=01、再レビュー時はインクリメント。ディレクトリ内既存の review-*.md の最大連番+1 を使う）
4. レビュー結果を implementer に SendMessage で直接送る:
   - VERDICT: PASS または VERDICT: FAIL
   - FAIL の場合: 問題一覧と具体的な修正指示、および書き出し先パス (`{RUN_DIR}/review-{NN}.md`) を通知
   - PASS の場合: 良好点があれば記載、書き出し先パスを通知
5. FAIL の場合、implementer からの修正完了メッセージを待って再レビューする（REVIEW_INDEX をインクリメントして 3. から繰り返す）
6. レビューループは最大3回まで。3回 FAIL したら最後の VERDICT を記録してチームリードに報告する

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
- 各レビュー回の成果物は必ず `{RUN_DIR}/review-{NN}.md` に書き出すこと（`{RUN_DIR}/review-*.md` 参照可）
```

### 5-3: チーム完了待ち

implementer から「実装+レビュー完了」の報告を待ちます。報告を受け取ったら:

1. INNER_LOOP_COUNT を報告されたレビューループ回数で更新する
2. ドキュメントの実装ログに追記する
3. 両チームメイトに shutdown_request を送る
4. ステップ 6 へ進む

---

## ステップ 6: テスト (Sonnet)

通常の PIR² と同じ。スキル本体（メイン Claude）が `tester` サブエージェントを `Agent` ツールで起動してください（チーム外、通常の Agent）。

- model: `sonnet`
- プロンプト:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `TEST_INDEX=01`（初回。再テスト時はインクリメント）
  - `{RUN_DIR}/plan.md` のパス
  - `{RUN_DIR}/implementation-{最新}.md` のパス
  - 「テストレポート本体は `{RUN_DIR}/test-{TEST_INDEX}.md` に書き出し、チャットには VERDICT + 要約のみ返してください。テストデータのクリーンアップはユーザー明示指示まで実行しないこと」

`VERDICT: PASS` の場合:

ドキュメントのヘッダーを更新してステップ7へ進んでください：

```markdown
_作成: YYYY-MM-DD | ステータス: **完了** YYYY-MM-DD_
```

末尾に以下を追加：

```markdown
> **このドキュメントは内容を確認後に削除してください。**
> `rm docs/plans/YYYY-MM-DD-<feature>.md`
```

`VERDICT: FAIL` の場合:

1. `OUTER_LOOP_COUNT += 1`
2. `OUTER_LOOP_COUNT >= 3` ならループを終了し、ステップ7へ進む（失敗として記録）
3. `INNER_LOOP_COUNT = 0` にリセット
4. **ステップ 5 に戻る**（impl-review チームを再作成して実装+レビューループを再実行。`IMPL_INDEX` をインクリメント、`{RUN_DIR}/test-{最新}.md` のパスを tester 指摘事項として渡す）
5. tester を再起動（`TEST_INDEX` をインクリメント）
6. PASS になるまで繰り返す

---

## ステップ 6.5: メモリへの記録

`PROJECT_MEMORY_DIR` 配下にタスクの振り返り材料を追記します:

- まず `mkdir -p {PROJECT_MEMORY_DIR}` でディレクトリを作成
- パス: `{PROJECT_MEMORY_DIR}/pir_skill_log.md`
- フォーマット: `## [タスク名] — [気づき・課題・パターン]`

---

## ステップ 7: 振り返り (常に実行)

通常の PIR² と同じ。スキル本体（メイン Claude）が `retrospector` サブエージェントを `Agent` ツールで起動してください:

- model: `INNER_LOOP_COUNT が 0 かつ OUTER_LOOP_COUNT が 0 の場合は sonnet`、いずれかが 1 以上の場合は `opus`
- プロンプト: 以下の情報をすべて渡す
  - `PROJECT_MEMORY_DIR`
  - `PROJECT_ROOT`
  - `RUN_DIR`
  - `META_MODE=false`（/pir2async は常に通常モードで起動する。メタモードは `/retro --meta` で明示起動する）
  - `INNER_LOOP_COUNT`
  - `OUTER_LOOP_COUNT`
  - `REPLAN_COUNT`
  - `{RUN_DIR}/review-*.md` のパス一覧（retrospector が必要に応じて Read する）
  - `{RUN_DIR}/test-*.md` のパス一覧
  - 最終的な VERDICT
  - ワークフロー種別: pir2async（通常の pir2 との比較用に記録）

retrospector のレポートに「メタ改善推奨」項目が含まれていた場合、その旨をステップ8の最終サマリーに必ず転記してユーザーに通知してください（自動でメタモードは起動せず、ユーザーが `/retro --meta` を実行するかどうかを判断できるようにする）。

---

## ステップ 7.5: handoff.md 完了判定と後処理

`$HANDOFF_PATH` が存在する場合のみ実行:

1. Read して「残 TODO」の `[ ]` と `[x]` を数える
2. 全項目が `[x]` なら `Bash(rm "$HANDOFF_PATH")` で削除し、最終サマリーに「🎉 handoff.md 全項目完了 → 削除済み」と記載
3. 残項目ありなら `最終更新` 行を `YYYY-MM-DD HH:MM (run: $(basename $RUN_DIR))` に Edit し、最終サマリーに「⏭️ handoff.md に未完 N 項目残置: `$HANDOFF_PATH`」と記載

---

## ステップ 8: 最終サマリーの提示

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

### 再探索ループ回数
- REPLAN_COUNT: [回数]
- [ハードキャップ到達時のみ]: planner が依然追加探索を要求中: [topic 一覧]

### 作業ディレクトリ
{RUN_DIR}

### 振り返り
[retrospectorの改善内容の要約]

### 通常版 PIR² との比較ポイント
- レビューループ回数の違い
- 指摘の質・粒度の違い
- チーム内対話で解決された問題（あれば）
```
