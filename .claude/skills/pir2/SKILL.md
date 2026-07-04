---
name: pir2
description: コーディングタスクを Plan → Implement → Review → Retrospect の4フェーズで実行する。複雑なタスク・設計が必要なタスク・品質保証が重要なタスク、大きな機能追加・リファクタリング・アーキテクチャ変更に使う。「ちゃんと作りたい」「しっかり実装して」「品質重視で」といった要望にも対応する。ユーザーが /pir2 と入力したら必ずこのスキルを使う。
argument-hint: [タスクの説明]
---

# PIR² — Plan → Implement → Review → Retrospect

PIR²ワークフローを実行します。このスキル本体（= メイン Claude）がオーケストレーターとなり、explorer → planner → implementer → reviewer → tester → retrospector を `Agent` ツールで順に起動します。サブエージェントも v2.1.172 以降は `Agent` ツールでネスト起動できますが、PIR² では制御フロー（起動・ループ管理・VERDICT 集約・ユーザー確認ゲート）をスキル本体に集約する設計とし、サブからのネスト起動は read-only の探索（explorer）に限ります。

**タスク**: $ARGUMENTS

---

## ステップ 1: プロジェクトメモリパスと RUN_DIR の確定

以下の Bash コマンドで `PROJECT_ROOT` / `PROJECT_MEMORY_DIR` / `RUN_DIR` / `HANDOFF_PATH` を確定し、以降のすべてのステップで使用してください:

```bash
PROJECT_ROOT="$(pwd)"
# sanitized-cwd 計算（PROJECT_MEMORY_DIR 専用）は ~/.claude/skills/pir2/references/sanitized-cwd.md を SSOT とする
# 成果物置き場（RUN_DIR/HANDOFF_PATH）の基底パスの SSOT は run-dir-base.md。PROJECT_ROOT 基底になったため
# RUN_DIR/HANDOFF_PATH 側の sanitize は不要（run_feature の sanitize のみ下記に別途残る）
sanitized_cwd="$(pwd | sed 's|[^a-zA-Z0-9]|-|g')"
PROJECT_MEMORY_DIR="${HOME}/.claude/projects/${sanitized_cwd}/memory"
run_ts="$(date +%Y%m%d-%H%M%S)"
run_feature="$(printf '%s' "$ARGUMENTS" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
[ -z "$run_feature" ] && run_feature="task"
RUN_DIR="${PROJECT_ROOT}/.ai-pir-runs/${run_ts}-${run_feature}"
mkdir -p "$RUN_DIR"
# 中間ファイルを git 追跡から外す（git リポジトリのときのみ）
if git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  grep -qxF '/.ai-pir-runs/' "${PROJECT_ROOT}/.gitignore" 2>/dev/null || echo '/.ai-pir-runs/' >> "${PROJECT_ROOT}/.gitignore"
fi
HANDOFF_PATH="${PROJECT_ROOT}/.ai-pir-runs/handoff.md"
echo "PROJECT_ROOT=$PROJECT_ROOT"
echo "PROJECT_MEMORY_DIR=$PROJECT_MEMORY_DIR"
echo "RUN_DIR=$RUN_DIR"
echo "HANDOFF_PATH=$HANDOFF_PATH"
```

次に `RESUME_MODE` をスキル本体（メイン Claude）が判定する:

- `$ARGUMENTS` に `引継い` / `続き` / `resume` / `Resume` / `RESUME` / `handoff` / `Handoff` / `HANDOFF` / `carry on` のいずれかが含まれる → `RESUME_MODE=resume`
- 含まれず、かつ `$HANDOFF_PATH` のファイルが存在する → `RESUME_MODE=passive-notice`
- それ以外 → `RESUME_MODE=new`

`RESUME_MODE` に応じて以降の挙動を分岐させる（詳細プロトコル: `~/.claude/pir-handoff.md`）:

- `resume`: ステップ 2（ブレスト）をスキップし、planner への入力に `HANDOFF_PATH=$HANDOFF_PATH` を含めて「handoff.md の未チェック項目のみを planning 対象にせよ」と指示する。スキル本体は handoff.md を上書きしない
- `passive-notice`: 「💡 前回の handoff が残っています: `$HANDOFF_PATH`」とユーザーに表示し、通常の新規タスクフローで続行する（handoff.md は触らない）
- `new`: 通常の新規タスクフロー。planner の plan.md 完成直後にスキル本体が handoff.md 初期版を Write する（プランのステップを `[ ]` チェックリスト化）

