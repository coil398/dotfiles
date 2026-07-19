---
name: "cursor-pir2"
description: "コーディングタスクを Plan → Implement → Review → Retrospect の4フェーズで実行する。複雑なタスク・設計が必要なタスク・品質保証が重要なタスク、大きな機能追加・リファクタリング・アーキテクチャ変更に使う。「ちゃんと作りたい」「しっかり実装して」「品質重視で」といった要望にも対応する。ユーザーが /cursor-pir2 と入力したら必ずこのスキルを使う。"
argument-hint: "[タスクの説明]"
---

<!-- Cursor native overlay: seeded from .agents/skills; edit here for Cursor mechanics -->

> **Cursor 実行時の注意（第2波）**
> - 子エージェントは `Task` ツール（`subagent_type`）で起動する。Claude の `Agent` ツール語彙は使わない
> - メインエージェントがオーケストレーター。VERDICT ループ・ユーザー確認ゲート・ループカウンタはメインが保持する
> - Claude 専用機能（`TeamCreate` / Agent Teams / `~/.claude/hooks`）は Cursor では非対応のためスキップする（必要なら通常の直列 Task 起動へ縮退）
> - ベンダーモデル名（reasoning / coding / reasoning 等）はハードコードしない。agent overlay の `role=reasoning|coding` と Cursor UI の運用既定に従う


# PIR² — Plan → Implement → Review → Retrospect

PIR²ワークフローを実行します。このスキル本体（= メインエージェント）がオーケストレーターとなり、Plan → Implement → Review → Test → Retrospect を進めます。

Cursor では子エージェントは `Task` ツールで起動する。`/cursor-pir2` の明示起動を subagent 使用許可とみなしてよい。探索 → 計画 → 単一実装者 → レビュー → テストの分業を基本形にする。メインエージェントがオーケストレーターと最終判断（VERDICT ループ・ユーザー確認ゲート）を持ち続け、実装 subagent がさらに subagent を起動する前提にはしない。並列 writer は禁止し、Task / subagent が利用できない場合は、同じフェーズ境界と記録ファイルを保ったままメインエージェントが直接実行してください。

**タスク**: $ARGUMENTS

---

## ステップ 1: プロジェクトメモリパスと RUN_DIR の確定

以下の Bash コマンドで `PROJECT_ROOT` / `PROJECT_MEMORY_DIR` / `RUN_DIR` / `HANDOFF_PATH` を確定し、以降のすべてのステップで使用してください:

