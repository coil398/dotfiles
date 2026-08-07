---
name: "writing-plan"
description: "実装計画を作成し、各ステップ完了後にドキュメントへ追記して最終的に実装記録として残す。PIR²のP+Iフェーズとしても単独でも使う。「計画を立てて」「ステップバイステップで進めて」「段階的に実装して」「実装記録を残したい」といった要望にも対応する。ユーザーが /writing-plan と入力したら必ずこのスキルを使う。"
argument-hint: "[タスクの説明]"
---

# ライティングプラン — 計画 → 実装追記 → ドキュメント化

**タスク**: $ARGUMENTS

実装計画を作成し、各ステップの完了後にドキュメントへ追記します。Sol orchestrator は計画と各ステップの所有範囲・requirementsを確定しますが、対象リポジトリを実装・修正せず、具体実装は共通の [worker-delegation 契約](../worker-delegation/SKILL.md) に委譲します。reviewer は correctness / consistency / quality / security / architecture の 5 観点から **REVIEWER_SET に含まれる観点のみ並列起動** します（planner 系スキルなのでデフォルトは全 5 観点固定。`--reviewers=<roles>` / `--all-reviewers` フラグで上書き可能）。reviewer / tester の品質・動作判定はworkerとは別系統です。
最終的にこのドキュメントは「実装記録」として機能します（確認後に削除する想定）。

---

## ステップ 0: プロジェクトメモリパスと RUN_DIR の確定

以下の Bash コマンドで `PROJECT_ROOT` / `PROJECT_MEMORY_DIR` / `RUN_DIR` を確定し、以降のすべてのステップで使用してください:

```bash
PROJECT_ROOT="$(pwd)"
# sanitized-cwd 計算は ${PROJECT_ROOT}/.codex/skills/pir2/references/sanitized-cwd.md を SSOT とする
# （Codex harness の sanitize 仕様変更時はこの SSOT のみを更新し、9 ファイルに横展開）
sanitized_cwd="$(pwd | sed 's|[^a-zA-Z0-9]|-|g')"
PROJECT_MEMORY_DIR="${HOME}/.codex/projects/${sanitized_cwd}/memory"
run_ts="$(date +%Y%m%d-%H%M%S)"
run_feature="$(printf '%s' "$ARGUMENTS" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
[ -z "$run_feature" ] && run_feature="task"
RUN_DIR="${HOME}/.ai-pir-runs/${sanitized_cwd}/${run_ts}-${run_feature}"
mkdir -p "$RUN_DIR"
echo "PROJECT_ROOT=$PROJECT_ROOT"
echo "PROJECT_MEMORY_DIR=$PROJECT_MEMORY_DIR"
echo "RUN_DIR=$RUN_DIR"
```

`/writing-plan` は handoff 連携を行わないため、`HANDOFF_PATH` / `RESUME_MODE` は不要です。

### 共通 observability（Phase 0 では初期化だけ）

Phase 0 では `${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/record-observation.sh` を `OBS_HELPER` に束縛し、台帳の `init` だけを worker 起動前に一度実行する。worker / acceptance / verdict の値はこの段階では未確定なので、ここで append してはいけない。具体的な CLI と固定 TSV header は `pir2/references/worker-observability.md` を SSOT とする。

```sh
OBS_HELPER="${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/record-observation.sh"
"$OBS_HELPER" init --run-dir "$RUN_DIR"
```

---

## ステップ 1: 実装計画の作成

Sol orchestrator が `planner` role を `spawn_agent`（`agent_type="planner"`）で起動してください。モデル引数は指定せず、`.codex/agents/planner.toml` の role 定義に委ねます。

- プロンプト:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - タスク内容（$ARGUMENTS）
  - タスクを独立した bite-sized なステップに分解し、各ステップの完了基準を明確にした計画を作成するよう指示する
  - 「プラン本体は `{RUN_DIR}/plan.md` に書き出し、チャットには要約のみ返してください」