retrospector フェーズ完了後、スキル本体は handoff.md を Read し、全項目が `[x]` なら削除、残項目ありなら「最終更新」タイムスタンプを更新する。

このステップで内部状態フラグ `PLAN_STRATEGY_CHANGED=false` を初期化してください。これはユーザー方針切替（ステップ 4.6 の「別案」選択など）による plan 再策定が発生した場合のみ `true` にセットされ、planner 側 3.3「v1 判断白紙化チェック」の発動条件として使われます。EXPLORATION_NEEDED ループ（ステップ 4.5）の追加探索による再策定では立てません。

以降の各サブエージェントへのプロンプトには必ず `PROJECT_MEMORY_DIR=[パス]` および `RUN_DIR=[パス]` を含めてください。

---

## ステップ 2: ブレインストーミング（状況に応じて実施）

タスクの仕様を評価し、以下のいずれかに該当する場合は brainstorm スキルを実行してから次のステップへ進んでください：

- 要件が曖昧で複数の解釈が可能
- アーキテクチャ上の選択肢が複数あり、どれを選ぶかユーザーに確認が必要
- ユーザーとの対話を通じて設計を固めたほうが手戻りリスクを減らせると判断される

実行方法: Skill ツールで `skill: "brainstorm"` を呼び出す。ユーザーとの対話で固まった設計はステップ4の planner に渡してください。

該当しない場合（タスクが明確、既存の設計がある、`docs/brainstorm/` に関連する設計ドキュメントが存在する）はスキップしてください。

> **brainstorm 完了後は必ず自動でステップ3へ進むこと**。「設計ドキュメントを保存しました」と単独ターンで区切ってユーザーの承認を待つのは禁止。`/pir2` は一度起動されたら最終サマリー（ステップ12）まで止まらず進める設計であり、brainstorm の最終出力「次のステップとして `/writing-plan` で実装プランを作成できます」は `/brainstorm` 単独起動時向けの案内なので、`/pir2` 経由では無視して続行する。承認を挟んでよいのは `~/.claude/skills/pir2/SKILL.md` 内で明示的にユーザー確認が指定されているポイント（既存パターン逸脱の事前申告・ステップ6.5 未解決事項確認）のみ。

---

## ステップ 3: 探索フェーズ（explorer）

コードベース探索はメイン Claude が **直接** Glob/Grep/Read で行ってはならない。必ず `explorer` エージェントを `Agent` ツールで起動し、調査を委譲してください。

### 起動ルール

- **最低1体起動**: タスクの規模にかかわらず初回探索は必須
- **最大3体並列**: 調査領域が独立している場合のみ並列起動
- **モデル使い分け**:
  - `haiku`: 広く浅い調査（ファイル構造、パターン列挙、grep 結果の収集）。最大3体並列可
  - `sonnet`: 深く読み解く調査（既存ロジックの意味理解、設計意図の把握）。最大1体
  - `opus`: sonnet でも読み解けなかった場合のフォールバック（高度な間接参照、メタプログラミング、複雑な状態遷移）。最大1体、他層と並列起動しない
- **ミックス起動可**: 広さと深さを同時に欲しい場合は haiku と sonnet を同ターンで並列起動してよい。opus は単独起動とする
- **opus 発動条件**: sonnet の探索レポートで「既存ロジックの意図を推測で補っている」「複数回の間接参照で追跡が途中で途切れている」「メタプログラミング/DSL により表層の grep では意味が取れない」と判断した場合のみ。常用しない

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

### 既存 agent を探索フェーズに流用する場合のロール境界再注入

PIR² 起動前の会話で稼働していた agent を `SendMessage` で探索フェーズに流用する場合、`Agent` ツールでの新規起動と違い `explorer.md` のシステムプロンプト（実装・git 操作の禁止条項）が再注入されない。流用するときは `SendMessage` 本文の冒頭に必ず次を明記すること:

