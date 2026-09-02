---
name: "pir2async"
description: "PIR² の実験的な Codex collaboration workflow。spawn_agent / send_message / followup_task で探索・計画・レビューを連携し、具体的なファイル変更は worker-delegation に委譲する。通常の /pir2 との比較用。/pir2async と入力されたときだけ使う。"
argument-hint: "[タスクの説明] [--deepplan]"
---

# PIR² Async — experimental Codex collaboration workflow

pir2async は、通常の /pir2 と比較するための実験的な PIR² バリアントです。探索・計画・レビューの独立した役割を Codex の collaboration API で非同期に連携し、各役割のレポートを RUN_DIR に残します。実験結果は品質や完了の判定を代替しません。具体的な repository write は worker-delegation の Luna/Terra/Sol worker に限り、Sol orchestrator は実装・修正を行いません。

このスキルでは spawn_agent、send_message、followup_task を次の用途だけで使います。

- spawn_agent: 読み取り中心の explorer / planner / reviewer / tester / retrospector を起動する
- send_message: 起動済みの担当者へ、対象パス・追加の観点・レポートの保存先を伝える
- followup_task: 前の調査またはレビューに対する、範囲が明確な再調査・再確認を依頼する

コラボレーターをまとめるためのチーム状態、共有ワークスペース、入れ子の起動責任は仮定しません。現在の Codex runtime が上記呼び出しを提供しない場合は、スキル本体が読み取り役を実行するか、正確な blocker を報告してください。

## 境界

- 本スキルは明示的な実験用途に限定します。通常の実装には /pir2 を使います。
- target repository のファイルを変更する具体的な実装・修正は、必ず $PROJECT_ROOT/.codex/skills/worker-delegation/SKILL.md の契約と runner に委譲します。
- collaboration API の担当者は target repository を直接変更しません。レポート、計画、レビュー記録などの run artifact のみを書き出します。
- worker の自己申告、runner の終了コード、collaboration API の応答だけを acceptance や PASS の根拠にしません。最終判定はスキル本体が実際の diff と検証コマンドで行います。
- commit / push / destructive な git 操作は行いません。

タスク: $ARGUMENTS

---

## ステップ 1: 実行コンテキストの確定

以下を最初に実行し、以後の全レポートと依頼に同じ値を渡します。

```bash
PROJECT_ROOT="$(pwd)"
# sanitized-cwd 計算は ${PROJECT_ROOT}/.codex/skills/pir2/references/sanitized-cwd.md を SSOT とする
# （Codex harness の sanitize 仕様変更時はこの SSOT のみを更新し、9 ファイルに横展開）
sanitized_cwd="$(pwd | sed 's|[^a-zA-Z0-9]|-|g')"
PROJECT_MEMORY_DIR="$HOME/.codex/projects/$sanitized_cwd/memory"
run_ts="$(date +%Y%m%d-%H%M%S)"
run_feature="$(printf '%s' "$ARGUMENTS" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
[ -n "$run_feature" ] || run_feature="task"
RUN_DIR="$HOME/.ai-pir-runs/$sanitized_cwd/$run_ts-$run_feature"
HANDOFF_PATH="$HOME/.ai-pir-runs/$sanitized_cwd/handoff.md"
INNER_LOOP_COUNT=0
OUTER_LOOP_COUNT=0
IMPL_INDEX="00"
REPLAN_COUNT="00"
REVIEW_INDEX="00"
TEST_INDEX="00"
PRE_IMPL_INDEX=""
REPORT_SUFFIX=""
WORKER_RAW_OUTPUT=""
IMPLEMENTATION_REPORT_PATH=""
REPLAN_ARTIFACT_PATH=""
REVIEW_REPORT_PATH=""
TEST_REPORT_PATH=""
mkdir -p "$RUN_DIR"
printf '%s\n' \
  "PROJECT_ROOT=$PROJECT_ROOT" \
  "PROJECT_MEMORY_DIR=$PROJECT_MEMORY_DIR" \
  "RUN_DIR=$RUN_DIR" \
  "HANDOFF_PATH=$HANDOFF_PATH" \
  "REPLAN_COUNT=$REPLAN_COUNT" \
  "REVIEW_INDEX=$REVIEW_INDEX" \
  "TEST_INDEX=$TEST_INDEX"
```