```bash
PROJECT_ROOT="$(pwd)"
# sanitized-cwd 計算は .cursor/skills/pir2/references/sanitized-cwd.md を SSOT とする
# （Codex harness の sanitize 仕様変更時はこの SSOT のみを更新し、9 ファイルに横展開）
sanitized_cwd="$(pwd | sed 's|[^a-zA-Z0-9]|-|g')"
PROJECT_MEMORY_DIR="${HOME}/.cursor/projects/${sanitized_cwd}/memory"
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

次に `RESUME_MODE` をスキル本体（メインエージェント）が判定する:

- `$ARGUMENTS` に `引継い` / `続き` / `resume` / `Resume` / `RESUME` / `handoff` / `Handoff` / `HANDOFF` / `carry on` のいずれかが含まれる → `RESUME_MODE=resume`
- 含まれず、かつ `$HANDOFF_PATH` のファイルが存在する → `RESUME_MODE=passive-notice`
- それ以外 → `RESUME_MODE=new`

`RESUME_MODE` に応じて以降の挙動を分岐させる（詳細プロトコル: `~/.claude/pir-handoff.md`）:

- `resume`: ステップ 2（ブレスト）をスキップし、planner への入力に `HANDOFF_PATH=$HANDOFF_PATH` を含めて「handoff.md の未チェック項目のみを planning 対象にせよ」と指示する。スキル本体は handoff.md を上書きしない
- `passive-notice`: 「💡 前回の handoff が残っています: `$HANDOFF_PATH`」とユーザーに表示し、通常の新規タスクフローで続行する（handoff.md は触らない）
- `new`: 通常の新規タスクフロー。planner の plan.md 完成直後にスキル本体が handoff.md 初期版を Write する（プランのステップを `[ ]` チェックリスト化）

retrospector フェーズ完了後、スキル本体は handoff.md を Read し、全項目が `[x]` なら削除、残項目ありなら「最終更新」タイムスタンプを更新する。

このステップで内部状態フラグ `PLAN_STRATEGY_CHANGED=false` を初期化してください。これはユーザー方針切替（ステップ 4.6 の「別案」選択など）による plan 再策定が発生した場合のみ `true` にセットされ、planner 側 3.3「v1 判断白紙化チェック」の発動条件として使われます。EXPLORATION_NEEDED ループ（ステップ 4.5）の追加探索による再策定では立てません。

以降の各フェーズまたはsubagentへのプロンプトには必ず `PROJECT_MEMORY_DIR=[パス]` および `RUN_DIR=[パス]` を含めてください。

---

## ステップ 2: ブレインストーミング（状況に応じて実施）

タスクの仕様を評価し、以下のいずれかに該当する場合は brainstorm スキルを実行してから次のステップへ進んでください：

- 要件が曖昧で複数の解釈が可能
- アーキテクチャ上の選択肢が複数あり、どれを選ぶかユーザーに確認が必要
- ユーザーとの対話を通じて設計を固めたほうが手戻りリスクを減らせると判断される

実行方法: Cursor の skill として `brainstorm` を呼び出す（または同等手順をメインが実行）。ユーザーとの対話で固まった設計はステップ4の planner に渡してください。

該当しない場合（タスクが明確、既存の設計がある、`docs/brainstorm/` に関連する設計ドキュメントが存在する）はスキップしてください。

> **brainstorm 完了後は必ず自動でステップ3へ進むこと**。「設計ドキュメントを保存しました」と単独ターンで区切ってユーザーの承認を待つのは禁止。`/cursor-pir2` は一度起動されたら最終サマリー（ステップ12）まで止まらず進める設計であり、brainstorm の最終出力「次のステップとして `/cursor-writing-plan` で実装プランを作成できます」は `/cursor-brainstorm` 単独起動時向けの案内なので、`/cursor-pir2` 経由では無視して続行する。承認を挟んでよいのは `.cursor/skills/pir2/SKILL.md` 内で明示的にユーザー確認が指定されているポイント（既存パターン逸脱の事前申告・ステップ6.5 未解決事項確認）のみ。

---

## ステップ 3: 探索フェーズ（explorer）

コードベース探索は read-heavy なので、subagent が利用可能なら `explorer` を優先して委譲してください。subagent が利用できない、または小規模変更で直接探索の方が明らかに速い場合は、メインエージェント が `rg` / `rg --files` / Read で直接探索してよい。ただし探索結果は必ず `{RUN_DIR}/exploration-{NN}.md` に保存し、推測と確認済み事実を分けて扱うこと。

### 起動ルール

- **最低1回実行**: タスクの規模にかかわらず初回探索は必須。subagent 利用可なら最低1体、利用不可ならメインエージェント が直接実行
- **最大3体並列**: 調査領域が独立している場合のみ並列起動
- **role 使い分け**（モデル名はピンしない。Cursor UI の運用既定に従う）:
  - coding（浅め）: 広く浅い調査（ファイル構造、パターン列挙、grep 結果の収集）。最大3体並列可
  - coding（深め）: 深く読み解く調査（既存ロジックの意味理解、設計意図の把握）。最大1体
  - reasoning: 深め coding でも読み解けなかった場合のフォールバック（高度な間接参照、メタプログラミング、複雑な状態遷移）。最大1体、他層と並列起動しない
- **ミックス起動可**: 広さと深さを同時に欲しい場合は浅め coding と深め coding を同ターンで並列起動してよい。reasoning フォールバックは単独起動とする
- **reasoning 発動条件**: 深め coding の探索レポートで「既存ロジックの意図を推測で補っている」「複数回の間接参照で追跡が途中で途切れている」「メタプログラミング/DSL により表層の grep では意味が取れない」と判断した場合のみ。常用しない

### プロンプトに必ず含めるパラメータ
- `PROJECT_MEMORY_DIR=[パス]`
- `RUN_DIR=[パス]`
- `EXPLORATION_INDEX=NN`（初回=`01`、並列起動時はスキル本体が `01`/`02`/`03` と割り振る）
- 「探索レポート本体は `{RUN_DIR}/exploration-{NN}.md` に書き出し、チャットには要約のみ返してください」
- 「探索フェーズではタスクのコード実装を行わず、`git add` / `git commit` などリポジトリ状態を変更する git 操作も一切行わないでください。実装が必要だと判明したら探索レポートの『呼び出し元への依頼』に回してください」（explorer は `Write` / `Bash` を持つため、明示しないと探索の延長で実装・コミットまで踏み込むロール逸脱が起こりうる）

### プロンプトに必ず含める調査観点

- 変更対象と同一ドメイン・同一レイヤーの既存実装パターン（類似機能がどう実装されているか）
- 再利用可能な既存ユーティリティ・ヘルパー関数
- 変更対象のメソッド/関数内の他分岐が設定しているフィールド・処理の一覧
- フレームワークが自動処理する機能（新規コードで手動実装すべきでないもの）
- 調査対象がライブラリ・フレームワークの API 仕様に関わる場合は、公式 README / doc / Issue を WebFetch/WebSearch で裏取りし参照 URL をレポートに含めること（推測や記憶で結論を埋めさせない）

### 追加探索

初回レポートで不明点があれば追加で explorer を起動してください。回数上限なし。推測でプランを埋めるくらいなら追加探索を回す。追加探索時は `EXPLORATION_INDEX` を既存 `{RUN_DIR}/exploration-*.md` の最大値+1 に設定する。

### ライブラリ選定が必要な場合

新しいライブラリ・フレームワークの導入判断が必要なら `tech-validator` エージェントを起動する（既存の依存関係で解決できる場合はスキップ）。

---

## ステップ 4: プラン策定（planner）

設計判断が重い場合は `planner` subagent を起動し、タスク内容と探索レポート全文を渡してください。小規模・明確な変更では、メインエージェント が planner 観点を直接適用して `{RUN_DIR}/plan.md` を作成してよい。

- role: coding（モデル名はピンしない）
- プロンプト:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `PLAN_STRATEGY_CHANGED=$PLAN_STRATEGY_CHANGED`（現在の値。初回起動時は `false`、ステップ 4.6 で「別案」が選ばれた直後の再起動時のみ `true`）
  - タスク内容
  - `{RUN_DIR}/exploration-*.md` のパス一覧（planner は本文を自分で Read する）
  - ブレインストーミング結果（ステップ2で実施した場合）
  - 「完全に独立した実装 shard がある場合のみ `IMPLEMENTATION_SHARDS` を提案してください。判定基準は `.cursor/skills/pir2/references/implementation-delegation.md` に従うこと」
  - 「プランレポート本体は `{RUN_DIR}/plan.md` に書き出し、チャットには要約＋EXPLORATION_NEEDED の有無のみ返してください」

planner からプラン要約を受け取ってください。

### 既存パターン逸脱の事前申告

planner から「既存構造と異なる構成を採用する」判断が含まれたプランが返ってきた場合、実装着手前にユーザーに差分（既存 N 件中 M 件の構成 / 今回採用しようとしている構成 / 逸脱理由 / 代替案）を提示し、承認を得ること。承認なしに次のステップに進んではならない。

---

## ステップ 4.5: 能動的再探索ループ（最大5回）

詳細プロトコル: `.cursor/skills/pir2/references/exploration-loop.md` を参照（収束判定ロジック / ループ本体 / 既存パターン逸脱の事前申告タイミング）。

要点: planner の返り値要約に `### EXPLORATION_NEEDED` の `- topic` が残る間、追加探索 → planner 再起動を最大 5 回繰り返す。収束したらステップ 5 へ進む。`REPLAN_COUNT = 0` から開始し、ハードキャップ到達時は最終サマリー（ステップ12）に「**planner が依然追加探索を要求中（ハードキャップ5回到達）**: [topic 一覧]」と明記する。