> 「これより explorer ロールに切り替わります。責務は調査と `{RUN_DIR}/exploration-{INDEX}.md` への探索レポート作成のみ。コードの実装、`git add` / `git commit` / `git reset` / `git checkout` / `git restore` / `git stash` 等のリポジトリ状態を変更する操作は一切禁止。実装が必要だと判明したら探索レポートの『呼び出し元への依頼』セクションに回すこと。」

会話で実装文脈を濃く持っている agent は流用するとロール境界が曖昧になり実装に踏み込みやすい。その場合は流用せず `Agent` ツールで新規 explorer を起動する方を優先する。

### ライブラリ選定が必要な場合

新しいライブラリ・フレームワークの導入判断が必要なら `tech-validator` エージェントを起動する（既存の依存関係で解決できる場合はスキップ）。

---

## ステップ 4: プラン策定（planner）

`planner` エージェントを `Agent` ツールで起動し、タスク内容と探索レポート全文を渡してください。

- model: `opus`
- プロンプト:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `PLAN_STRATEGY_CHANGED=$PLAN_STRATEGY_CHANGED`（現在の値。初回起動時は `false`、ステップ 4.6 で「別案」が選ばれた直後の再起動時のみ `true`）
  - タスク内容
  - `{RUN_DIR}/exploration-*.md` のパス一覧（planner は本文を自分で Read する）
  - ブレインストーミング結果（ステップ2で実施した場合）
  - 「完全に独立した実装 shard がある場合のみ `IMPLEMENTATION_SHARDS` を提案してください（試験実装。判定基準は `~/.claude/skills/pir2/references/implementation-delegation.md` に従い、少しでも分離が曖昧なら提案しないこと）」
  - 「大きいが結合していて並列分割できない実装は `IMPLEMENTATION_UNITS`（順序付きの直列 unit）を提案してください（試験実装。`IMPLEMENTATION_SHARDS` と排他。各 unit は fresh な implementer で直列実装される）」
  - 「プランレポート本体は `{RUN_DIR}/plan.md` に書き出し、チャットには要約＋EXPLORATION_NEEDED の有無のみ返してください」

planner からプラン要約を受け取ってください。

### 既存パターン逸脱の事前申告

planner から「既存構造と異なる構成を採用する」判断が含まれたプランが返ってきた場合、実装着手前にユーザーに差分（既存 N 件中 M 件の構成 / 今回採用しようとしている構成 / 逸脱理由 / 代替案）を提示し、承認を得ること。承認なしに次のステップに進んではならない。

---

## ステップ 4.5: 能動的再探索ループ（最大5回）

詳細プロトコル: `~/.claude/skills/pir2/references/exploration-loop.md` を参照（収束判定ロジック / ループ本体 / 既存パターン逸脱の事前申告タイミング）。

要点: planner の返り値要約に `### EXPLORATION_NEEDED` の `- topic` が残る間、追加探索 → planner 再起動を最大 5 回繰り返す。収束したらステップ 5 へ進む。`REPLAN_COUNT = 0` から開始し、ハードキャップ到達時は最終サマリー（ステップ12）に「**planner が依然追加探索を要求中（ハードキャップ5回到達）**: [topic 一覧]」と明記する。

---

## ステップ 4.6: プラン選択肢のユーザー確認（該当時のみ・Auto mode でも例外なし）

詳細プロトコル: `~/.claude/skills/pir2/references/plan-choice-gate.md` を参照（検出トリガー / 確認フォーマット / 運用ルール / 別案の字義解釈確認 / v2→v3 切替の真意確認）。

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

詳細プロトコル: `~/.claude/skills/pir2/references/next-steps-queue.md` を参照（初期 Write テンプレート / 5.6-2 checkbox 更新手順 / 5.6-3 中断後の Read ルール / スキップ条件）。

要点: `{RUN_DIR}/next-steps.md` にサブエージェント起動予定 checkbox リストを Write する。**ユーザー会話による中断後、スキル本体は次の判断前に必ずこのファイルを Read してから動く**。各ステップ完了直後に checkbox を `[x]` + `<!-- done: ISO8601 -->` に更新する（必須運用）。`RESUME_MODE=resume` の場合は handoff.md 由来の未完了項目を統合する。

---

