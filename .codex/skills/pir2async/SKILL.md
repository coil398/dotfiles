---
name: "pir2async"
description: "PIR²のAgent Teams版。implementerとreviewerをチーム化し直接対話させることで、伝言ゲームの情報ロスを排除する実験的ワークフロー。通常の/pir2との品質比較用。ユーザーが /pir2async と入力したら必ずこのスキルを使う。"
argument-hint: "[タスクの説明]"
---

# PIR² Async — Agent Teams 版 Plan → Implement → Review → Retrospect

PIR²ワークフローのAgent Teams実験版です。implementerとreviewerをチーム化し、直接対話でレビューループを回します。このスキル本体（= メイン Claude）がオーケストレーターとなり、`explorer` / `planner` / `tester` / `retrospector` を `Agent` ツールで起動し、`implementer` と `reviewer` は Agent Teams としてチーム化して起動します。サブエージェント内からの Agent 呼び出しは Claude Code の設計上不可能なため、起動責任はスキル本体に集約されます。
以下の手順を**順番に**実行してください。

**タスク**: $ARGUMENTS

---

## ステップ 1: プロジェクトメモリパスの確認

以下の Bash コマンドで現在のプロジェクトメモリパスとプロジェクトルートを取得し、以降のすべてのステップで使用してください:

```bash
sh ~/.claude/lib/pir-preflight.sh "$ARGUMENTS"
```

出力フォーマット（5 行の `KEY=VALUE`）:
- `PROJECT_MEMORY_DIR=...`
- `PROJECT_ROOT=...`
- `RUN_DIR=...`
- `HANDOFF_PATH=...`
- `RESUME_MODE=new|resume|passive-notice`

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

> **brainstorm 完了後は必ず自動でステップ3へ進むこと**。「設計ドキュメントを保存しました」と単独ターンで区切ってユーザー承認を待つのは禁止。承認を挟んでよいのはこのスキル本体で明示的にユーザー確認が指定されているポイントのみ。

---

## ステップ 3: 探索 (explorer)

planner はプラン策定専任でありコードベース探索はできない。スキル本体（メイン Claude）が `explorer` サブエージェントを `Agent` ツールで起動してください。

- 最低1体起動。調査領域が独立しているなら最大3体まで並列起動可
- プロンプトに以下を含める:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `EXPLORATION_INDEX=NN`（初回=`01`、並列起動時はスキル本体が `01`/`02`/`03` と割り振る）
  - 「探索レポート本体は `{RUN_DIR}/exploration-{NN}.md` に書き出し、チャットには要約のみ返してください」
  - 「探索フェーズではタスクのコード実装を行わず、`git add` / `git commit` などリポジトリ状態を変更する git 操作も一切行わないでください。実装が必要だと判明したら探索レポートの『呼び出し元への依頼』に回してください」（explorer は `Write` / `Bash` を持つため、明示しないと探索の延長で実装・コミットまで踏み込むロール逸脱が起こりうる）
  - タスク内容
  - 同一ドメイン・同一レイヤーの既存実装パターン、再利用可能な既存ユーティリティ、フレームワークが自動処理する機能などの調査観点
  - 必要なら公式 README / doc の WebFetch/WebSearch による裏取りを明示
- 追加探索時は `EXPLORATION_INDEX` を既存 `{RUN_DIR}/exploration-*.md` の最大値+1 に設定する

### 既存 agent を探索フェーズに流用する場合のロール境界再注入

PIR² 起動前の会話で稼働していた agent を `SendMessage` で探索フェーズに流用する場合、`Agent` ツールでの新規起動と違い `explorer.md` のシステムプロンプト（実装・git 操作の禁止条項）が再注入されない。流用するときは `SendMessage` 本文の冒頭に必ず次を明記すること:

> 「これより explorer ロールに切り替わります。責務は調査と `{RUN_DIR}/exploration-{INDEX}.md` への探索レポート作成のみ。コードの実装、`git add` / `git commit` / `git reset` / `git checkout` / `git restore` / `git stash` 等のリポジトリ状態を変更する操作は一切禁止。実装が必要だと判明したら探索レポートの『呼び出し元への依頼』セクションに回すこと。」

会話で実装文脈を濃く持っている agent は流用するとロール境界が曖昧になり実装に踏み込みやすい。その場合は流用せず `Agent` ツールで新規 explorer を起動する方を優先する。

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

詳細プロトコル: `~/.claude/skills/pir2/references/exploration-loop.md` を参照（収束判定ロジック / ループ本体 / 既存パターン逸脱の事前申告タイミング）。

要点: planner の返り値要約に `### EXPLORATION_NEEDED` の `- topic` が残る間、追加探索 → planner 再起動を最大 5 回繰り返す。収束したらステップ 5 へ進む。`REPLAN_COUNT = 0` から開始し、ハードキャップ到達時は最終サマリー（ステップ8）に「**planner が依然追加探索を要求中（ハードキャップ5回到達）**: [topic 一覧]」と明記する。

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

## ステップ 4.85: 次ステップキュー初期版生成

`{RUN_DIR}/next-steps.md` に以降のサブエージェント起動予定を checkbox リストで書き出す。**ユーザー会話による中断後、メイン Claude（スキル本体）は次の判断を行う前に必ずこのファイルを Read してから動く**。

このキューは「ユーザーとの対話で 1 ターン以上中断したあと、次に何をすべきかをスキル本体が失念する」パターン（pir_pattern_registry `[2026-05-13T16:30:00Z]` フラグの根拠の 1 つ）を構造的にブロックするための明示状態管理。

### 4.85-1: 初期内容を Write する

`{RUN_DIR}/next-steps.md` に以下の内容で Write する:

```markdown
# 次ステップキュー (run: <RUN_DIR basename>)

最終更新: <ISO8601 現在時刻>

## 残ステップ

- [ ] ステップ 4.9: 破壊的変更チェックリスト
- [ ] ステップ 4.95: 直前追加 feedback の自己照合ゲート
- [ ] ステップ 5: 実装+レビュー チーム起動 (IMPL_INDEX=01 / REVIEW_INDEX=01)
- [ ] ステップ 6: tester 起動 (TEST_INDEX=01)
- [ ] ステップ 6.5: メモリへの記録
- [ ] ステップ 7: retrospector 起動
- [ ] ステップ 7.5: handoff.md 完了判定と後処理
- [ ] ステップ 8: 最終サマリーの提示

## 完了済み

（完了するたびに上の checkbox を `- [x]` に変更し `<!-- done: <ISO8601> -->` を付与する。Read 時に最上位の `- [ ]` を「次に実行すべきステップ」とみなす）
```

ループによる `IMPL_INDEX` / `REVIEW_INDEX` / `TEST_INDEX` の更新は、最初の 1 件だけ初期版に書き、再ループ詳細は「中断・再開ログ」セクションに追記する。

### 4.85-2: 各サブエージェント完了時の checkbox 更新（必須運用）

ステップ 4.9 以降の各ステップ完了直後に **必ず** 以下を実行する:

1. `{RUN_DIR}/next-steps.md` を Read
2. 完了した checkbox を `- [x]` に変更し `<!-- done: <ISO8601> -->` を付与
3. `最終更新` の ISO8601 を現在時刻に更新
4. Write で上書き保存

### 4.85-3: ユーザー会話による中断後の必須運用

メイン Claude（スキル本体）はユーザーとの対話で **1 ターン以上中断したあと**、次の判断（サブエージェント起動など）を行う前に必ず `{RUN_DIR}/next-steps.md` を Read する。未チェックの最上位 checkbox が「次に実行すべきステップ」を示す。

判断記録は `{RUN_DIR}/next-steps.md` の末尾セクション（`## 中断・再開ログ`、初期版にはなくてよい。発生時に追記）に以下の形式で残す:

```
- <ISO8601>: ユーザー会話で中断（理由: <要約>）→ 再開時に Read。次ステップ: <最上位 [ ] のステップ>
```

### スキップ条件

なし（PIR² Async 開始時に必ず生成する）。`RESUME_MODE=resume` の場合は handoff.md 由来の未完了項目を反映した残ステップを書き出す。

---

## ステップ 4.9: 破壊的変更チェックリスト（チーム起動前に必ず実行）

implementer + reviewer チームを起動する前に、メイン Claude（スキル本体）が plan.md と explorer レポートを Read して以下 5 項目を機械チェックする。**1 つでも該当するなら「破壊的変更フラグ ON」をスキル本体内で保持し、後段の REVIEWER_SET / refactor-advisor / tester を全工程必須化（軽量化禁止）する。**

このチェックは「reviewer / tester を省略してよさそう」と判断したくなる軽量化バイアスを構造的にブロックするための機械ゲート。出現の根拠は pir_pattern_registry の `[2026-05-13T16:30:00Z]` フラグ（H2/H3/H4 が同一 run で発生）。

### チェック項目（plan.md と explorer レポートを Read して機械的に判定）

- **(a) OpenAPI フィールド名のリネーム or 削除**: plan.md または explorer レポートに `docs/openapi/` 配下のフィールド `rename` / `削除` / `name change` の言及があるか
- **(b) 自動生成ファイル再生成連鎖**: `apigen` / `prtgen` / `proto` / `openapi` / `sqlc` / `make .*gen` / `go generate` のいずれかが plan に含まれるか
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
- ON の場合: REVIEWER_SET 全 5 観点固定 / refactor-advisor 起動 / tester 起動（軽量化禁止）
- OFF の場合: 通常運用（5-0 で REVIEWER_SET 通常選定、tester は通常判断）
```

### 軽量化したい場合の運用

破壊的変更フラグが ON のときに「REVIEWER_SET を減らしたい」「tester を省略したい」と判断したくなった場合、**スキル本体の独断は禁止**。必ずユーザーに以下の形式で確認する:

```
破壊的変更チェックリスト判定: ON
該当項目: (a) OpenAPI rename + (c) golden 波及

通常はこの状況で REVIEWER_SET 全 5 観点 + refactor-advisor + tester 全工程必須ですが、
[省略したい工程] を省略してよろしいですか？
- yes: 省略を承認（理由をご教示ください）
- no: 全工程実行（推奨）
```

Auto mode でもこのユーザー確認は省略不可。

### スキップ条件

破壊的変更フラグが OFF のときはステップ 5 以降を通常運用で進める。

### 完了後

ステップ 4.85-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。

---

## ステップ 4.95: 直前追加 feedback の自己照合ゲート（チーム起動前に必ず実行）

implementer + reviewer チームを起動する前に、メイン Claude（スキル本体）が以下を実行する。これは「直前 /retro で追加した feedback を、その直後の implementer プロンプト作成時に参照せずに矛盾する除外指示を書いてしまう」即時違反パターン（pir_pattern_registry `[2026-05-13T16:30:00Z]` フラグの根拠 H3）を構造的にブロックするための機械ゲート。

### 4.95-1: 直前 N 日分の追加 feedback を Read

1. `{PROJECT_MEMORY_DIR}/MEMORY.md` を Read（最新 feedback 一覧の把握）
2. 過去 14 日以内に追加・更新された `{PROJECT_MEMORY_DIR}/feedback_*.md` を `ls -t` で抽出（新しい順 5 件まで）
3. 各 feedback の冒頭・「Why」「How to apply」セクションからキーフレーズ（除外対象になりやすい固有名・命名規則・スコープ指定の単語）を抽出

### 4.95-2: implementer プロンプト案の自己照合

implementer プロンプト案の中の以下の記述を、抽出した feedback のキーフレーズと逐一突合する:

- 「除外指示」: 「〇〇は変更しない」「〇〇には触らない」「〇〇は対象外」のような明示的除外
- 「変更しないファイル/フィールド」: 「〇〇は素直な命名のため」「〇〇は既存のままで OK」のような正当化付き保留
- 「スコープ縮小」: 「軽量に〇〇だけ」「最小限の〇〇のみ」のような範囲限定

突合方法は単純な部分一致 grep で十分。

### 4.95-3: 矛盾検出時の動作

矛盾が **1 件でも見つかったらチーム起動を中断**する。

1. 該当 feedback と矛盾箇所を `{RUN_DIR}/feedback-conflict.md` に書き出す:

```markdown
# 直前 feedback との矛盾検出