---

## ステップ 4.6: プラン選択肢のユーザー確認（該当時のみ・Auto mode でも例外なし）

詳細プロトコル: `.cursor/skills/pir2/references/plan-choice-gate.md` を参照（検出トリガー / 確認フォーマット / 運用ルール / 別案の字義解釈確認 / v2→v3 切替の真意確認）。

要点: planner レポートに「複数案」「USER_DECISION_REQUIRED」「スコープ縮小」「外部依存不足」のいずれかが含まれたら**ステップ 5 前にユーザー確認必須（Auto mode でも例外なし）**。planner の推奨案を必ず明示する。ユーザーが別案 or 方針切替した場合は `PLAN_STRATEGY_CHANGED=true` をセットして planner を再起動（字義解釈確認を先に実施）。該当なしはスキップしてステップ 5 へ。

---

## ステップ 5: プラン保存

`docs/plans/` ディレクトリがなければ作成し、以下の形式でプランを保存してください:

**保存先**: `docs/plans/YYYY-MM-DD-<feature>.md`（YYYY-MM-DD は今日の日付）

保存したらユーザーにパスを提示:

```
プラン: docs/plans/YYYY-MM-DD-<feature>.md
```

ファイル内容のテンプレート:

```markdown
# [タスク名] 実装記録

_作成: YYYY-MM-DD | ステータス: 進行中_

## 目標

[タスクの概要]

## 実装計画

- [ ] ステップ1: [ステップ名]
- [ ] ステップ2: [ステップ名]
...

---

## 設計詳細

[{RUN_DIR}/plan.md を Read し、その内容をここに転記する]

---

## 実装ログ

### 実装完了

- 変更ファイル: （実装完了後に埋める）
- 実装内容: （実装完了後に埋める）

---

> このドキュメントは内容を確認後に削除してください。
> `rm docs/plans/YYYY-MM-DD-<feature>.md`
```