## ステップ 5.7: 破壊的変更チェックリスト + 動作変更チェック（implementer 起動前に必ず実行）

詳細プロトコル: `~/.claude/skills/pir2/references/destructive-change-check.md` を参照（pir2 専用の 2 軸マトリクス判定 / 判定項目 a〜e・f1〜f3 / 書き出しフォーマット / 軽量化確認 / スキップ条件）。

要点: plan.md と explorer レポートを Read して「破壊的変更フラグ（a〜e）」と「動作変更フラグ（f1〜f3）」を独立に判定。結果を `{RUN_DIR}/destructive-change-check.md` に書き出し、後段（reviewer / refactor-advisor / tester）の戦略をマトリクスで決定。フラグ ON で軽量化したい場合はユーザー確認必須。完了後は 5.6-2 に従い next-steps.md の checkbox を更新する。

---

## ステップ 5.8: 直前追加 feedback の自己照合ゲート（implementer 起動前に必ず実行）

詳細プロトコル: `~/.claude/skills/pir2/references/feedback-conflict-gate.md` を参照（feedback Read → プロンプト照合 → 矛盾検出時の中断フォーマット → 記録 → スキップ条件）。

要点: 過去 14 日以内の feedback_*.md 5 件を Read し、implementer プロンプト案の除外指示・スコープ縮小と突合。矛盾 1 件でも検出したら起動中断 → ユーザー確認。矛盾なしも `{RUN_DIR}/feedback-conflict.md` に「照合 N 件、矛盾なし」を記録。完了後は 5.6-2 に従い next-steps.md の checkbox を更新する。

---

## ステップ 6: 実装（implementer）

`INNER_LOOP_COUNT = 0`、`OUTER_LOOP_COUNT = 0`、`PHANTOM_RETRY_COUNT = 0` から開始してください。

### 6-0: 実装 actor の決定

詳細プロトコル: `~/.claude/skills/pir2/references/implementation-delegation.md` を参照（単一 implementer / 複数 implementer shard / main fallback の判定、shard 許可条件・禁止パターン、プロンプト共通項目、shard 統合確認、再実装ルール）。

要点: デフォルトは `IMPLEMENTATION_ACTOR=implementer-subagent`（単一 implementer 1 体）。planner が `{RUN_DIR}/plan.md` に `IMPLEMENTATION_SHARDS` を提示し、かつ delegation.md の許可条件（shard 同士のファイル所有範囲・依存順序・共有生成物が完全に分離）をスキル本体（メイン Claude）が全て確認できた場合のみ `IMPLEMENTATION_ACTOR=implementer-shards` として最大 3 体まで並列実装してよい。planner が `IMPLEMENTATION_UNITS` を提示し（大きいが結合していて並列 shard にできない実装）、delegation.md の unit 許可条件をスキル本体が全て確認できた場合は `IMPLEMENTATION_ACTOR=implementer-sequential` として、unit を fresh な implementer で `UNIT_ID` 昇順に直列実装してよい。いずれも 1 つでも条件が欠けたら `implementer-subagent` に戻す。subagent 不可・小変更・plan 未成熟の場合のみ `IMPLEMENTATION_ACTOR=main` に縮退する。

> **試験実装の注記**: `implementer-shards` / `review-fix shard` は試験実装であり、`~/.claude/skills/pir2/references/experimental.md` の `pir2-implementer-shards-and-review-fix-shards` を採用可否判断の SSOT として retrospector が毎サイクル観測する。`implementer-sequential` も試験実装で、SSOT は同ファイルの `pir2-implementer-sequential-units`。判定が曖昧なら常に保守的に `implementer-subagent` を選ぶこと。

### 6-1: implementer 起動

#### implementer 起動前の pre-set 記録（決定論的完了検証 6-3 用・必須）

`IMPLEMENTATION_ACTOR` が `main` 以外のとき、implementer を起動する **前** に、決定論的完了検証（共通プロトコル `~/.claude/skills/pir2/references/deterministic-completion-check.md`「pre-set 記録」）の基準スナップショットとして作業ツリーの dirty 集合を記録する。`main` 実装時は 6-3 自体を適用しないため記録も不要。shard/sequential 時も pre-set はこの1回（並列/直列起動の直前）のみ記録する。

