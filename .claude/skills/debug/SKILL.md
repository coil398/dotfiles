---
name: debug
description: エラーや不具合を診断して修正する。症状・エラーメッセージを受け取り根本原因を特定してから修正する。「動かない」「壊れた」「エラーが出る」「なぜか失敗する」やスタックトレース・エラーログが貼られたときにも使う。ユーザーが /debug と入力したら必ずこのスキルを使う。
argument-hint: [症状やエラーメッセージ]
---

# Debug — 診断 → 実装 → レビュー

エラーや不具合を診断し修正します。このスキル本体（= メイン Claude）がオーケストレーターとなり、`explorer` / `planner` / `implementer` / `reviewer` を `Agent` ツールで順に起動します。サブエージェント内からの Agent 呼び出しは Claude Code の設計上不可能なため、起動責任はスキル本体に集約されます。

**症状**: $ARGUMENTS

---

## ステップ 0: プロジェクトメモリパスと RUN_DIR の確定

以下の Bash コマンドで `PROJECT_ROOT` / `PROJECT_MEMORY_DIR` / `RUN_DIR` / `HANDOFF_PATH` を確定し、以降のすべてのステップで使用してください:

```bash
PROJECT_ROOT="$(pwd)"
sanitized_cwd="$(pwd | sed 's|[^a-zA-Z0-9]|-|g')"  # Claude Code harness と一致させる
PROJECT_MEMORY_DIR="${HOME}/.claude/projects/${sanitized_cwd}/memory"
run_ts="$(date +%Y%m%d-%H%M%S)"
run_feature="$(printf '%s' "$ARGUMENTS" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
[ -z "$run_feature" ] && run_feature="task"
RUN_DIR="${HOME}/.ai-pir-runs/${sanitized_cwd}/${run_ts}-${run_feature}"
mkdir -p "$RUN_DIR"
HANDOFF_PATH="${HOME}/.ai-pir-runs/${sanitized_cwd}/handoff.md"
echo "PROJECT_ROOT=$PROJECT_ROOT"
echo "PROJECT_MEMORY_DIR=$PROJECT_MEMORY_DIR"
echo "RUN_DIR=$RUN_DIR"
echo "HANDOFF_PATH=$HANDOFF_PATH"
```

次に `RESUME_MODE` をスキル本体（メイン Claude）が判定する:

- `$ARGUMENTS` に `引継い` / `続き` / `resume` / `Resume` / `RESUME` / `handoff` / `Handoff` / `HANDOFF` / `carry on` のいずれかが含まれる → `RESUME_MODE=resume`
- 含まれず、かつ `$HANDOFF_PATH` のファイルが存在する → `RESUME_MODE=passive-notice`
- それ以外 → `RESUME_MODE=new`

`RESUME_MODE` に応じて挙動を分岐（詳細プロトコル: `~/.claude/pir-handoff.md`）:

- `resume`: planner に `HANDOFF_PATH` を渡し「未チェック項目のみ」と指示。handoff.md を上書きしない
- `passive-notice`: 「💡 前回の handoff が残っています: `$HANDOFF_PATH`」と表示し通常フロー
- `new`: 通常フロー。planner 完了直後にスキル本体が handoff.md 初期版を Write

retrospector 後、スキル本体は全 `[x]` なら handoff.md を削除、残項目ありなら「最終更新」を更新する。

---

## ステップ 1: 探索 (explorer)

planner はプラン策定専任でありコードベース探索はできない。スキル本体（メイン Claude）が `explorer` サブエージェントを `Agent` ツールで起動し、症状の周辺コードを調査させてください。