RESUME_MODE は次で決めます。

- タスク引継ぎを示す語（resume、handoff、引継い、続きなど）が $ARGUMENTS にあれば resume
- それ以外で $HANDOFF_PATH が存在すれば passive-notice
- それ以外は new

resume では handoff の未完了項目を planner に渡し、passive-notice では存在だけを知らせ、new では plan 作成後に handoff の初期版を作ります。詳細は $PROJECT_ROOT/.codex/pir-handoff.md と $PROJECT_ROOT/.codex/skills/pir2/references/handoff-cleanup.md に従います。

### 共通 observability（Phase 0 では初期化だけ）

Phase 0 では `${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/record-observation.sh` を `OBS_HELPER` に束縛し、台帳の `init` だけを worker 起動前に一度実行する。worker / acceptance / verdict の値はこの段階では未確定なので、ここで append してはいけない。具体的な CLI と固定 TSV header は `pir2/references/worker-observability.md` を SSOT とする。

```sh
OBS_HELPER="${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/record-observation.sh"
"$OBS_HELPER" init --run-dir "$RUN_DIR"
```

---

## ステップ 2: 必要なら brainstorm

要件が曖昧、設計の選択肢が複数、またはユーザーとの対話が手戻りを減らす場合だけ brainstorm を先に実行します。brainstorm の結果を planner への入力に含め、設計ドキュメント保存だけで停止せずステップ3へ進みます。

---

## ステップ 3: 非同期探索

spawn_agent で最低1体の explorer を起動します。独立した領域がある場合だけ最大3体まで同時に起動します。初回探索の artifact は
`RUN_DIR/exploration-NN.md` とし、追加探索では Step 4 の `REPLAN_COUNT` を含む固有の
`RUN_DIR/replan-REPLAN_COUNT-exploration-NN.md` を使います。各依頼には次を含めます。

- PROJECT_ROOT、PROJECT_MEMORY_DIR、RUN_DIR
- EXPLORATION_INDEX=NN
- タスクと担当領域
- 初回は RUN_DIR/exploration-NN.md、追加探索は RUN_DIR/replan-REPLAN_COUNT-exploration-NN.md に事実ベースのレポートを書き、呼び出し元には要約だけ返すこと
- target repository の実装、stage、commit、push、destructive git 操作を行わないこと
- 既存パターン、再利用可能な utility、呼び出し経路、外部依存、未解決点

起動後は send_message でレポートパスと禁止事項を再確認します。レポートに未解決の具体的な問いが残った場合だけ、元の担当者へ followup_task を発行して追加の read-only 調査を行います。追加探索の番号は既存の最大値+1にします。

---

## ステップ 4: planner / deepplan と再探索

`$ARGUMENTS` に `--deepplan` / `deepplan` があれば `PLAN_MODE=deepplan`（フラグ除外）。でなければ `planner`。

### PLAN_MODE=deepplan

`.codex/skills/deepplan/SKILL.md`（本体は `.agents/skills/deepplan/SKILL.md`）を同一 `RUN_DIR` で実行し `{RUN_DIR}/plan.md` を得る。EXPLORATION_NEEDED 残時の再策定も deepplan。以降の実装はチーム側。

### PLAN_MODE=planner（既定）

探索レポートのパス一覧、brainstorm 結果（実施時）、handoff（resume 時）を spawn_agent の planner に渡します。planner は次を実行します。

- RUN_DIR/plan.md に目標、対象ファイル、実装手順、検証手順、禁止範囲を書き出す
- 実装は行わない
- 追加調査が必要なら EXPLORATION_NEEDED と具体的な topic を返す
- plan の要約だけを呼び出し元へ返す

`EXPLORATION_NEEDED` が残る間は、**各追加探索 attempt の直前**に次を順番に実行します。