---

## ステップ 5.5: handoff.md 初期版生成（`RESUME_MODE=new` の場合のみ）

`RESUME_MODE=resume` または `passive-notice` の場合はこのステップをスキップしてください（既存 handoff.md を温存する）。

`RESUME_MODE=new` の場合のみ実行:

1. `{RUN_DIR}/plan.md` を Read し、「実装ステップ」に相当する項目を抽出する
2. `$HANDOFF_PATH` に `~/.claude/pir-handoff.md` の「フォーマット」節に従った内容で Write する:
   - `最終更新`: 現在時刻 + `run: $(basename $RUN_DIR)`
   - `タスク`: ユーザー指示の一行要約
   - `背景・決定事項`: plan.md から抽出した主要決定（なければ空セクションのまま）
   - `残 TODO`: 抽出した実装ステップを `- [ ] <ステップ名>` 形式に変換
   - `既知の問題 / 要確認`: 空セクションで用意
   - `関連 artifact`: `最新 plan: {RUN_DIR}/plan.md`

handoff.md のパスをユーザーに提示:

```
handoff: $HANDOFF_PATH
```

`RESUME_MODE=passive-notice` だった場合はこの時点で「💡 前回の handoff が残っています: `$HANDOFF_PATH`（`引継いで` で resume 可能）」とユーザーに表示してから次ステップへ。

---

## ステップ 5.6: 次ステップキュー初期版生成

詳細プロトコル: `.cursor/skills/pir2/references/next-steps-queue.md` を参照（初期 Write テンプレート / 5.6-2 checkbox 更新手順 / 5.6-3 中断後の Read ルール / スキップ条件）。

要点: `{RUN_DIR}/next-steps.md` にsubagent起動予定 checkbox リストを Write する。**ユーザー会話による中断後、スキル本体は次の判断前に必ずこのファイルを Read してから動く**。各ステップ完了直後に checkbox を `[x]` + `<!-- done: ISO8601 -->` に更新する（必須運用）。`RESUME_MODE=resume` の場合は handoff.md 由来の未完了項目を統合する。

---

## ステップ 5.7: 破壊的変更チェックリスト + 動作変更チェック（implementer 起動前に必ず実行）

詳細プロトコル: `.cursor/skills/pir2/references/destructive-change-check.md` を参照（pir2 専用の 2 軸マトリクス判定 / 判定項目 a〜e・f1〜f3 / 書き出しフォーマット / 軽量化確認 / スキップ条件）。

要点: plan.md と explorer レポートを Read して「破壊的変更フラグ（a〜e）」と「動作変更フラグ（f1〜f3）」を独立に判定。結果を `{RUN_DIR}/destructive-change-check.md` に書き出し、後段（reviewer / refactor-advisor / tester）の戦略をマトリクスで決定。フラグ ON で軽量化したい場合はユーザー確認必須。完了後は 5.6-2 に従い next-steps.md の checkbox を更新する。