`implementer` エージェントを `Agent` ツールで起動し、プラン全文を渡してください（`implementer-shards` 時は delegation.md の許可条件を満たした各 shard を **同一メッセージ内で並列起動**、`implementer-sequential` 時は `IMPLEMENTATION_UNITS` の各 unit を `UNIT_ID` 昇順に **1 体ずつ直列起動**＝先行 unit の完了を待って次を起動し各 unit に先行 unit の `implementation-*.md` パスと `git diff` 確認指示を渡す（delegation.md「直列実行プロトコル」）、`main` 時はスキル本体が直接実装）。

- model: `sonnet`
- プロンプト（共通項目の全量は delegation.md「implementer プロンプト共通項目」を参照）:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `IMPL_INDEX=01`（初回。再実装時は呼び出し元がインクリメント）
  - `IMPLEMENTATION_ACTOR`（`implementer-subagent` / `implementer-shards` / `implementer-sequential` / `main`）
  - shard 実行時のみ `SHARD_ID` と許可/禁止ファイル一覧
  - sequential unit 実行時のみ `UNIT_ID`・当該 unit の spec・完了済み unit の `{RUN_DIR}/implementation-{IMPL_INDEX}-unit-*.md` パス一覧・「起動後 `git diff` で先行 unit を確認し命名/抽象に従う」指示
  - `{RUN_DIR}/plan.md` のパス（implementer が Read する）
  - （`RESUME_MODE` が `new` または `resume` の場合のみ）`HANDOFF_PATH=$HANDOFF_PATH` と「実装完了した項目を handoff.md で `[x]` 化し、新規発見の TODO は追記すること。詳細: `~/.claude/pir-handoff.md`」
  - 「実装完了レポート本体は `{RUN_DIR}/implementation-{IMPL_INDEX}.md`、shard 実行時は `{RUN_DIR}/implementation-{IMPL_INDEX}-{SHARD_ID}.md`、sequential unit 実行時は `{RUN_DIR}/implementation-{IMPL_INDEX}-unit-{UNIT_ID}.md` に書き出し、チャットには要約のみ返してください」
  - **役割境界の厳守（必須明示）**: 「プランに `go test` / `pytest` / `npm test` / `jest` / `rspec` など**テストスイート実行のステップ**が書かれていても、それは tester 専任のため **implementer は実行しないこと**（planner の誤記として扱い、実装完了レポートの『注意点・未解決事項』にスキップした旨を記録する）。実行してよいのは静的検証（lint / 型チェック）・ビルド・コード生成（`make codegen` など）・diff 確認まで。`make golden` もテスト実行を伴うため実行せず、golden の実生成は tester に委ねる」

### 6-2: 統合確認（`implementer-shards` / `implementer-sequential` 時）

`implementer-shards` 時: 全 shard 完了後、スキル本体（メイン Claude）は delegation.md「shard 統合確認」に従い、全 `implementation-{IMPL_INDEX}-*.md` を Read し、`git diff` で shard 外編集・同一ファイル競合・命名不整合・未接続実装がないか確認する。問題があれば `IMPLEMENTATION_ACTOR=implementer-subagent` に戻して統合修正する。

`implementer-sequential` 時: 全 unit 完了後、delegation.md「unit 統合確認」に従い、全 `implementation-{IMPL_INDEX}-unit-*.md` を Read し、`git diff` で unit 境界をまたぐ命名不整合・重複抽象・未接続実装がないか確認する。問題があれば `IMPLEMENTATION_ACTOR=implementer-subagent` に戻して統合修正する。

implementer から実装要約を受け取ってください。

### 6-3: 決定論的完了検証（`IMPLEMENTATION_ACTOR` が `main` 以外のとき必須）

詳細プロトコル: `~/.claude/skills/pir2/references/deterministic-completion-check.md` を参照（適用対象 actor / pre-set・post-set 記録 bash / 集合照合規則 PHANTOM_CLAIM・UNDECLARED_CHANGE・NO_OP 免除 / 判定結果書き出し / 失敗パスのユーザーゲート）。本 reference は pir2 6-3 と pir2codex 6-1 の共通プロトコル。