1. `REPLAN_COUNT="$(printf '%02d' "$((10#$REPLAN_COUNT + 1))")"` として 2 桁の値へ増分する。`REPLAN_COUNT` が `05` を超えたら追加 explorer / planner を起動せず、retry cap の hard stop として未解決 topic を記録し、追加探索 loop を終了して次のステップへ進む
2. `EXPLORATION_INDEX` を `${RUN_DIR}/exploration-*.md` と `${RUN_DIR}/replan-*-exploration-*.md` の既存 artifact における最大連番 + 1 に割り当て、`REPLAN_ARTIFACT_PATH="${RUN_DIR}/replan-${REPLAN_COUNT}-exploration-${EXPLORATION_INDEX}.md"` を新しい未作成パスとして確定する
3. `REPLAN_ARTIFACT_PATH` を explorer の出力先と planner への入力一覧へ渡してから、追加 explorer を spawn_agent で起動する

同一 `REPLAN_COUNT` の topic が複数ある場合は、topic ごとに `EXPLORATION_INDEX` と artifact path を分ける。追加探索完了後に planner を再起動し、更新された `EXPLORATION_NEEDED` を確認する。収束後、必要なら docs/plans/YYYY-MM-DD-<feature>.md に plan を保存します。

---

## ステップ 5: 実装前ゲートとキュー

$PROJECT_ROOT/.codex/skills/pir2/references/next-steps-queue.md の形式で RUN_DIR/next-steps.md を作成し、ユーザー会話で中断した場合は次の判断前に必ず読み直します。

実装開始前に、既存の PIR² ゲートを実行します。

- $PROJECT_ROOT/.codex/skills/pir2/references/destructive-change-check.md
- $PROJECT_ROOT/.codex/skills/pir2/references/feedback-conflict-gate.md
- $PROJECT_ROOT/.codex/skills/pir2/references/implementation-delegation.md

判定、ユーザー確認、計画逸脱の扱いは各 reference を SSOT とします。実験比較のため、通常の /pir2 と同じ REVIEWER_SET（既定は correctness / consistency / quality / security / architecture）を記録します。

---

## ステップ 6: 具体実装は worker-delegation だけで行う

スキル本体が plan を読み、具体的な一つの task.md と requirements.md を作成します。task には目的、所有範囲、具体的な手順、禁止事項、入力パスを、requirements には diff・変更ファイル・検証コマンドで判定できる - R<number>: を記載します。

初回実装は次の runner 契約で Luna に委譲します。

```sh
IMPL_INDEX="01"
PRE_IMPL_INDEX="$IMPL_INDEX"
REPORT_SUFFIX="$IMPL_INDEX"
WORKER_RAW_OUTPUT="$RUN_DIR/worker-output-${REPORT_SUFFIX}.md"
IMPLEMENTATION_REPORT_PATH="$RUN_DIR/implementation-${REPORT_SUFFIX}.md"
$PROJECT_ROOT/.codex/skills/worker-delegation/scripts/run-worker.sh \
  --actor luna --effort max \
  --cwd "$PROJECT_ROOT" \
  --task-file <task.md> \
  --requirements-file <requirements.md> \
  --output-file "$WORKER_RAW_OUTPUT"
```

### 必須: すべての worker job の決定論的完了ゲート

初回実装（initial implementation）だけでなく、reviewer FAIL 後・tester FAIL 後を含む**すべての worker-delegation job とすべての correction**（Luna、測定済み Terra、例外的な Sol worker
の再実行を含む）で、Sol acceptance の前に
`$PROJECT_ROOT/.codex/skills/worker-delegation/references/deterministic-completion-check.md`
を Read し、同じ決定論的完了プロトコルを実行します。worker の終了コードや
自己申告だけでこのゲートを省略してはいけません。