プラン要約を受け取ったら次のステップへ進んでください。

---

## ステップ 2: ドキュメントの初期化

`docs/plans/` ディレクトリがなければ作成してください。

以下の形式でドキュメントを作成してください。
ブレインストーム設計ドキュメント（`docs/brainstorm/` 配下）が存在する場合は参照先として記載してください。

**保存先**: `docs/plans/YYYY-MM-DD-<feature>.md`（YYYY-MM-DD は今日の日付）

ファイルを保存したら、**すぐに**以下の形式でパスをユーザーに提示してください：

```
プラン: docs/plans/YYYY-MM-DD-<feature>.md
```

```markdown
# [タスク名] 実装記録

_作成: YYYY-MM-DD | ステータス: 進行中_

## 目標

[タスクの概要]

## 実装計画

- [ ] ステップ 1: [ステップ名]
- [ ] ステップ 2: [ステップ名]
- [ ] ステップ 3: [ステップ名]

---

## 設計詳細

[`{RUN_DIR}/plan.md` を Read して詳細プランをそのまま転記（対象ファイル・変更内容・理由・検証方法・影響範囲）]

---

## 実装ログ

<!-- 各ステップ完了時に追記される -->
```

---

## ステップ 3: 実装と追記のループ

計画の各ステップについて順番に以下を繰り返してください。`IMPL_INDEX` と `REVIEW_INDEX` は全体を通じて連続してインクリメントします（計画ステップをまたいで継続）。初期値は `IMPL_INDEX=00`・`REVIEW_INDEX=00`。

### 3-1. 実装 (worker-delegation)

`IMPL_INDEX += 1`（2桁ゼロ埋め）してから、具体実装は `.codex/skills/worker-delegation/SKILL.md` に従って委譲する。Sol orchestrator は該当ステップだけを対象に、対象ファイル・変更内容・禁止事項を `task.md` に、ファイル・差分・検証コマンドで判定できる `R1` から始まる requirements を `requirements.md` に作成し、対象リポジトリを実装・修正しない。

Sol orchestrator は `mktemp -d` に一時入力を用意し、既定 actor の Luna Max worker を次で起動する。worker raw output と Sol canonical report は別 artifact とし、各計画ステップ・correction・shard/unit で固有 suffix の未作成パスを割り当てる。

```sh
WORKER_RUN_DIR="$(mktemp -d)"
TASK_FILE="$WORKER_RUN_DIR/task.md"
REQUIREMENTS_FILE="$WORKER_RUN_DIR/requirements.md"
PRE_IMPL_INDEX="$IMPL_INDEX"
REPORT_SUFFIX="$IMPL_INDEX"
WORKER_RAW_OUTPUT="$RUN_DIR/worker-output-$REPORT_SUFFIX.md"
IMPLEMENTATION_REPORT_PATH="$RUN_DIR/implementation-$REPORT_SUFFIX.md"
# Solが現在の計画ステップを TASK_FILE に、ステップ固有の R1...Rn を REQUIREMENTS_FILE に Write する
.codex/skills/worker-delegation/scripts/run-worker.sh \
  --actor luna --effort max \
  --cwd "$PROJECT_ROOT" \
  --task-file "$TASK_FILE" \
  --requirements-file "$REQUIREMENTS_FILE" \
  --output-file "$WORKER_RAW_OUTPUT"
```