---

## ステップ 5.8: 直前追加 feedback の自己照合ゲート（実装開始前に必ず実行）

詳細プロトコル: `.cursor/skills/pir2/references/feedback-conflict-gate.md` を参照（feedback Read → プロンプト照合 → 矛盾検出時の中断フォーマット → 記録 → スキップ条件）。

要点: 過去 14 日以内の feedback_*.md 5 件を Read し、実装プロンプト案の除外指示・スコープ縮小と突合。矛盾 1 件でも検出したら実装開始を中断 → ユーザー確認。矛盾なしも `{RUN_DIR}/feedback-conflict.md` に「照合 N 件、矛盾なし」を記録。完了後は 5.6-2 に従い next-steps.md の checkbox を更新する。

---

## ステップ 6: 実装（implementer）

`INNER_LOOP_COUNT = 0`、`OUTER_LOOP_COUNT = 0` から開始してください。

詳細プロトコル: `.cursor/skills/pir2/references/implementation-delegation.md` を参照（単一 implementer / 複数 implementer shard / main fallback の判定、shard 禁止条件、プロンプト、統合確認）。

要点: デフォルトは `IMPLEMENTATION_ACTOR=implementer-subagent`（単一 writer）。planner が `IMPLEMENTATION_SHARDS` を提示し、かつ shard 同士のファイル所有範囲・依存順序・共有生成物が完全に分離している場合のみ `IMPLEMENTATION_ACTOR=implementer-shards` として最大3体まで並列実装してよい。subagent 不可・小変更・plan 未成熟の場合のみ `IMPLEMENTATION_ACTOR=main` に縮退する。どの場合もメインエージェント は完了後に diff と `{RUN_DIR}/implementation-*.md` を読み直して最終責任を持つ。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する（`IMPL_INDEX` が複数回ループする場合は最初の 1 回のみマーク。2 回目以降のループは「中断・再開ログ」セクションに追記する）。

---

## ステップ 6.5: 実装者の未解決事項ユーザー確認（該当時のみ）

implementer の返り値要約で「注意点・未解決事項の有無」が **「あり」** の場合、次ステップへ進む前に必ずユーザーに判断を仰ぐ。スキル本体がスコープ縮小や仕様変更を独断してはならない。

### 6.5-1: 内容の確認

1. `{RUN_DIR}/implementation-{最新 IMPL_INDEX}.md` の「注意点・未解決事項」セクションを Read する
2. 未解決事項の性質を分類する:
   - **(a) プラン逸脱の報告**（プランの一部が実装できなかった / 前提が崩れた）
   - **(b) プラン通りに実装したが新たに発見した問題**（スコープ外の副次的な気づき）
   - **(c) 判断を委ねる事項**（implementer が明示的に「planner/ユーザーに判断を委ねる」と記載した箇所）

### 6.5-2: ユーザーへの提示

未解決事項の要点と分類を1〜3文で要約し、以下の選択肢を提示してユーザーの判断を受け取る:

- **(A) スコープ縮小を承認してレビューへ進む**: 未解決事項を次フェーズ繰越しとして記録し、ステップ 7 へ。`docs/plans/YYYY-MM-DD-*.md` の「注意点・未解決事項」セクションにも繰越し内容を明記する
- **(B) 再プラン**: ステップ 4 に戻り、planner に現在の implementation 状態と未解決事項を渡してプラン再策定（fallback 設計切り替え）。`{RUN_DIR}/implementation-{最新}.md` のパスも planner に渡すこと
- **(C) 追加指示で再実装**: implementer を再起動し、ユーザーからの追加指示を渡して再試行。`IMPL_INDEX` をインクリメントする

### 6.5-3: 判断の記録

ユーザーの選択と理由を `{RUN_DIR}/user-decisions.md` に追記する（ファイルがなければ作成）。形式:

```
## [YYYY-MM-DD HH:MM:SS] 未解決事項ユーザー確認

### 未解決事項の要約
[1〜3文]

### 選択
[A / B / C]

### 理由（ユーザーから得られた場合）
[理由]
```

### 6.5-4: スキップ条件

implementer の返り値要約で「注意点・未解決事項の有無」が **「なし」** の場合は本ステップをスキップし、ステップ 7 へ直接進む。