1. `IMPL_INDEX` と `PRE_IMPL_INDEX` を決め、job 固有の `REPORT_SUFFIX` を作り、
   `WORKER_RAW_OUTPUT="${RUN_DIR}/worker-output-${REPORT_SUFFIX}.md"` と
   `IMPLEMENTATION_REPORT_PATH="${RUN_DIR}/implementation-${REPORT_SUFFIX}.md"` を
   新しい未作成パスへ更新します。worker 起動**前**に reference の **pre-set**
   snapshot を `${RUN_DIR}/verify-${PRE_IMPL_INDEX}-pre.list` へ保存します。
2. worker job の完了直後、Sol は `$WORKER_RAW_OUTPUT` を Read し、`ACTOR`、
   `ACTUAL_MODEL`、`ACTUAL_EFFORT`、`STATUS`、`CHANGED_FILES`、`OBSERVED_RESULTS`、
   `BLOCKERS`、`ESCALATION_REASON` の 8 fields を確認します。raw の変更申告を
   rename/copy せず、`git status -sb`、実際の diff、実在ファイル、requirements ごとの
   コマンド結果を独立に測定して `$IMPLEMENTATION_REPORT_PATH` を Write します。
   canonical report には Sol が確認した metadata と、正確な
   `### 変更ファイル一覧` の backtick path 箇条書き、`### 注意点・未解決事項` を含めます。
3. Sol normalization 完了後にだけ **post-set** snapshot、delta、canonical report
   だけを source とする CLAIMED 集合を reference の手順どおりに計算し、
   `${RUN_DIR}/verify-${IMPL_INDEX}.md` に判定を記録します。raw は CLAIMED source に
   せず、raw+canonical の和集合も作りません。
4. `PHANTOM_CLAIM` は **hard fail** です。reviewer、tester、Sol acceptance
   へ進まず、原因付き correction task/requirements を worker-delegation に戻し、
   reference の retry / user gate に従います。
5. `UNDECLARED_CHANGE` は warning として記録し、実際の diff を Sol が確認します。
   warning を隠したり、申告集合を推測で補ったりしてはいけません。

共通 verifier は `$PROJECT_ROOT/.codex/skills/worker-delegation/scripts/verify-deterministic-check.sh` を `bash` で実行し、判定 report と pre/post/delta のパスを Sol acceptance evidence に記録します。

決定論的ゲートの判定と証拠（pre-set、post-set、delta、canonical worker report、
verifier report）が揃った**後にのみ** Sol が acceptance を記録できます。つまり、
worker-delegation の初回実装にも correction にも例外はありません。

Luna の結果を Sol orchestrator が diff、変更ファイル、要求されたコマンド、requirements ごとに実測します。判断不足・権限不足・CLI error・入力不足では自動的に別 actor へ進まず、不足を解消して再計画します。十分な入力を与えたうえで Luna の capability または local-reasoning insufficiency を実測できた場合だけ、同じ task/requirements を `--actor terra --effort high` で明示再実行します。Terra High を同じ原因で Max に上げるのは、multi-stage causality、design contradiction、cross-module invariants、security/data-integrity risk、または documented High insufficiency の証拠がある場合に一度だけ許可します。Terra の capability/local-reasoning insufficiency を測定した場合だけ、例外的な Sol worker subagent を `--actor sol --effort high` で明示起動します。Sol High を同じ原因で Max に上げるのは highest-complexity/high-risk evidence または documented Sol High insufficiency がある場合に一度だけ許可します。requirements、environment、permission、external/CLI、一般 blocker は effort を上げる理由にせず、全 attempt を `automatic_fallback=no` として記録します。各段は条件付きで、全段を必ず実行しません。

reviewer / tester の FAIL 後も、具体的な修正はこの同じ worker-delegation ladder に戻します。collaboration API で実装担当者を起動したり、レビュー役に target file の修正をさせたりしません。

実装レポートは Sol が独立測定して作る canonical report とし、single は
`RUN_DIR/implementation-IMPL_INDEX.md`、shard は
`RUN_DIR/implementation-IMPL_INDEX-shard-SHARD_ID.md`、review-fix shard は
`RUN_DIR/implementation-IMPL_INDEX-review-fix-REVIEW_FIX_SHARD_ID.md`、unit は
`RUN_DIR/implementation-IMPL_INDEX-unit-UNIT_ID.md` に保存します。raw はそれぞれ
`worker-output-` prefix の同じ suffix で保存し、runner の `--output-file` に渡すのは
raw のみです。shard/unit の CLAIMED は canonical report 全件の union だけです。