worker 完了直後、Sol は `$WORKER_RAW_OUTPUT` を Read して canonical 8 fields
（`ACTOR`、`ACTUAL_MODEL`、`ACTUAL_EFFORT`、`STATUS`、`CHANGED_FILES`、
`OBSERVED_RESULTS`、`BLOCKERS`、`ESCALATION_REASON`）を確認します。raw の変更申告を
そのまま rename/copy せず、Sol が `git status -sb`、対象 diff、実在ファイル、各要件の
検証コマンド出力を独立に実測して `$IMPLEMENTATION_REPORT_PATH` へ canonical metadata、
正確な `### 変更ファイル一覧`（backtick path の箇条書き）、`### 注意点・未解決事項` を
Write します。deterministic gate の CLAIMED と reviewer/tester の入力は canonical
report のみであり、raw 単独を source にしません。順序は raw → Sol normalization →
deterministic post/CLAIMED → acceptance → reviewer → tester です。

Lunaの完了報告やrunnerの終了だけをacceptanceとみなさず、Sol orchestrator が `git status -sb`、対象差分、変更ファイル、requirementsごとの検証コマンド出力を実測します。Lunaの判断不足・requirements failure・権限不足・CLI error・入力不足・環境 failureは自動的に別 actor へ進まず、Sol orchestrator が不足を解消して再計画します。taskとrequirementsが十分で、Lunaの capability または local-reasoning insufficiency を実測できた場合だけ、理由・差分・昇格時点を記録し、`--actor terra --effort high` を明示して同じ要件のTerra Highを起動します。Terra Highを同じ原因でMaxにするのは、multi-stage causality、design contradiction、cross-module invariants、security/data-integrity risk、または documented High insufficiency の証拠がある場合に一度だけ許可します。Terraの capability/local-reasoning insufficiencyを測定した場合だけ、Sol worker subagentを `--actor sol --effort high` で明示起動します。Sol Highを同じ原因でMaxにするのは、highest-complexity/high-risk evidence または documented Sol High insufficiency がある場合に一度だけ許可します。全 attempt は `automatic_fallback=no` として記録し、全段を必ず実行することはありません。

#### 3-1A. 決定論的完了ゲート（全 worker job / correction）

各計画ステップの worker と reviewer/tester FAIL 後の correction は、起動直前に `IMPL_INDEX` / `PRE_IMPL_INDEX` を固定して `REPORT_SUFFIX` を決め、`WORKER_RAW_OUTPUT` と `IMPLEMENTATION_REPORT_PATH` を新しいパスへ更新してから pre-set を記録します。worker report 直後（Sol acceptance、reviewer、tester の前）に、Sol normalization 済み canonical reportだけを入力として共通 SSOT `${PROJECT_ROOT}/.codex/skills/worker-delegation/references/deterministic-completion-check.md` の post-set / delta / CLAIMED 手順を実行します。`shard` は `${IMPL_INDEX}-shard-${SHARD_ID}`、review-fix shard は `${IMPL_INDEX}-review-fix-${REVIEW_FIX_SHARD_ID}`、unit は `${IMPL_INDEX}-unit-${UNIT_ID}` の suffix を raw/canonical で一致させ、CLAIMED は canonical 全件の union のみとします。`bash "${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/verify-deterministic-check.sh"` で8 fixtureを検証し、canonical report と `${RUN_DIR}/verify-${IMPL_INDEX}.md` を保存します。共通 protocol本文は複製せず、writing-plan固有の `IMPL_INDEX` / `REVIEW_INDEX` / `TEST_INDEX` を記録します。

`PHANTOM_CLAIM` は hard fail です。Sol acceptance、reviewer、testerへ進まず、原因と verifier path を含む correction task/requirements を同じ Luna-first actor ladder に戻します。上限到達時は overall FAIL の hard stop としてユーザー判断を待ちます。`UNDECLARED_CHANGE` は warn として実差分を Sol が確認します。PASS時だけ pre/post/delta/verifier path を acceptance evidence と reviewer/tester 起動記録に残します。

### 3-1A. observability の実イベント（各計画ステップ / correction / shard / unit）

各 worker job の raw → canonical → deterministic gate の後、Sol が acceptance または blocker と
各 `Rn` の測定を確定した直後に、job 固有の実測値で `worker` を一度だけ append します。Phase 0
では未確定値を束縛せず、計画ステップ・correction・shard/unit ごとに新しい `JOB_ID`、index、
raw/provenance、canonical artifact を使います。