> **重要**: 仕様変更判断（スコープ縮小・フェーズ繰越し・API 変更等）はスキル本体ではなくユーザーに委ねる。「小さな変更だから」「fallback で動くから」を理由にユーザー確認を省略してはならない。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。スキップした場合も「スキップ済み」として `[x]` にする。

---

## ステップ 7: レビューループ（reviewer ハイブリッド並列、最大3回）

### 7-1: 観点セット決定

`REVIEWER_SET` を決定する（planner 系スキルなのでデフォルトは全 5 観点固定）:

1. **ユーザーフラグのパース**: `$ARGUMENTS` に `--reviewers=<roles>` が含まれていればカンマ区切りを観点集合として採用（未知 role は無視）。`--all-reviewers` が含まれていれば全 5 観点を採用。両方指定時は `--reviewers=` を優先
2. **フラグ未指定時のデフォルト**: 全 5 観点 `[correctness, consistency, quality, security, architecture]`（planner が動くタスクは設計判断・多ファイル変更を含むため）
3. フラグ抽出後の残り文字列をタスク説明として扱う（以降のサマリ等で `$ARGUMENTS` をそのまま使っていた箇所は、フラグ除去後のタスク説明を使う）
4. 決定した `REVIEWER_SET` を最終サマリーに `REVIEWER_SET=correctness,consistency,...` として記録

### 7-2A: 起動宣言（Fan-Out Gate — 並列レビューの直前に必ず書く）

reviewer 並列起動またはメインエージェント による複数観点レビューの **直前のターン本文中** に、以下のテンプレートを必ず生成すること。このテンプレートが本文に出現していないターンでレビューを開始した場合は、ステップ完了判定を取り消して 7-2A からやり直す。

> **Fan-Out Gate（reviewer）**
> - REVIEWER_SET = [<観点をカンマ区切りで全列挙>]
> - 起動体数 = <N>（= len(REVIEWER_SET)、必ず一致）
> - subagent 利用時: 同一ターンで <N> 個の reviewer subagent を起動する
> - subagent 非利用時: メインエージェント が <N> 観点を同一レビューサイクル内で全て実行する
> - 1 体ずつの後追い起動・観点削減はいずれも違反

このブロックは「レビュー直前の自己コミットメント」であり、ユーザーへの報告ではなく観点漏れを止めるためのフェンスとして機能する。再レビュー時（7-4 からの差し戻し時）にも毎回この宣言を書くこと。REVIEWER_SET は初回選定を維持し、再レビュー時に観点を勝手に減らさないこと。

### 7-2B: 並列レビュー実行

直前ターンで宣言した REVIEWER_SET の各観点について、subagent が利用可能なら reviewer subagent を同一ターンで **N 個** 起動する。subagent が利用できない場合は、メインエージェント が各 `REVIEWER_ROLE` の観点を分割して同一レビューサイクル内で実行し、`{RUN_DIR}/review-{REVIEW_INDEX}-{ROLE}.md` を観点ごとに書き出す。

詳細仕様（観点マッピング / 違反パターンと検出 / 違反検出時のリカバリ / reviewer 起動パラメータ）: `.cursor/skills/pir2/references/fan-out-gate.md` を参照。

> **注**: refactor-advisor はこのステップでは起動しない。reviewer 全員 PASS 後のステップ 7.5 で 1 回だけ起動する。

### 7-3: VERDICT 集約

**今回起動した reviewer** の VERDICT を以下のルールで集約する:

- **全体 VERDICT = PASS**: 起動した全員が `VERDICT: PASS` の場合
- **全体 VERDICT = FAIL**: 1体でも `VERDICT: FAIL` を返した場合

### 7-4: 判定