```markdown
### 変更ファイル一覧
- path/to/changed-file — 変更の概要

### 実装概要
[実測した概要]

### 注意点・未解決事項
[なし、または具体的な事項]
```

上記の決定論的完了ゲートが完了した後にだけ Sol が acceptance を記録し、次のステップへ進みます。

### observability の実イベント（各 concrete job / correction / shard）

各 worker job の raw → canonical → deterministic gate の後、Sol が acceptance または blocker と
各 `Rn` の測定を確定した直後に、job 固有の実測値で `worker` を一度だけ append します。Phase 0
では未確定値を束縛せず、各 correction / shard は新しい `JOB_ID`、index、raw/provenance、canonical
artifact を使います。

```sh
JOB_ID="pir2async-${REPORT_SUFFIX}"
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

Sol が各 `Rn` を実測した直後は acceptance を一行ずつ append します。非同期 reviewer の各 report
完了直後は concrete role とその cycle の `REVIEW_INDEX`、tester report 完了直後は `tester` と
`TEST_INDEX` を渡します。generic `reviewer` role の行は作りません。

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

---

## ステップ 7: 非同期 reviewer 連携

各 Fan-Out reviewer cycle の直前に、次を **1 回だけ**実行します（role ごとに増分してはいけません）。

```bash
REVIEW_INDEX="$(printf '%02d' "$((10#$REVIEW_INDEX + 1))")"
```

この cycle の全 role は同じ `REVIEW_INDEX` を共有し、role ごとに
`REVIEW_REPORT_PATH="${RUN_DIR}/review-${REVIEW_INDEX}-${REVIEWER_ROLE}.md"` を確定します。
初回 cycle は `00` から `01`、修正後の再レビューは必ず次の新しい 2 桁 index になります。
Fan-Out Gate の違反を同じ cycle 内で再送する場合だけ index を据え置き、別 cycle として再レビューを始める場合は必ず増分します。

REVIEWER_SET の各 role に対し、同じレビューサイクル内で spawn_agent を起動します。各 reviewer には PROJECT_ROOT、PROJECT_MEMORY_DIR、RUN_DIR、REVIEW_INDEX、plan、Sol が作成した最新 canonical `$IMPLEMENTATION_REPORT_PATH`、担当 role、`REVIEW_REPORT_PATH` を渡します。raw `$WORKER_RAW_OUTPUT` は reviewer の入力にも CLAIMED source にも渡しません。reviewer は実際の diff と plan を読み、担当観点だけを判定し、`REVIEW_REPORT_PATH`（`RUN_DIR/review-REVIEW_INDEX-ROLE.md`）に書き出します。

起動後、スキル本体は send_message で各 reviewer に対象 report と「担当観点以外を PASS/FAIL 判定へ混ぜない」境界を伝えます。`REVIEWER_SET` の各 role について個別 report と明示的な verdict を確認し、role の欠落、未報告、判定不能、`PASS` 以外の verdict、または未解決の Critical / High を reviewer gate の non-PASS とします。全 role の verdict が PASS、すなわち `every reviewer in REVIEWER_SET returns PASS` かつ未解決の Critical / High がないときだけ reviewer gate は PASS です。

reviewer gate が non-PASS の場合:

1. `REVIEWER_SET` の各 role の report を個別に Read し、欠落・未報告・判定不能も role ごとの未解決事項として記録する。マージ要約を根拠にしない
2. `INNER_LOOP_COUNT += 1`
3. `INNER_LOOP_COUNT >= 3` で 1 role でも non-PASS、未報告、判定不能、または未解決の Critical / High が残る場合は、overall FAIL として停止する。各 role の未解決事項を report から列挙してユーザーに報告し、ユーザーの判断を求める。この retry-cap hard stop では correction job、tester、または成功完了を進めてはいけない。tester へ進めたり成功完了を報告したりしてはいけない。
4. 上限未到達の場合だけ、指摘を task/requirements に具体化する
5. `IMPL_INDEX` を増分し、`PRE_IMPL_INDEX` と `REPORT_SUFFIX` を更新して新しい
   `WORKER_RAW_OUTPUT` / `IMPLEMENTATION_REPORT_PATH` を確定する。runner の
   `--output-file` は raw pathだけにし、worker完了後は raw → Sol normalization →
   deterministic gate → acceptance の順で処理する。worker-delegation の runner で修正し、
   ステップ6の決定論的完了ゲートを実行した後にだけ Sol acceptance を実測する
6. 修正後の実装を、以前に PASS だった role も含めた `REVIEWER_SET` の every reviewer に followup_task（継続不能なら同じ role の spawn_agent）で再レビューさせる。再レビューを新しい Fan-Out cycle として開始する直前に `REVIEW_INDEX` を 2 桁で増分し、その cycle の全 role に同じ index と固有の `REVIEW_REPORT_PATH` を渡す。観点集合を減らしたり、PASS だった role を省略したりしてはいけない。

Tester may start and successful completion may be reported only after every reviewer in REVIEWER_SET returns PASS and the implementation job's deterministic completion gate is complete. 1 roleでも FAIL、Critical / High、未判定、または未報告なら tester へ進みません。観点集合は run の途中で変更しません。

---

## ステップ 8: tester と外側ループ（reviewer PASS 後に必須）

REVIEWER_SET の every reviewer が PASS を返した後にだけ、別系統の tester launch を行います。各 `spawn_agent(agent_type="tester")` の **直前**に、次を 1 回だけ実行します（retry でも同じ手順を繰り返します）。

```bash
TEST_INDEX="$(printf '%02d' "$((10#$TEST_INDEX + 1))")"
TEST_REPORT_PATH="${RUN_DIR}/test-${TEST_INDEX}.md"
```

したがって初回 launch は `00` から `01`、retry は `02` 以降の新しい 2 桁 index と固有の `TEST_REPORT_PATH` になります。`.codex/agents/tester.toml` の定義、plan、最新 canonical `$IMPLEMENTATION_REPORT_PATH`、TEST_SCOPE、RUN_DIR、`TEST_INDEX`、`TEST_REPORT_PATH` を渡します。raw `$WORKER_RAW_OUTPUT` は tester の入力、CLAIMED source、verdict source にしません。tester は実行可能なテスト、アドホック確認、documentation/config-only に適切な静的・構文・設定検証を行い、`TEST_REPORT_PATH`（`RUN_DIR/test-TEST_INDEX.md`）に実際の結果を書きます。tester を省略せず、PASS/FAIL は worker の報告と分離します。

`VERDICT: FAIL` の場合は、次の順序を厳守します。

1. `OUTER_LOOP_COUNT += 1`。
2. `OUTER_LOOP_COUNT >= 3` なら、次の tester 起動より先に、
   共通 `${PROJECT_ROOT}/.codex/skills/pir2/references/continuation-gate.md` を必ず Read し、続行判定へ分岐します。
   この Read と分岐を完了するまで `worker correction`、`task.md` / `requirements.md` の作成を開始してはいけません。`OUTER_LOOP_COUNT == 3` なら 8-2-G を実行し、既に許可した追加周回の tester FAIL で `OUTER_LOOP_COUNT > 3` になった場合は、ゲートを再度通過させず、`${RUN_DIR}/user-decisions.md` に記録して overall FAIL の hard stop とします。
3. `OUTER_LOOP_COUNT < 3` の場合だけ、`INNER_LOOP_COUNT=0` に戻し、tester report を直接 Read して修正 task/requirements を作成し、`IMPL_INDEX` を増分して新しい `REPORT_SUFFIX`、`WORKER_RAW_OUTPUT`、`IMPLEMENTATION_REPORT_PATH` を割り当てます。通常 correction は worker-delegation で実行し、raw normalization → deterministic gate → acceptance → `REVIEWER_SET` の every reviewer（PASS 済みも含む）→ tester の順を保持します。worker の完了報告は tester verdict ではありません。deterministic verifier report path と pre/post/delta path は各 correction の acceptance evidence に記録します。

### 8-2-G: 続行可能ゲート（`OUTER_LOOP_COUNT` 上限到達時のみ）

共通 reference を Read した後、`OUTER_LOOP_COUNT == 3` では `${RUN_DIR}/test-{最新}.md` と `${RUN_DIR}/implementation-{最新}.md` を Read し、reference の4条件を判定します。ゲート発火、4条件の判定、ユーザー回答、最終判断は必ず `${RUN_DIR}/user-decisions.md` に追記します。4条件がすべて成立した場合だけユーザーへ Y/N を尋ね、Y は4条件が全て成立した場合だけ許可します。

- Y の場合だけ `OUTER_LOOP_COUNT=4` に進め、ゲートの判断を記録してから最新 tester report を Read し、追加 correction を1回だけ作成して、worker correction → raw normalization → deterministic gate → acceptance → every reviewer → tester の一周を実行します。追加周回でもゲートを再通過させず、`OUTER_LOOP_COUNT=4` の追加周回後の tester FAIL はその場で overall FAIL の hard stop とします。
- N、4条件の不足、または追加周回後の tester FAIL は overall FAIL の hard stop です。条件不足で Y/N を出さない場合も含め、追加 correction・成功完了・ステップ9の振り返りと handoff・ステップ10の実験サマリーへ進めてはいけません。

---

## ステップ 9: 振り返りと handoff

spawn_agent で retrospector を起動するか、スキル本体が同じ入力を使って振り返ります。次を渡します。

- RUN_DIR 内の plan / implementation / `replan-REPLAN_COUNT-exploration-EXPLORATION_INDEX.md`、`review-REVIEW_INDEX-ROLE.md`、`test-TEST_INDEX.md` report
- `REPLAN_COUNT`、`REVIEW_INDEX`、`TEST_INDEX`（いずれも 2 桁の最新 artifact index）
- `INNER_LOOP_COUNT`（reviewer retry cap は 3）、`OUTER_LOOP_COUNT`（tester retry cap は通常上限3、continuation gateでユーザーYの場合だけ最大4）、再探索 retry cap は 5
- WORKFLOW_KIND=pir2async
- PLAN_STRATEGY_CHANGED=false

振り返り結果を PROJECT_MEMORY_DIR/pir_skill_log.md に追記します。handoff が存在する場合は $PROJECT_ROOT/.codex/skills/pir2/references/handoff-cleanup.md に従い、全 TODO 完了時だけ削除します。

---

## ステップ 10: 実験サマリー

結果は次の形式でユーザーへ提示します。

```markdown
## PIR² Async 実験サマリー

- タスク: [説明]
- workflow: pir2async（experimental）
- REVIEWER_SET: [実際に起動した role]
- 変更ファイル: [Sol が diff で確認した一覧]
- reviewer: [PASS / FAIL]、INNER_LOOP_COUNT=[N]
- tester: [PASS / FAIL]、OUTER_LOOP_COUNT=[N]
- 再探索: REPLAN_COUNT=[NN]
  - 最終 reviewer artifact index: REVIEW_INDEX=[NN]
  - 最終 tester artifact index: TEST_INDEX=[NN]
  - retry cap: replan=5、reviewer=3、tester=通常上限3、continuation gateでユーザーYの場合だけ最大4（到達時は未解決事項とともに hard stop を記録）
  - 実装 actor: [luna / terra / sol、実測 model/effort、evidence-backed 昇格理由]
- RUN_DIR: [パス]
- blocker / 未解決事項: [なければ none]
```

実験結果は通常の /pir2 と比較できるよう、レビューの所要時間、指摘の質、worker acceptance と独立 reviewer/tester の差異を記録します。