```sh
JOB_ID="writing-plan-${REPORT_SUFFIX}"
WORKER_STATUS="$SOL_MEASURED_WORKER_STATUS"
SOL_MEASUREMENT_RESULT="$SOL_MEASURED_RESULT"
MISMATCH_RESULT="$SOL_MEASURED_MISMATCH"
MISMATCH_REASON="$SOL_MEASURED_MISMATCH_REASON"
ESCALATION_FROM="$SOL_ESCALATION_FROM"; ESCALATION_TO="$SOL_ESCALATION_TO"; ESCALATION_REASON="$SOL_ESCALATION_REASON"
EFFORT_ESCALATION_FROM="$SOL_EFFORT_ESCALATION_FROM"; EFFORT_ESCALATION_TO="$SOL_EFFORT_ESCALATION_TO"
INSUFFICIENCY_CLASS="$SOL_INSUFFICIENCY_CLASS"; INPUT_SUFFICIENT="$SOL_INPUT_SUFFICIENT"; MEASURED_INSUFFICIENCY_REF="$SOL_MEASURED_INSUFFICIENCY_REF"
"$OBS_HELPER" worker \
  --run-dir "$RUN_DIR" --raw-output "$WORKER_RAW_OUTPUT" \
  --provenance "$WORKER_RAW_OUTPUT.provenance.tsv" \
  --job-id "$JOB_ID" --index "$REPORT_SUFFIX" --status "$WORKER_STATUS" \
  --sol-measurement-result "$SOL_MEASUREMENT_RESULT" --mismatch "$MISMATCH_RESULT" --mismatch-reason "$MISMATCH_REASON" \
  --escalation-from "$ESCALATION_FROM" --escalation-to "$ESCALATION_TO" \
  --effort-escalation-from "$EFFORT_ESCALATION_FROM" --effort-escalation-to "$EFFORT_ESCALATION_TO" --escalation-reason "$ESCALATION_REASON" \
  --insufficiency-class "$INSUFFICIENCY_CLASS" --input-sufficient "$INPUT_SUFFICIENT" --measured-insufficiency-ref "$MEASURED_INSUFFICIENCY_REF" \
  --task-ref "$TASK_FILE" --requirements-ref "$REQUIREMENTS_FILE" \
  --report-ref "$IMPLEMENTATION_REPORT_PATH" \
  --changed-files-ref "$CHANGED_FILES_REF" --verification-ref "$VERIFICATION_REF"
```

各 `Rn` の Sol 実測直後に acceptance 行を一行ずつ append し、reviewer report 完了直後は concrete
role と同じ cycle index、tester report 完了直後は `tester` role を渡します。generic `reviewer`
role の行は作りません。