- 矛盾 feedback: <ファイル絶対パス>
- 該当キーフレーズ: <feedback から抽出した語>
- 矛盾箇所（implementer プロンプト案）: <該当行の引用>
- 推奨アクション: <除外指示取り下げ / plan 再策定 / 範囲拡大>
```

2. ユーザーに以下の形式で通知（Auto mode でも省略不可）:

```
直前 feedback との矛盾を検出しました。
- 矛盾 feedback: <ファイルパス>
- 矛盾箇所: <implementer プロンプト案の該当行>
- 推奨アクション: 除外指示を取り下げて plan を再策定

このまま implementer + reviewer チームを起動しますか？
- yes: 矛盾を承認して起動（理由をご教示ください）
- no: plan 再策定（推奨）
```

### 4.95-4: 照合結果の記録（矛盾なしの場合も必須）

矛盾なしの場合も `{RUN_DIR}/feedback-conflict.md` に「照合した feedback: N 件、矛盾なし」を記録する。retrospector N4.4 の自動測定（D 案で追加予定）で読み取り可能にするための痕跡。

### スキップ条件

過去 14 日以内に追加・更新された `feedback_*.md` が 0 件の場合のみスキップ。それ以外は必須。`{PROJECT_MEMORY_DIR}` 自体が存在しない場合は `feedback-conflict.md` に「project memory なし、照合スキップ」と記録してスキップ。

### 完了後

ステップ 4.85-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。

---

**INNER_LOOP_COUNT = 0、OUTER_LOOP_COUNT = 0 から始めてください。**

## ステップ 5: 実装+レビュー チーム起動（1 implementer + 1〜5 reviewer）

ここが通常の PIR² との違いです。implementer と **REVIEWER_SET に含まれる観点の reviewer**（1〜5 体）を **Agent Teams** として起動し、直接対話させます。

### 5-0: REVIEWER_SET 決定

`REVIEWER_SET` を決定する（planner 系スキルなのでデフォルトは全 5 観点固定）:

1. **ユーザーフラグのパース**: `$ARGUMENTS` に `--reviewers=<roles>` が含まれていればカンマ区切りを観点集合として採用（未知 role は無視）。`--all-reviewers` が含まれていれば全 5 観点を採用。両方指定時は `--reviewers=` を優先
2. **フラグ未指定時のデフォルト**: 全 5 観点 `[correctness, consistency, quality, security, architecture]`（planner が動くタスクは設計判断・多ファイル変更を含むため）
3. フラグ抽出後の残り文字列をタスク説明として扱う
4. 決定した `REVIEWER_SET` を最終サマリーに `REVIEWER_SET=correctness,consistency,...` として記録

### 5-1: チーム作成

TeamCreate ツールでチームを作成してください:

```
team_name: "impl-review"
description: "実装とレビューのチーム。implementerが実装し、REVIEWER_SET に含まれる reviewer が並列で直接レビューしてフィードバックする。"
```

### 5-2A: 起動宣言（Fan-Out Gate — チームメイト並列起動の直前に必ず書く）

チームメイト起動メッセージを送信する **直前のターン本文中** に、以下のテンプレートを必ず生成すること。このテンプレートが本文に出現していないターンで Agent 起動を発火させた場合は、ステップ完了判定を取り消して 5-2A からやり直す。

> **Fan-Out Gate（impl-review チーム）**
> - REVIEWER_SET = [<観点をカンマ区切りで全列挙>]
> - 起動体数 = <N+1>（implementer 1 体 + reviewer N 体 = 1 + len(REVIEWER_SET)、必ず一致）
> - 同一 function_calls ブロックに <N+1> 個の Agent 起動を並べる
> - implementer だけ先に起動・reviewer を後追い追加・観点削減はいずれも違反

このブロックは「起動直前の自己コミットメント」であり、自分の手癖（逐次起動する癖）を止めるためのフェンスとして機能する。OUTER_LOOP_COUNT 差し戻しでチームを再作成する際にも毎回この宣言を書くこと。

### 5-2B: チームメイト並列起動（implementer 1体 + reviewer N 体、同一メッセージ内）

直前ターンで宣言した内容に従い、**REVIEWER_SET に含まれる reviewer と implementer** を同一の `<function_calls>` ブロック内に **N+1 個** 並べて **並列で** 起動する。全て `team_name: "impl-review"` を指定する。REVIEWER_SET に含まれない reviewer セクションはスキップする（該当の TeamCreate 以降のチームメイトも起動しない）。

違反パターン（次のいずれかが発生したら違反として検出し 5-2A からやり直す）:
- function_calls ブロックが 2 ターン以上に分かれる
- 並んだ Agent 起動の数が宣言した N+1 より少ない
- implementer だけ先に起動して reviewer を後追いで追加した
- 直前ターンの宣言テンプレートが省略された

#### implementer (name: "implementer")

```
subagent_type: implementer
team_name: impl-review
name: implementer
model: sonnet
```

プロンプト:

```
あなたは impl-review チームの implementer です。チームには N 体の reviewer（N=REVIEWER_SET の要素数、1〜5）が並列で待機しています。チームリードから REVIEWER_SET を受け取ってください。