- 全体 `VERDICT: PASS` → ステップ 7.5 へ（refactor-advisor の起動 + 提案ゲート）
- 全体 `VERDICT: FAIL` →
  1. `INNER_LOOP_COUNT += 1`
  2. `INNER_LOOP_COUNT >= 3` ならステップ 7.5 へ強制移行（失敗として記録。この場合 refactor-advisor はスキップしてステップ 8 へ直接進む）
  3. 実装修正を行う（`IMPL_INDEX` をインクリメント、**FAIL を返した全 reviewer の `{RUN_DIR}/review-{最新}-{ROLE}.md` パスを全て読む**、`{RUN_DIR}/plan.md` も読む。マージ要約は作らず、各レポートを直接根拠にする）。reviewer 指摘がファイル単位で分離できる場合は `implementation-delegation.md` の review-fix shard ルールに従い、複数 implementer で並列修正してよい。分離できない場合は `IMPLEMENTATION_ACTOR=implementer-subagent` なら同じ implementer ロールを再起動し、`IMPLEMENTATION_ACTOR=main` ならメインエージェント が修正する
  4. **7-2A（Fan-Out Gate 宣言）→ 7-2B（並列発火）の手順で** reviewer を **同じ REVIEWER_SET で** 並列で再起動（`REVIEW_INDEX` をインクリメント、最新の `{RUN_DIR}/implementation-{最新}.md` のパスを渡す。PASS を返した観点も再レビューする = 修正による新たな退行を検知するため。観点集合は初回選定を維持し途中で追加・削除しない。**再レビュー時も Fan-Out Gate を省略しないこと**）
  5. 全体 PASS になるまで繰り返す

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する（複数回ループで `REVIEW_INDEX` が増えた場合は最初の 1 回のみマーク、ループ詳細は「中断・再開ログ」に追記）。

---

## ステップ 7.5: リファクタ提案（refactor-advisor 起動 → ゲート → 任意適用）

全体 VERDICT が PASS の場合のみ実行。FAIL で INNER_LOOP_COUNT 上限到達の場合はスキップしてステップ 8 へ。

詳細プロトコル: `.cursor/skills/pir2/references/refactor-advisor-gate.md` を参照（refactor-advisor 起動仕様 / 提案存在確認 / ユーザー提示フォーマット / ユーザー選択の処理 / リファクタ適用の implementer 再起動 / 退行検知の再 reviewer ループ）。

要点:
- refactor-advisor は **1 体だけ起動**（reviewer 並列とは別系統、直列）
- 提案がある場合のみユーザーゲートを開く（`all` / 番号指定 / `none` / `custom`）
- 適用後は **7-2A（Fan-Out Gate 宣言）→ 7-2B（並列発火）** で reviewer 再起動し退行検知
- 再 reviewer FAIL なら 7-4 の差し戻しループに合流（`INNER_LOOP_COUNT` 継続）
- refactor-advisor は同一 run 内 **1 回のみ**（無限リファクタループ防止）

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。スキップ条件（reviewer FAIL で上限到達した場合）に該当した場合も `[x]` に更新（スキップ理由を「中断・再開ログ」に記録）。

---

## ステップ 8: テストループ（tester、最大3回）

### 8-1: tester 起動

テストは read/log-heavy なので、subagent が利用可能なら `tester` を起動する。利用できない場合はメインエージェント が同じ仕様で実行する。起動仕様（model / プロンプトに含めるパラメータ一覧）は `.cursor/skills/pir2/references/tester-prompt.md` を参照。`TEST_INDEX` は初回 `01`、再テスト時はインクリメント。

### 8-2: 判定

- `VERDICT: PASS` → ステップ 9 へ
- `VERDICT: FAIL` →
  1. `OUTER_LOOP_COUNT += 1`
  2. `OUTER_LOOP_COUNT >= 3` の場合は **続行可能ゲート（8-2-G）** へ。判定が「続行」なら 3. へ、「移行」ならステップ 9 へ（失敗として記録）
  3. `INNER_LOOP_COUNT = 0` にリセット
  4. 実装修正を行う（`IMPL_INDEX` をインクリメント、`{RUN_DIR}/test-{最新}.md` のパスを tester 指摘事項として読む）。`IMPLEMENTATION_ACTOR=implementer-subagent` なら同じ implementer ロールを再起動し、`IMPLEMENTATION_ACTOR=implementer-shards` なら `implementation-delegation.md` の再実装ルールに従う。`IMPLEMENTATION_ACTOR=main` ならメインエージェント が修正する
  5. **ステップ 7 に戻る**（レビューループを再実行、`REVIEW_INDEX` は継続インクリメント）
  6. tester を再起動（`TEST_INDEX` をインクリメント）
  7. PASS になるまで繰り返す

### 8-2-G: 続行可能ゲート（OUTER_LOOP_COUNT 上限到達時のみ）