```sh
for REQUIREMENT_ID in $REQUIREMENT_IDS; do
  ACCEPTANCE_VERDICT="$SOL_MEASURED_REQUIREMENT_VERDICT"
  ACCEPTANCE_REF="$RUN_DIR/sol-acceptance-${REPORT_SUFFIX}.md"
  EVIDENCE_SUMMARY="Sol measured ${REQUIREMENT_ID}"
  "$OBS_HELPER" acceptance \
    --run-dir "$RUN_DIR" --job-id "$JOB_ID" --index "$REPORT_SUFFIX" \
    --requirement-id "$REQUIREMENT_ID" --verdict "$ACCEPTANCE_VERDICT" \
    --evidence-ref "$ACCEPTANCE_REF" --evidence-summary "$EVIDENCE_SUMMARY"
done
for REVIEW_ROLE in $REVIEWER_SET; do
  REVIEW_VERDICT="$SOL_MEASURED_REVIEW_VERDICT"
  REVIEW_REPORT_PATH="$RUN_DIR/review-${REVIEW_INDEX}-${REVIEW_ROLE}.md"
  "$OBS_HELPER" verdict \
    --run-dir "$RUN_DIR" --job-id "$JOB_ID" --target-attempt-index "$REPORT_SUFFIX" --cycle "$REVIEW_INDEX" \
    --role "$REVIEW_ROLE" --verdict "$REVIEW_VERDICT" \
    --report-ref "$REVIEW_REPORT_PATH" --model "$REVIEW_ACTUAL_MODEL" --effort "$REVIEW_ACTUAL_EFFORT" --evidence-ref "$REVIEW_EVIDENCE_REF" --sol-acceptance-ref "$ACCEPTANCE_REF"
done
TEST_VERDICT="$SOL_MEASURED_TEST_VERDICT"
TEST_REPORT_PATH="$RUN_DIR/test-${TEST_INDEX}.md"
"$OBS_HELPER" verdict \
  --run-dir "$RUN_DIR" --job-id "$JOB_ID" --target-attempt-index "$REPORT_SUFFIX" --cycle "$TEST_INDEX" \
  --role tester --verdict "$TEST_VERDICT" --report-ref "$TEST_REPORT_PATH" --model "$TEST_ACTUAL_MODEL" --effort "$TEST_ACTUAL_EFFORT" --evidence-ref "$TEST_EVIDENCE_REF" \
  --sol-acceptance-ref "$ACCEPTANCE_REF"
```

### 3-2. ドキュメントへの追記

workerの完了報告を受け取ってもacceptanceとはみなさない。3-1A の deterministic gate が PASS し、Solがrequirementsを実測して受け入れた後に、ドキュメントを更新する：

1. 計画セクションの `[ ]` を `[x]` に変更
2. 実装ログセクションに追記（Sol が作成した canonical `${IMPLEMENTATION_REPORT_PATH}` を Read して詳細を転記。raw `${WORKER_RAW_OUTPUT}` は転記元にしない）：

```markdown
### ステップ N: [ステップ名]

- 変更ファイル: [一覧]
- 実装内容: [概要]
```

### 3-3. レビュー (Codex reviewer ハイブリッド並列)

初回ステップでのみ `REVIEWER_SET` を決定する（全計画ステップで同じ集合を使い回す。途中で追加・削除しない）:

1. **ユーザーフラグのパース**: `$ARGUMENTS` に `--reviewers=<roles>` が含まれていればカンマ区切りを観点集合として採用（未知 role は無視）。`--all-reviewers` があれば全 5 観点。両方指定時は `--reviewers=` を優先。フラグ抽出後の残りをタスク説明として扱う
2. **フラグ未指定時のデフォルト**: 全 5 観点 `[correctness, consistency, quality, security, architecture]`（planner 系スキル）
3. 決定した `REVIEWER_SET` をドキュメントのヘッダー部（「実装記録」）に記録

`REVIEW_INDEX += 1`（2桁ゼロ埋め）してから、以下の Fan-Out Gate 手順で reviewer を並列起動する。

#### 3-3A: 起動宣言（Fan-Out Gate — 並列発火の直前に必ず書く）

reviewer 並列起動メッセージを送信する **直前のターン本文中** に、以下のテンプレートを必ず生成すること。このテンプレートが本文に出現していないターンで `spawn_agent` を発火させた場合は、ステップ完了判定を取り消して 3-3A からやり直す。

> **Fan-Out Gate（reviewer）**
> - REVIEWER_SET = [<観点をカンマ区切りで全列挙>]
> - 起動体数 = <N>（= len(REVIEWER_SET)、必ず一致）
> - 同一 collaboration 呼び出しブロックに <N> 個の `spawn_agent` 起動を並べる
> - 1 体ずつ起動・後追い起動・観点削減はいずれも違反