REVIEWER_SET の観点と対応する reviewer name:
- correctness → reviewer-correctness (担当: バグ・正確性 / パフォーマンス / リグレッション)
- consistency → reviewer-consistency (担当: 命名規則・構造一貫性 / 同一ロジック全適用網羅性 / 類似ファイル群波及網羅性)
- quality → reviewer-quality (担当: 保守性（局所スコープ）/ テストの質 / データアクセス重複 / スコープ逸脱)
- security → reviewer-security (担当: セキュリティ（OWASP）/ 認可・認証 / シークレット漏洩 / 依存脆弱性)
- architecture → reviewer-architecture (担当: レイヤリング / 循環依存 / 責務逸脱 / 抽象粒度)

PROJECT_MEMORY_DIR=[パス]
RUN_DIR=[パス]
IMPL_INDEX=01
REVIEWER_SET=[カンマ区切りの role リスト。起動時にチームリードから渡される]
（`RESUME_MODE` が `new` または `resume` の場合のみ）HANDOFF_PATH=[$HANDOFF_PATH]

## タスク
以下のパスのプランを Read して実装してください:
{RUN_DIR}/plan.md

`HANDOFF_PATH` が渡された場合は実装完了した項目を `[x]` 化し、新規発見の TODO は `残 TODO` に追記してください（詳細: `~/.claude/pir-handoff.md`）。

## チームでの作業手順

1. プランに基づいて実装を行い、`{RUN_DIR}/implementation-{IMPL_INDEX}.md` に実装完了レポートを Write する
2. 実装が完了したら、**REVIEWER_SET に含まれる reviewer 全員に並列で SendMessage** して同時レビュー依頼する:
   - 送信先: REVIEWER_SET に含まれる role に対応する reviewer-{role}（N 通を同時発火）
   - 本文（全通共通）:
     - 変更したファイル一覧
     - 実装内容の概要
     - `{RUN_DIR}/implementation-{IMPL_INDEX}.md` のパス
     - 「あなたの担当 role の観点でレビューお願いします」