詳細プロトコル: `.cursor/skills/pir2/references/continuation-gate.md` を参照（4 条件の判定基準 / ユーザー確認フォーマット / 運用ルール）。1 条件でも欠けたらゲートを出さず無条件でステップ 9 へ移行する。ユーザーが N を選んだ場合もステップ 9 へ。**Auto mode でも本ゲートはユーザー応答を待つ**（仕様変更判断ゲートのため Auto mode 例外）。1 サイクル中に通過できるのは最大 1 回のみ（OUTER_LOOP_COUNT=4 で再 FAIL したら無条件にステップ 9 へ）。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する（複数回ループで `TEST_INDEX` が増えた場合も同様、最初の 1 回のみマーク）。

---

## ステップ 9: ウォークスルー生成（メインエージェント が直接）

変更されたファイルを Read して最終的な実装内容を確認し、ウォークスルーを作成する。フル版（内部記録）とサマリー版（最終サマリーに転記）の 2 形式を作成し、フル版は実装記録ドキュメント（ステップ 5 で作成）の「実装ログ」セクションに埋める。

詳細テンプレート（フル版・サマリー版・サマリー版の原則）: `.cursor/skills/pir2/references/walkthrough-templates.md` を参照。

最重要原則: **推測でコードを書かない。実際に Read したコードのみ引用する**。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。

---

## ステップ 10: メモリへの記録

`PROJECT_MEMORY_DIR` 配下にタスクの振り返り材料を追記します:

- まず `mkdir -p {PROJECT_MEMORY_DIR}` でディレクトリを作成
- パス: `{PROJECT_MEMORY_DIR}/pir_skill_log.md`
- フォーマット: `## [タスク名] — [気づき・課題・パターン]`
- **モデル/実行形態スイープ計装**（後日「どのフェーズを安価モデルに下げられるか」「subagent を使う価値があるか」を判断する素材。機械集計しやすいよう固定プレフィックスで必ず1行記録する）:
  `- 使用モデル: explorer=<model×体数>, planner=<model>, implementer=<model>, reviewer=<model×体数>, tester=<model>, retrospector=<model> / REPLAN=<N> / INNER_LOOP=<N> / OUTER_LOOP=<N>`
  今回 run で各フェーズを**実際に実行した形態**を埋める。subagent を使わなかったフェーズは `main:<model>` と記録する。スイープ実験本体は計装でデータが溜まってから別途行う。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。

---

## ステップ 11: 振り返り（retrospector、常に実行）

振り返りはメインエージェント が実行してよい。subagent が利用可能で、今回 run が大きくログ分析を分離した方がよい場合のみ `retrospector` を起動する。起動仕様（model 切替条件 / プロンプトに含めるパラメータ一覧 / 起動後の処理）は `.cursor/skills/pir2/references/retrospector-prompt.md` を参照。`/cursor-pir2` では `ワークフロー種別: pir2` を明示し、`PLAN_STRATEGY_CHANGED` の現在値も渡すこと（true なら今回 run でユーザー方針切替が発生し planner v1→v2 再策定が走った）。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。

---

## ステップ 11.5: handoff.md 完了判定と後処理

詳細プロトコル: `.cursor/skills/pir2/references/handoff-cleanup.md` を参照。要点: `$HANDOFF_PATH` が存在する場合、全 `[x]` なら削除、残項目ありなら `最終更新` 行を更新する。最終サマリーに結果を記載すること。`$HANDOFF_PATH` が存在しない場合はスキップ。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。全 checkbox が `[x]` になった場合は最終サマリー（ステップ 12）に「next-steps.md: 全項目完了」と記載する。

---

## ステップ 12: 最終サマリーの提示

詳細テンプレートは `.cursor/skills/pir2/references/final-summary-template.md` を参照。実装記録、変更ファイル、レビュー結果、refactor-advisor 結果、テスト結果、再探索回数、RUN_DIR、振り返り、メタ改善推奨を含める。

---

## ステップ 13: ウォークスルーの提示

ステップ9で作成したサマリー版ウォークスルーをユーザーに提示してください。フル版は内部記録として保持し、ユーザーから「詳細を見せて」等の要求があれば提示します。

末尾に `詳細なウォークスルーが必要な場合はお知らせください。` と添えてください。