要点: implementer 完了報告（および 6-2 統合確認）の直後、reviewer 起動（ステップ7）より前に、`implementation-{IMPL_INDEX}*.md` の `### 変更ファイル一覧` から抽出した申告集合 CLAIMED と、6-1 で記録した pre-set からの git delta を純 bash で集合照合する。**PHANTOM_CLAIM（申告したが実際は dirty でないファイルがある／編集想定タスクなのに申告も変更も空で `NO_OP_JUSTIFIED` 宣言なし）は hard fail**。検出時は検証レポート `{RUN_DIR}/verify-{IMPL_INDEX}.md` を逐語注入して implementer を **1 回だけ**再実行（`IMPL_INDEX` と `PHANTOM_RETRY_COUNT` をインクリメント）し再検証する。**2 回目も PHANTOM なら reviewer を起動せずユーザーゲート**（捏造の上にレビューを積まない）。UNDECLARED_CHANGE（申告外の dirty。formatter/生成物副作用等）は warn として `{RUN_DIR}/verify-{IMPL_INDEX}.md` に記録し報告に含めるが**非ブロッキング**。`IMPLEMENTATION_ACTOR=main` は自己申告境界が存在しないため本ステップをスキップする。

> ℹ️ 6-3 は resume 時の追跡粒度を上げるため next-steps.md 上で「ステップ6」とは独立した checkbox を持つ（既存の「hyphen 番号は親ステップと checkbox を共有する」という慣習からの意図的な例外）。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox（「ステップ6」「ステップ6-3」双方）を `[x]` に更新する（`IMPL_INDEX` が複数回ループする場合は最初の 1 回のみマーク。PHANTOM 再実行で `IMPL_INDEX` が増えた場合も同様。2 回目以降のループは「中断・再開ログ」セクションに追記する）。`main` で 6-3 をスキップした場合は「ステップ6-3」チェックボックスを「main のためスキップ」と付記して `[x]` にする。

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

### 7-2A: 起動宣言（Fan-Out Gate — 並列発火の直前に必ず書く）

reviewer 並列起動メッセージを送信する **直前のターン本文中** に、以下のテンプレートを必ず生成すること。このテンプレートが本文に出現していないターンで Agent 起動を発火させた場合は、ステップ完了判定を取り消して 7-2A からやり直す。

> **Fan-Out Gate（reviewer）**
> - REVIEWER_SET = [<観点をカンマ区切りで全列挙>]
> - 起動体数 = <N>（= len(REVIEWER_SET)、必ず一致）
> - 同一 function_calls ブロックに <N> 個の Agent 起動を並べる
> - 1 体ずつ起動・後追い起動・観点削減はいずれも違反

このブロックは「起動直前の自己コミットメント」であり、ユーザーへの報告ではなく自分の手癖（1 体ずつ逐次起動する癖）を止めるためのフェンスとして機能する。再レビュー時（7-4 からの差し戻し時）にも毎回この宣言を書くこと。REVIEWER_SET は初回選定を維持し、再レビュー時に観点を勝手に減らさないこと。

### 7-2B: 並列発火（同一メッセージ内）

直前ターンで宣言した REVIEWER_SET の各観点について、同一の `<function_calls>` ブロック内に Agent ツール呼び出しを **N 個** 並べて 1 メッセージで同時送信する。各体は `REVIEWER_ROLE` を変えて担当観点を分割する。