このブロックは「起動直前の自己コミットメント」であり、自分の手癖（1 体ずつ逐次起動する癖）を止めるためのフェンスとして機能する。各計画ステップのレビュー時と、修正ループでの再レビュー時にも毎回この宣言を書くこと。

#### 3-3B: 並列発火（同一メッセージ内）

直前ターンで宣言した REVIEWER_SET の各観点について、同一の collaboration 呼び出しブロック内に `spawn_agent`（`agent_type="reviewer"`）を **N 個** 並べて 1 メッセージで同時送信する。各体は `REVIEWER_ROLE` を変えて担当観点を分割する。モデル引数は指定せず、`.codex/agents/reviewer.toml` の role 定義に委ねます。

詳細仕様（観点マッピング / 違反パターンと検出 / 違反検出時のリカバリ / reviewer 起動パラメータ）: `.codex/skills/pir2/references/fan-out-gate.md` を参照。

違反パターン（次のいずれかが発生したら違反として検出し 3-3A からやり直す）:
- collaboration 呼び出しブロックが 2 ターン以上に分かれる
- 並んだ `spawn_agent` 起動の数が宣言した N より少ない
- 観点を独自判断で減らした
- 直前ターンの宣言テンプレートが省略された

各体の起動パラメータ:

- プロンプト（共通。`REVIEWER_ROLE` のみ変える）:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `REVIEW_INDEX=[NN]`（起動する全体で同じ番号を共有する）
  - `REVIEWER_ROLE=[correctness|consistency|quality|security|architecture]`（体ごとに変える。REVIEWER_SET に含まれる観点のみ）
  - `{RUN_DIR}/plan.md` のパス
  - 最新 canonical `$IMPLEMENTATION_REPORT_PATH`（`implementation-{最新 IMPL_INDEX}.md`）のパス。raw `$WORKER_RAW_OUTPUT` は渡さない
  - 「レビューレポート本体は `{RUN_DIR}/review-{REVIEW_INDEX}-{REVIEWER_ROLE}.md` に書き出し、チャットには VERDICT + 要約のみ返してください」

### 3-4. VERDICT 集約とループ (最大2回)

- **全体 VERDICT = PASS**: `REVIEWER_SET` の every reviewer が `VERDICT: PASS`、未報告・判定不能・Critical / High の未解決がない → testerへ
- **全体 VERDICT = FAIL**: 1体でも non-PASS、未報告、判定不能、または未解決の Critical / High → 修正ループへ

**修正ループ**: 各計画ステップごとに `LOOP_COUNT = 0` で開始。

1. `LOOP_COUNT += 1`
2. `LOOP_COUNT >= 2` に達した場合は当該ステップを overall FAIL の hard stop として記録し、ユーザー判断を待つ。tester、次の計画ステップ、または成功完了へ進めない
3. Sol orchestrator がFAILを返した全 reviewer の `{RUN_DIR}/review-{最新}-{ROLE}.md` を読み、該当ステップのtaskとrequirementsを更新して、`worker-delegation` の actor ladder（Luna Max → measured Terra High → evidence-only Terra Max → measured Sol High worker → evidence-only Sol Max）で再実装する。各遷移は capability/local-reasoning evidence と `automatic_fallback=no` を記録し、`IMPL_INDEX` / `PRE_IMPL_INDEX` を更新して固有 suffix の `WORKER_RAW_OUTPUT` と `IMPLEMENTATION_REPORT_PATH` を再計算する。runner の `--output-file` は raw pathだけにし、完了後は Sol normalization → deterministic gate → acceptance の順に戻す。
4. **3-3A（Fan-Out Gate 宣言）→ 3-3B（並列発火）の手順で** `reviewer` を **同じ REVIEWER_SET で**並列で再起動して VERDICT を確認する（`REVIEW_INDEX` をインクリメント、最新の canonical `$IMPLEMENTATION_REPORT_PATH` のパスだけを渡す。PASS を返した観点も再レビューする。**再レビュー時も Fan-Out Gate を省略しないこと**）
5. 全体 FAIL なら繰り返す