- model は explorer 側の定義に従う
- プロンプトに以下を含める:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `EXPLORATION_INDEX=01`
  - 「探索レポート本体は `{RUN_DIR}/exploration-01.md` に書き出し、チャットには要約のみ返してください」
  - 「探索フェーズではタスクのコード実装を行わず、`git add` / `git commit` などリポジトリ状態を変更する git 操作も一切行わないでください。実装が必要だと判明したら探索レポートの『呼び出し元への依頼』に回してください」（explorer は `Write` / `Bash` を持つため、明示しないと探索の延長で実装・コミットまで踏み込むロール逸脱が起こりうる）
  - 症状・エラーメッセージ（$ARGUMENTS）
  - 「症状に関連するコード・エントリポイント・エラーメッセージの発生源を特定し、呼び出し経路と関連する既存実装パターンを含む探索レポートを返す」
  - 必要に応じて WebFetch/WebSearch で外部ドキュメント（ライブラリ挙動・類似 Issue 等）も裏取りする

### 既存 agent を探索フェーズに流用する場合のロール境界再注入

PIR² 起動前の会話で稼働していた agent を `SendMessage` で探索フェーズに流用する場合、`Agent` ツールでの新規起動と違い `explorer.md` のシステムプロンプト（実装・git 操作の禁止条項）が再注入されない。流用するときは `SendMessage` 本文の冒頭に必ず次を明記すること:

> 「これより explorer ロールに切り替わります。責務は調査と `{RUN_DIR}/exploration-{INDEX}.md` への探索レポート作成のみ。コードの実装、`git add` / `git commit` / `git reset` / `git checkout` / `git restore` / `git stash` 等のリポジトリ状態を変更する操作は一切禁止。実装が必要だと判明したら探索レポートの『呼び出し元への依頼』セクションに回すこと。」

会話で実装文脈を濃く持っている agent は流用するとロール境界が曖昧になり実装に踏み込みやすい。その場合は流用せず `Agent` ツールで新規 explorer を起動する方を優先する。

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
  - 「プランの冒頭に『## 診断: [根本原因]』セクションを追加してください。診断には根本原因を裏付ける具体的なコード証拠（`file:line` と該当コードの引用）を必ず含め、なぜそのコードが症状を引き起こすかを説明してください。explorer レポートの記述をそのまま結論とせず、該当コードを Read で確認した上で診断を確定してください。」
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

## ステップ 2.85: 次ステップキュー初期版生成

`{RUN_DIR}/next-steps.md` に以降のサブエージェント起動予定を checkbox リストで書き出す。**ユーザー会話による中断後、メイン Claude（スキル本体）は次の判断を行う前に必ずこのファイルを Read してから動く**。

このキューは「ユーザーとの対話で 1 ターン以上中断したあと、次に何をすべきかをスキル本体が失念する」パターン（pir_pattern_registry `[2026-05-13T16:30:00Z]` フラグの根拠の 1 つ）を構造的にブロックするための明示状態管理。

詳細プロトコル（共通手順）: `~/.claude/skills/pir2/references/next-steps-queue.md` を参照（checkbox 更新 4 手順 / 中断後の必須 Read ルール / スキップ条件 / RESUME_MODE=resume 時の handoff 統合）。debug でのステップ番号読み替え: 5.6-2 → 2.85-2、5.6-3 → 2.85-3。

要点: スキル本体はユーザー会話中断後、次の判断前に必ず `{RUN_DIR}/next-steps.md` を Read してから動く。各ステップ完了直後に checkbox を `[x]` + `<!-- done: ISO8601 -->` に更新する（必須運用）。

### 2.85-1: 初期内容を Write する

`{RUN_DIR}/next-steps.md` に以下の内容で Write する:

```markdown
# 次ステップキュー (run: <RUN_DIR basename>)

最終更新: <ISO8601 現在時刻>

## 残ステップ

- [ ] ステップ 2.9: 破壊的変更チェックリスト
- [ ] ステップ 2.95: 直前追加 feedback の自己照合ゲート
- [ ] ステップ 3: implementer 起動 (IMPL_INDEX=01)
- [ ] ステップ 4: reviewer ハイブリッド並列起動 (REVIEW_INDEX=01)
- [ ] ステップ 5: レビューループ判定
- [ ] ステップ 5.5: メモリへの記録
- [ ] ステップ 5.8: handoff.md 完了判定と後処理
- [ ] ステップ 6: 最終サマリーの提示

## 完了済み

（完了するたびに上の checkbox を `- [x]` に変更し `<!-- done: <ISO8601> -->` を付与する。Read 時に最上位の `- [ ]` を「次に実行すべきステップ」とみなす）
```