詳細仕様（観点マッピング / 違反パターンと検出 / 違反検出時のリカバリ / reviewer 起動パラメータ）: `~/.claude/skills/pir2/references/fan-out-gate.md` を参照。

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
  3. 実装修正を行う（`IMPL_INDEX` をインクリメント、**FAIL を返した全 reviewer の `{RUN_DIR}/review-{最新}-{ROLE}.md` パスを全て渡す**、`{RUN_DIR}/plan.md` のパスも渡す。マージ要約は作らず、各レポートを直接 Read させる）。reviewer 指摘がファイル単位で分離できる場合は `~/.claude/skills/pir2/references/implementation-delegation.md` の review-fix shard ルールに従い、最大 5 体まで implementer を並列起動して修正してよい（試験実装。分離が曖昧なら単一 `implementer` に戻す）。分離できない場合は単一 `implementer` を再起動する。**review-fix shard を使った場合は、全 shard 完了後に 6-2 と同じ統合確認（全 `{RUN_DIR}/implementation-{最新}-fix-*.md` を Read し、`git diff` で shard 外編集・同一ファイル競合・命名不整合・未接続実装がないか確認。問題があれば単一 `implementer` に戻して統合修正）を済ませてから次の再 reviewer へ進む**
  4. **7-2A（Fan-Out Gate 宣言）→ 7-2B（並列発火）の手順で** reviewer を **同じ REVIEWER_SET で** 並列で再起動（`REVIEW_INDEX` をインクリメント、最新の `{RUN_DIR}/implementation-{最新}.md` のパスを渡す。PASS を返した観点も再レビューする = 修正による新たな退行を検知するため。観点集合は初回選定を維持し途中で追加・削除しない。**再レビュー時も Fan-Out Gate を省略しないこと**）
  5. 全体 PASS になるまで繰り返す

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する（複数回ループで `REVIEW_INDEX` が増えた場合は最初の 1 回のみマーク、ループ詳細は「中断・再開ログ」に追記）。

---

## ステップ 7.5: リファクタ提案（refactor-advisor 起動 → ゲート → 任意適用）

全体 VERDICT が PASS の場合のみ実行。FAIL で INNER_LOOP_COUNT 上限到達の場合はスキップしてステップ 8 へ。

詳細プロトコル: `~/.claude/skills/pir2/references/refactor-advisor-gate.md` を参照（refactor-advisor 起動仕様 / 提案存在確認 / ユーザー提示フォーマット / ユーザー選択の処理 / リファクタ適用の implementer 再起動 / 退行検知の再 reviewer ループ）。

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

`tester` エージェントを `Agent` ツールで起動。起動仕様（model / プロンプトに含めるパラメータ一覧）は `~/.claude/skills/pir2/references/tester-prompt.md` を参照。`TEST_INDEX` は初回 `01`、再テスト時はインクリメント。

### 8-2: 判定

- `VERDICT: PASS` → ステップ 9 へ
- `VERDICT: FAIL` →
  1. `OUTER_LOOP_COUNT += 1`
  2. `OUTER_LOOP_COUNT >= 3` の場合は **続行可能ゲート（8-2-G）** へ。判定が「続行」なら 3. へ、「移行」ならステップ 9 へ（失敗として記録）
  3. `INNER_LOOP_COUNT = 0` にリセット
  4. `implementer` を再起動（`IMPL_INDEX` をインクリメント、`{RUN_DIR}/test-{最新}.md` のパスを tester 指摘事項として渡す）。tester FAIL は根本原因が共有契約・状態・実行順序にあることが多いため、原則 `IMPLEMENTATION_ACTOR=implementer-subagent`（単一）に戻す。例外条件は `~/.claude/skills/pir2/references/implementation-delegation.md`「tester FAIL 後」を参照
  5. **ステップ 7 に戻る**（レビューループを再実行、`REVIEW_INDEX` は継続インクリメント）
  6. tester を再起動（`TEST_INDEX` をインクリメント）
  7. PASS になるまで繰り返す

### 8-2-G: 続行可能ゲート（OUTER_LOOP_COUNT 上限到達時のみ）

詳細プロトコル: `~/.claude/skills/pir2/references/continuation-gate.md` を参照（4 条件の判定基準 / ユーザー確認フォーマット / 運用ルール）。1 条件でも欠けたらゲートを出さず無条件でステップ 9 へ移行する。ユーザーが N を選んだ場合もステップ 9 へ。**Auto mode でも本ゲートはユーザー応答を待つ**（仕様変更判断ゲートのため Auto mode 例外）。1 サイクル中に通過できるのは最大 1 回のみ（OUTER_LOOP_COUNT=4 で再 FAIL したら無条件にステップ 9 へ）。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する（複数回ループで `TEST_INDEX` が増えた場合も同様、最初の 1 回のみマーク）。

---

## ステップ 9: ウォークスルー生成（メイン Claude が直接）

変更されたファイルを Read して最終的な実装内容を確認し、ウォークスルーを作成する。フル版（内部記録）とサマリー版（最終サマリーに転記）の 2 形式を作成し、フル版は実装記録ドキュメント（ステップ 5 で作成）の「実装ログ」セクションに埋める。