### 3-5. tester（reviewer PASS 後に必須）

各計画ステップで reviewer gate の every reviewer が PASS になった後、別系統の `spawn_agent(agent_type="tester")` を必ず起動します。tester は `${PROJECT_ROOT}/.codex/agents/tester.toml` を使用し、`PROJECT_MEMORY_DIR`、`RUN_DIR`、`TEST_INDEX`（初回 `01`、再試行ごとに増分）、Sol が生成した canonical `$IMPLEMENTATION_REPORT_PATH`、対象ステップを渡し、`${RUN_DIR}/test-${TEST_INDEX}.md` に実際の検証結果を書きます。raw `$WORKER_RAW_OUTPUT` は tester/verdict/CLAIMED の入力にしません。documentation/config-only のステップでも適切な静的・構文・設定検証を tester が実行し、省略しません。worker report の自己申告は tester verdict ではありません。

- tester `VERDICT: PASS` のときだけ次の計画ステップまたは最終化へ進む
- tester `VERDICT: FAIL` のときは `OUTER_LOOP_COUNT += 1`。3回到達時は全体 FAIL の hard stop としてユーザー判断を待ち、成功扱いにしない
- 上限未到達なら tester report を根拠に correction task/requirements を作り、同じ Luna-first actor ladder で worker を起動する。worker report 直後に 3-1A の決定論的 gateを再実行し、PASS後に acceptance を記録する。その後、以前に PASS だった role を含む `REVIEWER_SET` の every reviewer を再実行し、全員 PASS の後に tester を `TEST_INDEX += 1` で再実行する

---

## ステップ 4: ドキュメントの最終化

すべてのステップが完了したら、ドキュメントのヘッダーを更新してください：

```markdown
_作成: YYYY-MM-DD | ステータス: **完了** YYYY-MM-DD_
```

末尾に総括セクションを追加してください：

```markdown
## 総括

- 完了ステップ数: N/N

> **このドキュメントは内容を確認後に削除してください。**
> `rm docs/plans/YYYY-MM-DD-<feature>.md`
```

複数セッションにまたがる大きな機能を実装している場合（= 今回のセッションで全ステップが完了していない場合）は、総括の代わりに以下の「次セッションへの引き継ぎ」セクションを追加し、ドキュメントは削除せず残してください。

```markdown
## 次セッションへの引き継ぎ

### 今セッションで完了したもの
- [変更・追加したファイル一覧]

### 意図的に今回スコープから外したもの
- [項目] — 理由: [なぜ今回やらないか]

### 次セッションで着手すべきタスク
- [タスク名] — 前提: [このタスクに取り掛かる前に確認すべきこと]

### 設計から変更した点
- [変更点] — 理由: [なぜ設計ドキュメントから逸脱したか]

### 詰まったポイント・迂回した仕様
- [詰まりの概要と暫定対応]
```

設計書（`docs/brainstorm/` 配下）は不変の全体像、実装プラン（`docs/plans/` 配下）はセッション単位の進捗、という役割分担を守ってください。次セッションはこの handoff セクションだけを読めば再開できる状態にすることが目的です。

---

## ステップ 5: 完了サマリーの提示

```
## ライティングプラン 完了

### タスク
[タスクの説明]

### 実装記録
docs/plans/YYYY-MM-DD-<feature>.md

### 完了ステップ
- [x] ステップ 1: ...
- [x] ステップ 2: ...

### レビュー集約
- REVIEWER_SET: [起動した観点のカンマ区切り、例: correctness,consistency,quality,security,architecture]
- 各ステップごとに REVIEWER_SET の観点で並列レビューを実施
- FAIL で上限 2 回の修正ループに到達したステップがあれば明記

> 内容を確認後、docs/plans/YYYY-MM-DD-<feature>.md を削除してください。
```