ループによる `IMPL_INDEX` / `REVIEW_INDEX` の更新は、最初の 1 件だけ初期版に書き、再ループ詳細は「中断・再開ログ」セクションに追記する。

---

## ステップ 2.9: 破壊的変更チェックリスト（implementer 起動前に必ず実行）

implementer を起動する前に、メイン Claude（スキル本体）が plan.md と explorer レポートを Read して以下 5 項目を機械チェックする。**1 つでも該当するなら「破壊的変更フラグ ON」をスキル本体内で保持し、後段の reviewer / tester を全工程必須化（軽量化禁止）する。**

debug スキルは「バグ修正」目的のため一見軽量化したくなりやすいが、修正対象が破壊的変更（OpenAPI / 自動生成 / golden 波及）を含むケースは pir2 と同等の必須工程を踏ませる必要がある。

### チェック項目（plan.md と explorer レポートを Read して機械的に判定）

- **(a) OpenAPI フィールド名のリネーム or 削除**: plan.md または explorer レポートに `docs/openapi/` 配下のフィールド `rename` / `削除` / `name change` の言及があるか
- **(b) 自動生成ファイル再生成連鎖**: `codegen` / `proto` / `openapi` / `sqlc` / `make .*gen` / `go generate` のいずれかが plan に含まれるか
- **(c) golden / snapshot テスト波及見込み**: `golden` / `snapshot` / `*_golden.json` / `__snapshots__` が plan / explorer レポートに登場するか、または (a)(b) のいずれかが ON の場合は自動的に ON
- **(d) 自動生成型変更**: `required` の追加・削除、`int32` ↔ `*int32` 等の proto3 optional 化、enum 値の追加・削除が plan に含まれるか
- **(e) controller 構造体リテラル / フィールド参照変更が 5 箇所以上**: explorer レポートに「N 箇所変更」「N+ files」のような数値があり 5 以上か、または plan に列挙された対象ファイル数が controller/ 配下で 5 以上か

### 判定結果の書き出しと反映

判定結果を `{RUN_DIR}/destructive-change-check.md` に書き出す。フォーマット:

```markdown
# 破壊的変更チェックリスト

- (a) OpenAPI フィールド名 rename/削除: [ON/OFF] — 根拠: <plan.md の該当箇所引用 or "該当なし">
- (b) 自動生成連鎖: [ON/OFF] — 根拠: <同上>
- (c) golden/snapshot 波及: [ON/OFF] — 根拠: <同上>
- (d) 自動生成型変更: [ON/OFF] — 根拠: <同上>
- (e) controller 5+ 箇所変更: [ON/OFF] — 根拠: <同上>

破壊的変更フラグ: [ON/OFF]
適用される必須工程:
- ON の場合: reviewer 5 観点全起動 / tester 起動（軽量化禁止）
- OFF の場合: 通常運用（ステップ 4 で REVIEWER_SET 自動選定、tester は通常判断）
```

### 軽量化したい場合の運用

破壊的変更フラグが ON のときに「reviewer 観点を減らしたい」「tester を省略したい」と判断したくなった場合、**スキル本体の独断は禁止**。必ずユーザーに以下の形式で確認する:

```
破壊的変更チェックリスト判定: ON
該当項目: (a) OpenAPI rename + (c) golden 波及

通常はこの状況で reviewer 5 観点 + tester 全工程必須ですが、
[省略したい工程] を省略してよろしいですか？
- yes: 省略を承認（理由をご教示ください）
- no: 全工程実行（推奨）
```

Auto mode でもこのユーザー確認は省略不可。

### スキップ条件