3. REVIEWER_SET の全員からそれぞれ VERDICT 返信（PASS / FAIL）を受け取る
4. VERDICT 集約:
   - **全体 PASS**: REVIEWER_SET の全員が `VERDICT: PASS`
   - **全体 FAIL**: 1体でも `VERDICT: FAIL`
5. 全体 FAIL の場合:
   - REVIEW_LOOP_COUNT += 1
   - REVIEW_LOOP_COUNT >= 3 なら打ち切ってチームリードに最終 VERDICT を報告（下記 7. へ）
   - FAIL を返した全 reviewer の指摘事項（各 reviewer が書き出した `{RUN_DIR}/review-{NN}-{ROLE}.md` を Read して統合）に従って修正する
   - `IMPL_INDEX` をインクリメントして新しい `{RUN_DIR}/implementation-{NN}.md` を書き出し、**REVIEWER_SET 全員に**再度レビュー依頼 SendMessage を送る（PASS を返した観点も再レビュー = 修正による退行検知のため。観点集合は初回選定を維持し途中で追加・削除しない）
6. 全体 PASS になるまで繰り返す
7. チームリードに SendMessage で以下を送る:
   - 最終的な変更ファイル一覧
   - 実装内容の概要
   - レビューループの回数（REVIEW_LOOP_COUNT）
   - REVIEWER_SET に含まれる観点ごとの最終 VERDICT
   - `{RUN_DIR}/implementation-{最終 IMPL_INDEX}.md` の書き出し完了
   - `{RUN_DIR}/review-{最終 REVIEW_INDEX}-{role}.md` N 本の書き出し完了（role は REVIEWER_SET に含まれるもののみ）
   - 「実装+レビュー完了」

## 重要
- REVIEWER_SET の reviewer すべてと並列対話でレビューループを回すこと（逐次送信禁止、同時送信）
- REVIEWER_SET に含まれない reviewer には SendMessage を送らない（そもそも起動されていない）
- チームリードへの報告は全体 PASS 後または打ち切り後のみ
- プラン外の変更は行わない
- 指摘事項の統合: reviewer のレポートをマージ要約せず、各 `{RUN_DIR}/review-{NN}-{ROLE}.md` を直接 Read して修正すること（telephone-game effect 回避）
```

#### reviewer-correctness (name: "reviewer-correctness")

```
subagent_type: reviewer
team_name: impl-review
name: reviewer-correctness
model: sonnet
```

プロンプト:

```
あなたは impl-review チームの reviewer-correctness です。チームメイトは implementer と、別観点の reviewer（REVIEWER_SET に含まれる他 role のみ、0〜4 体）です。各 reviewer は自分の担当観点のみを見ます。REVIEWER_SET にどの role が含まれているかはチームリードから渡されます（ただし自分自身が起動されている時点で REVIEWER_SET には `correctness` が含まれる）。

PROJECT_MEMORY_DIR=[パス]
RUN_DIR=[パス]
REVIEWER_ROLE=correctness
REVIEW_INDEX=01（初回。再レビュー時は implementer からの再依頼ごとに自分でインクリメント: 既存 `{RUN_DIR}/review-*-correctness.md` の最大連番+1）

担当観点（reviewer.md の role マッピングに従う）:
- バグ・正確性
- パフォーマンス
- リグレッション

他観点（命名規則一貫性 / 網羅性 / 保守性 / テストの質 / データアクセス重複 / スコープ逸脱 / セキュリティ / 認可・認証 / シークレット漏洩 / 依存脆弱性 / レイヤリング / 循環依存 / 責務逸脱 / 抽象粒度）は別の reviewer が担当するため、自分の担当外は VERDICT 判定に含めない。気づいた点があれば「担当外で気づいた点（参考）」に Low 相当で記載するのみ。

## チームでの作業手順