詳細テンプレート（フル版・サマリー版・サマリー版の原則）: `~/.claude/skills/pir2/references/walkthrough-templates.md` を参照。

最重要原則: **推測でコードを書かない。実際に Read したコードのみ引用する**。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。

---

## ステップ 10: メモリへの記録

`PROJECT_MEMORY_DIR` 配下にタスクの振り返り材料を追記します:

- まず `mkdir -p {PROJECT_MEMORY_DIR}` でディレクトリを作成
- パス: `{PROJECT_MEMORY_DIR}/pir_skill_log.md`
- フォーマット: `## [タスク名] — [気づき・課題・パターン]`
- **モデルスイープ計装**（後日「どのフェーズを安価モデルに下げられるか」を判断する素材。機械集計しやすいよう固定プレフィックスで必ず1行記録する）:
  `- 使用モデル: explorer=<model×体数>, planner=<model>, implementer=<model>, reviewer=<model×体数>, tester=<model>, retrospector=<model> / REPLAN=<N> / INNER_LOOP=<N> / OUTER_LOOP=<N>`
  今回 run で各エージェントを**実際に起動したモデル**を埋める（explorer は haiku/sonnet/opus の使い分け結果、retrospector は opus/sonnet 切替結果を反映）。スイープ実験本体は計装でデータが溜まってから別途行う。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。

---

## ステップ 11: 振り返り（retrospector、常に実行）

`retrospector` エージェントを `Agent` ツールで起動。起動仕様（model 切替条件 / プロンプトに含めるパラメータ一覧 / 起動後の処理）は `~/.claude/skills/pir2/references/retrospector-prompt.md` を参照。`/pir2` では `ワークフロー種別: pir2` を明示し、`PLAN_STRATEGY_CHANGED` の現在値も渡すこと（true なら今回 run でユーザー方針切替が発生し planner v1→v2 再策定が走った）。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。

---

## ステップ 11.5: handoff.md 完了判定と後処理

詳細プロトコル: `~/.claude/skills/pir2/references/handoff-cleanup.md` を参照。要点: `$HANDOFF_PATH` が存在する場合、全 `[x]` なら削除、残項目ありなら `最終更新` 行を更新する。最終サマリーに結果を記載すること。`$HANDOFF_PATH` が存在しない場合はスキップ。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。全 checkbox が `[x]` になった場合は最終サマリー（ステップ 12）に「next-steps.md: 全項目完了」と記載する。

---

## ステップ 12: 最終サマリーの提示

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

### 決定論的完了検証（6-3）
- PHANTOM_CLAIM: [検出なし / 検出→再実行1回で解消 / 検出→再失敗でユーザーエスカレーション / main のためスキップ]
- UNDECLARED_CHANGE: [なし / N 件（非ブロッキング・{RUN_DIR}/verify-*.md に記録）]
- PHANTOM_RETRY_COUNT: [回数]

### リファクタ提案（refactor-advisor）
- 提案件数: [N]件（Medium: X / Low: Y）
- 適用件数: [M]件
- 未適用件数: [N-M]件
- 未適用の内訳: [ユーザーが none を選択 / 番号指定から漏れた候補 等]

### テスト結果
- テスト VERDICT: [PASS/FAIL]
- 外側ループ回数: [OUTER_LOOP_COUNT]

### 再探索ループ回数
- REPLAN_COUNT: [回数]
- [ハードキャップ到達時のみ]: planner が依然追加探索を要求中: [topic 一覧]

### 作業ディレクトリ
{RUN_DIR}

### 振り返り
[retrospector の改善内容の要約]

### メタ改善推奨（retrospector レポートに含まれていた場合のみ）
[内容を転記し、`/retro --meta` の実行をユーザー判断に委ねる旨を添える]
```

---

## ステップ 13: ウォークスルーの提示

ステップ9で作成したサマリー版ウォークスルーをユーザーに提示してください。フル版は内部記録として保持し、ユーザーから「詳細を見せて」等の要求があれば提示します。

末尾に `詳細なウォークスルーが必要な場合はお知らせください。` と添えてください。