破壊的変更フラグが OFF のときはステップ 3 以降を通常運用で進める。

### 完了後

ステップ 2.85-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。

---

## ステップ 2.95: 直前追加 feedback の自己照合ゲート（implementer 起動前に必ず実行）

詳細プロトコル: `~/.claude/skills/pir2/references/feedback-conflict-gate.md` を参照（feedback Read → implementer プロンプト案との照合 → 矛盾検出時の中断フォーマット → 記録 → スキップ条件 → 完了後の checkbox 更新先）。

要点: 過去 14 日以内の `feedback_*.md` 5 件を Read し、implementer プロンプト案の除外指示・変更しないファイル/フィールド・スコープ縮小と突合。矛盾を 1 件でも検出したら implementer 起動を中断 → ユーザー確認。矛盾なしの場合も `{RUN_DIR}/feedback-conflict.md` に「照合 N 件、矛盾なし」を記録（retrospector N4.4 向け痕跡）。**debug スキルは『バグ修正』目的のため一見スコープを絞りたくなりやすいが、修正対象が直前 feedback の除外指示と矛盾するケースは pir2 と同等の照合を必須とする。**完了後は 2.85-2 に従い `{RUN_DIR}/next-steps.md` の checkbox を更新する。

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

### 完了後

ステップ 2.85-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する（複数回ループで `IMPL_INDEX` が増えた場合は最初の 1 回のみマーク、ループ詳細は「中断・再開ログ」に追記）。

---

## ステップ 4: レビュー (Sonnet ハイブリッド並列)

### 4-1: REVIEWER_SET 決定（planner 系：全 5 観点がデフォルト）

`REVIEWER_SET` を決定する:

1. **ユーザーフラグのパース**: `$ARGUMENTS` に `--reviewers=<roles>` が含まれていればカンマ区切りを観点集合として採用（未知 role は無視）。`--all-reviewers` が含まれていれば全 5 観点を採用。両方指定時は `--reviewers=` を優先。フラグ抽出後の残りをタスク説明として扱う
2. **フラグ未指定時のデフォルト**: 全 5 観点 `[correctness, consistency, quality, security, architecture]`（planner が動くタスクは設計判断を含むため）
3. 決定した `REVIEWER_SET` を最終サマリーに記録

### 4-2A: 起動宣言（Fan-Out Gate — 並列発火の直前に必ず書く）

reviewer 並列起動メッセージを送信する **直前のターン本文中** に、以下のテンプレートを必ず生成すること。このテンプレートが本文に出現していないターンで Agent 起動を発火させた場合は、ステップ完了判定を取り消して 4-2A からやり直す。

> **Fan-Out Gate（reviewer）**
> - REVIEWER_SET = [<観点をカンマ区切りで全列挙>]
> - 起動体数 = <N>（= len(REVIEWER_SET)、必ず一致）
> - 同一 function_calls ブロックに <N> 個の Agent 起動を並べる
> - 1 体ずつ起動・後追い起動・観点削減はいずれも違反

このブロックは「起動直前の自己コミットメント」であり、自分の手癖（1 体ずつ逐次起動する癖）を止めるためのフェンスとして機能する。再レビュー時（ステップ 5 の差し戻し時）にも毎回この宣言を書くこと。

### 4-2B: 並列発火（同一メッセージ内）

直前ターンで宣言した REVIEWER_SET の各観点について、同一の `<function_calls>` ブロック内に Agent ツール呼び出しを **N 個** 並べて 1 メッセージで同時送信する。各体は `REVIEWER_ROLE` を変えて担当観点を分割する。

詳細仕様（観点マッピング / 違反パターンと検出 / 違反検出時のリカバリ / reviewer 起動パラメータ）: `~/.claude/skills/pir2/references/fan-out-gate.md` を参照。

違反パターン（次のいずれかが発生したら違反として検出し 4-2A からやり直す）:
- function_calls ブロックが 2 ターン以上に分かれる
- 並んだ Agent 起動の数が宣言した N より少ない
- 観点を独自判断で減らした
- 直前ターンの宣言テンプレートが省略された

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