1. implementer からレビュー依頼 SendMessage を待つ（本文に implementation-{NN}.md のパスが含まれる）
2. 依頼を受けたら、変更ファイルを Read して**担当観点のみ**レビューする
3. レビュー結果を `{RUN_DIR}/review-{REVIEW_INDEX}-correctness.md` に Write で書き出す
4. レビュー結果を implementer に SendMessage で直接返信:
   - VERDICT: PASS または VERDICT: FAIL（担当観点のみで判定）
   - FAIL の場合: 問題一覧と修正指示、書き出し先パス `{RUN_DIR}/review-{REVIEW_INDEX}-correctness.md` を通知
   - PASS の場合: 良好点があれば記載、書き出し先パスを通知
5. implementer から再依頼（修正完了 + 新 implementation パス）を受けたら REVIEW_INDEX をインクリメントして 2. から繰り返す
6. implementer が全体 PASS を宣言したら終了。打ち切り時（REVIEW_LOOP_COUNT=3）も終了

## 判定基準
- PASS: 担当観点に Critical・High の問題がない場合
- FAIL: 担当観点に Critical または High の問題が1件以上ある場合

## 重要
- implementer と直接対話すること（チームリード経由ではない）
- 他観点のレビューは行わない（別の reviewer が並列で担当）
- レビューログを PROJECT_MEMORY_DIR/pir_reviewer_log.md に追記する（role を含むフォーマット: `## [タスク名] — role:correctness — VERDICT:[...]`）
- 各レビュー回の成果物は必ず `{RUN_DIR}/review-{REVIEW_INDEX}-correctness.md` に書き出すこと
```

#### reviewer-consistency (name: "reviewer-consistency")

```
subagent_type: reviewer
team_name: impl-review
name: reviewer-consistency
model: sonnet
```

プロンプト: reviewer-correctness と同じだが、以下を変える:
- name: reviewer-consistency
- REVIEWER_ROLE=consistency
- 出力パス: `{RUN_DIR}/review-{REVIEW_INDEX}-consistency.md`
- 担当観点: 命名規則・構造一貫性 / 同一ロジック全適用網羅性 / 類似ファイル群波及網羅性
- メモリログ: `role:consistency`

#### reviewer-quality (name: "reviewer-quality")

```
subagent_type: reviewer
team_name: impl-review
name: reviewer-quality
model: sonnet
```

プロンプト: reviewer-correctness と同じだが、以下を変える:
- name: reviewer-quality
- REVIEWER_ROLE=quality
- 出力パス: `{RUN_DIR}/review-{REVIEW_INDEX}-quality.md`
- 担当観点: 保守性（局所スコープ）/ テストの質 / データアクセス重複 / スコープ逸脱
- メモリログ: `role:quality`

#### reviewer-security (name: "reviewer-security")

```
subagent_type: reviewer
team_name: impl-review
name: reviewer-security
model: sonnet
```

プロンプト: reviewer-correctness と同じだが、以下を変える:
- name: reviewer-security
- REVIEWER_ROLE=security
- 出力パス: `{RUN_DIR}/review-{REVIEW_INDEX}-security.md`
- 担当観点: セキュリティ（OWASP）/ 認可・認証 / シークレット漏洩 / 依存脆弱性
- メモリログ: `role:security`

#### reviewer-architecture (name: "reviewer-architecture")

```
subagent_type: reviewer
team_name: impl-review
name: reviewer-architecture
model: sonnet
```

プロンプト: reviewer-correctness と同じだが、以下を変える:
- name: reviewer-architecture
- REVIEWER_ROLE=architecture
- 出力パス: `{RUN_DIR}/review-{REVIEW_INDEX}-architecture.md`
- 担当観点: レイヤリング / 循環依存 / 責務逸脱 / 抽象粒度
- メモリログ: `role:architecture`

### 5-3: チーム完了待ち

implementer から「実装+レビュー完了」の報告を待ちます。報告を受け取ったら:

1. INNER_LOOP_COUNT を報告されたレビューループ回数（REVIEW_LOOP_COUNT）で更新する
2. ドキュメントの実装ログに追記する（REVIEWER_SET に含まれる観点ごとの VERDICT も記載）
3. チームメイト全員（implementer + 起動した reviewer N 体）に shutdown_request を送る
4. ステップ 6 へ進む

### 完了後

ステップ 4.85-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。複数回ループで `IMPL_INDEX` / `REVIEW_INDEX` が増えた場合は最初の 1 回のみマーク、ループ詳細は「中断・再開ログ」に追記。

---

## ステップ 6: テスト (Sonnet)

通常の PIR² と同じ。スキル本体（メイン Claude）が `tester` サブエージェントを `Agent` ツールで起動する（チーム外、通常の Agent）。起動仕様（model / プロンプトに含めるパラメータ一覧）は `~/.claude/skills/pir2/references/tester-prompt.md` を参照。`TEST_INDEX` は初回 `01`、再テスト時はインクリメント。

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
2. `OUTER_LOOP_COUNT >= 3` の場合は **続行可能ゲート（6-G）** へ。判定が「続行」なら 3. へ、「移行」ならステップ 7 へ（失敗として記録）
3. `INNER_LOOP_COUNT = 0` にリセット
4. **ステップ 5 に戻る**（impl-review チームを再作成して実装+レビューループを再実行。`IMPL_INDEX` をインクリメント、`{RUN_DIR}/test-{最新}.md` のパスを tester 指摘事項として渡す。**チーム再作成時も 5-2A の Fan-Out Gate 宣言から実行すること**）
5. tester を再起動（`TEST_INDEX` をインクリメント）
6. PASS になるまで繰り返す

### 6-G: 続行可能ゲート（OUTER_LOOP_COUNT 上限到達時のみ）

詳細プロトコル: `~/.claude/skills/pir2/references/continuation-gate.md` を参照（4 条件の判定基準 / ユーザー確認フォーマット / 運用ルール）。1 条件でも欠けたらゲートを出さず無条件でステップ 7 へ移行する。ユーザーが N を選んだ場合もステップ 7 へ。**Auto mode でも本ゲートはユーザー応答を待つ**（仕様変更判断ゲートのため Auto mode 例外）。1 サイクル中に通過できるのは最大 1 回のみ。

### 完了後

ステップ 4.85-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。

---

## ステップ 6.5: メモリへの記録

`PROJECT_MEMORY_DIR` 配下にタスクの振り返り材料を追記します:

- まず `mkdir -p {PROJECT_MEMORY_DIR}` でディレクトリを作成
- パス: `{PROJECT_MEMORY_DIR}/pir_skill_log.md`
- フォーマット: `## [タスク名] — [気づき・課題・パターン]`

### 完了後

ステップ 4.85-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。

---

## ステップ 7: 振り返り (常に実行)

通常の PIR² と同じ。スキル本体（メイン Claude）が `retrospector` サブエージェントを `Agent` ツールで起動。起動仕様（model 切替条件 / プロンプトに含めるパラメータ一覧 / 起動後の処理）は `~/.claude/skills/pir2/references/retrospector-prompt.md` を参照。`/pir2async` では `ワークフロー種別: pir2async` を明示する（通常の pir2 との比較用）。`PLAN_STRATEGY_CHANGED` 機構は持たないため `false` 固定で渡す。

### 完了後

ステップ 4.85-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。

---

## ステップ 7.5: handoff.md 完了判定と後処理

詳細プロトコル: `~/.claude/skills/pir2/references/handoff-cleanup.md` を参照。要点: `$HANDOFF_PATH` が存在する場合、全 `[x]` なら削除、残項目ありなら `最終更新` 行を更新する。最終サマリーに結果を記載すること。`$HANDOFF_PATH` が存在しない場合はスキップ。

### 完了後

ステップ 4.85-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。全 checkbox が `[x]` になった場合は最終サマリー（ステップ 8）に「next-steps.md: 全項目完了」と記載する。

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