### 完了後

ステップ 2.85-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する（複数回ループで `REVIEW_INDEX` が増えた場合は最初の 1 回のみマーク、ループ詳細は「中断・再開ログ」に追記）。

---

## ステップ 5: レビューループ (最大2回)

**LOOP_COUNT = 0 から始めてください。**

全体 `VERDICT: FAIL` の場合:

1. `LOOP_COUNT += 1`
2. `LOOP_COUNT >= 2` の場合は **続行可能ゲート（5-G）** へ。判定が「続行」なら 3. へ、「移行」ならステップ 6 へ（失敗として記録）
3. `implementer` を再起動する（`IMPL_INDEX` をインクリメント、**FAIL を返した全 reviewer の `{RUN_DIR}/review-{最新}-{ROLE}.md` パスを全て**レビュー指摘事項として渡す、`{RUN_DIR}/plan.md` のパスも渡す。マージ要約は作らず、implementer に各レポートを直接 Read させる）
4. **4-2A（Fan-Out Gate 宣言）→ 4-2B（並列発火）の手順で** `reviewer` を **同じ REVIEWER_SET で**並列で再起動して VERDICT を確認する（`REVIEW_INDEX` をインクリメント、最新の `{RUN_DIR}/implementation-{最新}.md` のパスを渡す。PASS を返した観点も再レビューする。観点集合は初回選定を維持し途中で追加・削除しない。**再レビュー時も Fan-Out Gate を省略しないこと**）
5. 全体 FAIL なら繰り返す

全体 `VERDICT: PASS` になったらステップ6へ進んでください。

### 5-G: 続行可能ゲート（LOOP_COUNT 上限到達時のみ）

LOOP_COUNT が 2 に達した時点で、`{RUN_DIR}/review-{最新}-*.md` と `{RUN_DIR}/implementation-{最新}.md` を Read して以下の 4 条件を判定する:

- (i) 残 FAIL の根本原因が reviewer レポートに明示されているか（仮説でなく root cause 確定文言）
- (ii) implementer に渡せる修正方針が単一に絞り込まれているか
- (iii) 修正の影響範囲が限定的か（変更は 3 ファイル以下、または設計層をまたがない）
- (iv) 過去ループで根本原因の二転三転が収束したか

4 条件すべて満たす場合のみユーザーに続行可否を尋ねる（フォーマットは pir2 ステップ 8-2-G と同様、上限値のラベルを LOOP_COUNT に読み替える）。1 条件でも満たさない場合はゲートを出さず無条件でステップ 6 へ移行する。ゲートを 1 サイクル中に通過できるのは最大 1 回のみ。Auto mode でも必ずユーザー応答を待つ。

### 完了後

ステップ 2.85-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。

---

## ステップ 5.5: メモリへの記録

`PROJECT_MEMORY_DIR` 配下にタスクの振り返り材料を追記します:

- まず `mkdir -p {PROJECT_MEMORY_DIR}` でディレクトリを作成
- パス: `{PROJECT_MEMORY_DIR}/pir_skill_log.md`
- フォーマット: `## [タスク名] — [気づき・課題・パターン]`

### 完了後

ステップ 2.85-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。

---

## ステップ 5.8: handoff.md 完了判定と後処理

`$HANDOFF_PATH` が存在する場合のみ:

1. Read して「残 TODO」の `[ ]` / `[x]` を数える
2. 全 `[x]` なら `Bash(rm "$HANDOFF_PATH")` で削除、最終サマリーに「🎉 handoff 完了削除」と記載
3. 残項目ありなら `最終更新` を更新、最終サマリーに「⏭️ handoff に未完 N 項目残置: `$HANDOFF_PATH`」と記載

### 完了後

ステップ 2.85-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。全 checkbox が `[x]` になった場合は最終サマリー（ステップ 6）に「next-steps.md: 全項目完了」と記載する。

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
