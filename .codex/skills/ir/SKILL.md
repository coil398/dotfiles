---
name: "ir"
description: "軽量な Implement → Review の2フェーズワークフロー。タスクが明確で小さい場合に使う。バグ修正・小機能追加・設定変更・ファイル修正など、計画不要で「サクッとやって」「これ直して」「簡単な変更」といった要望に対応する。ユーザーが /ir と入力したら必ずこのスキルを使う。"
argument-hint: "[タスクの説明]"
---

# IR — Implement → Review

軽量ワークフローを実行します。プランニング・振り返りなしで、小さいタスクに使います。Sol（スキル本体）は実装範囲と要件を具体化し、具体実装は共通の [worker-delegation 契約](../worker-delegation/SKILL.md) に委譲します。reviewer / tester は worker とは別系統で起動し、品質・動作判定を担当します。

**タスク**: $ARGUMENTS

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

`/ir` は handoff 連携を行わないため、`HANDOFF_PATH` / `RESUME_MODE` は不要です。

### 共通 observability（Phase 0 では初期化だけ）

Phase 0 では `${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/record-observation.sh` を `OBS_HELPER` に束縛し、台帳の `init` だけを worker 起動前に一度実行する。worker / acceptance / verdict の値はこの段階では未確定なので、ここで append してはいけない。具体的な CLI と固定 TSV header は `pir2/references/worker-observability.md` を SSOT とする。

```sh
OBS_HELPER="${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/record-observation.sh"
"$OBS_HELPER" init --run-dir "$RUN_DIR"
```

---

## ステップ 1: 実装 (worker-delegation)

具体実装は `.codex/skills/worker-delegation/SKILL.md` を契約として扱い、Sol orchestrator は対象リポジトリを実装・修正しません。Sol orchestrator が小さいタスクの所有範囲と、ファイル・差分・コマンド出力で判定できる `R1` から始まる requirements を決めます。IRの軽量性を保つため、planner・handoff・retrospective の工程は追加しません。

初回の実装試行は `IMPL_INDEX=01` とします。Sol orchestrator は `mktemp -d` に `task.md`（目的、対象範囲、具体的な実装指示、禁止事項）と `requirements.md`（タスク固有の `- R<number>:` 要件）を用意し、既定の Luna Max worker を次で起動します。worker raw output と Sol canonical report は別 artifact とし、各 correction では新しい index/suffix の未作成パスを割り当てます。

```sh
WORKER_RUN_DIR="$(mktemp -d)"
TASK_FILE="$WORKER_RUN_DIR/task.md"
REQUIREMENTS_FILE="$WORKER_RUN_DIR/requirements.md"
PRE_IMPL_INDEX="$IMPL_INDEX"
REPORT_SUFFIX="$IMPL_INDEX"
WORKER_RAW_OUTPUT="$RUN_DIR/worker-output-$REPORT_SUFFIX.md"
IMPLEMENTATION_REPORT_PATH="$RUN_DIR/implementation-$REPORT_SUFFIX.md"
# Solが TASK_FILE と REQUIREMENTS_FILE を Write する
.codex/skills/worker-delegation/scripts/run-worker.sh \
  --actor luna --effort max \
  --cwd "$PROJECT_ROOT" \
  --task-file "$TASK_FILE" \
  --requirements-file "$REQUIREMENTS_FILE" \
  --output-file "$WORKER_RAW_OUTPUT"
```

worker 完了直後、Sol は `$WORKER_RAW_OUTPUT` を Read し、`ACTOR`、`ACTUAL_MODEL`、
`ACTUAL_EFFORT`、`STATUS`、`CHANGED_FILES`、`OBSERVED_RESULTS`、`BLOCKERS`、
`ESCALATION_REASON` の canonical 8 fields を確認します。raw の申告を rename/copy して
済ませず、`git status -sb`、対象 diff、実在ファイル、requirementsごとの検証コマンドを
Sol が独立に実測し、`$IMPLEMENTATION_REPORT_PATH` に canonical metadata、正確な
`### 変更ファイル一覧`（各項目は backtick path）、`### 注意点・未解決事項` を Write
します。deterministic CLAIMED は canonical report のみを読み、raw は CLAIMED source
にしません。順序は raw → Sol normalization → deterministic post/CLAIMED → acceptance
→ reviewer → tester です。

Lunaの完了報告やrunnerの終了だけをacceptanceとみなさず、Sol orchestrator が `git status -sb`、対象差分、変更ファイル、requirementsごとの検証コマンド出力を実測して判定します。Lunaの判断不足・requirements failure・権限不足・CLI error・入力不足・環境 failureは自動的に別 actor へ進まず、Sol orchestrator が不足を解消して再計画します。taskとrequirementsが十分で、Lunaの capability または local-reasoning insufficiency を実測できた場合だけ、理由・差分・昇格時点を記録し、`--actor terra --effort high` を明示して同じ要件のTerra Highを起動します。Terra Highを同じ原因でMaxにするのは、multi-stage causality、design contradiction、cross-module invariants、security/data-integrity risk、または documented High insufficiency の証拠がある場合に一度だけ許可します。Terraの capability/local-reasoning insufficiencyを測定した場合だけ、Sol worker subagentを `--actor sol --effort high` で明示起動します。Sol Highを同じ原因でMaxにするのは、highest-complexity/high-risk evidence または documented Sol High insufficiency がある場合に一度だけ許可します。全 attempt は `automatic_fallback=no` として記録し、全段を必ず実行することはありません。

### 1-1: 決定論的完了ゲート（全 worker job / correction）

worker起動直前に `IMPL_INDEX` / `PRE_IMPL_INDEX` を固定し、`WORKER_RAW_OUTPUT` と `IMPLEMENTATION_REPORT_PATH` を新しい suffix へ更新して pre-set を取ります。worker report 直後（Sol acceptance、reviewer、tester の前）に、Sol normalization 済み canonical reportだけを入力として、共通 SSOT `${PROJECT_ROOT}/.codex/skills/worker-delegation/references/deterministic-completion-check.md` の post-set / delta / CLAIMED 手順を実行します。shard/unit がある場合は raw/canonical の suffix を一致させ、CLAIMED は canonical report 全件の union のみとします。`${RUN_DIR}/verify-${IMPL_INDEX}.md` を作成し、`bash "${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/verify-deterministic-check.sh"` で8 fixtureを検証します。共通 protocol は複製せず、IR固有の `IMPL_INDEX` / `REVIEW_INDEX` / `TEST_INDEX` を記録します。

`PHANTOM_CLAIM` は hard fail です。reviewer、tester、acceptanceへ進まず、原因と verifier path を含む correction task/requirements を同じ Luna-first actor ladder に戻します。上限到達時は overall FAIL の hard stop としてユーザー判断を待ちます。`UNDECLARED_CHANGE` は warn として実差分を Sol が確認します。PASS時だけ pre/post/delta/verifier path を acceptance evidence と reviewer/tester 起動記録に残します。

Solのacceptance後にのみステップ2へ進み、reviewer / tester による品質・動作判定はworkerの自己申告と分離します。

### 1-2. observability の実イベント（各 concrete job / correction / shard）

各 worker job の raw → canonical → deterministic gate の後、Sol が acceptance または
blocker と `Rn` ごとの測定を確定した直後に、実測した値を束縛して次の `worker` 行を一度だけ
append します。`JOB_ID` / `WORKER_STATUS` / `SOL_MEASUREMENT_RESULT` / `MISMATCH_RESULT` は
job ごとの実値（それぞれ `completed|blocked|failed`、`accepted|rejected|blocked`、
`match|mismatch|not_comparable`）であり、raw の自己申告を転記しません。shard や correction
でも `REPORT_SUFFIX`、raw/provenance、canonical report、`JOB_ID` を新しくします。

```sh
JOB_ID="ir-${REPORT_SUFFIX}"
WORKER_STATUS="$SOL_MEASURED_WORKER_STATUS"
SOL_MEASUREMENT_RESULT="$SOL_MEASURED_RESULT"
MISMATCH_RESULT="$SOL_MEASURED_MISMATCH"
MISMATCH_REASON="$SOL_MEASURED_MISMATCH_REASON"
ESCALATION_FROM="$SOL_ESCALATION_FROM"; ESCALATION_TO="$SOL_ESCALATION_TO"
EFFORT_ESCALATION_FROM="$SOL_EFFORT_ESCALATION_FROM"; EFFORT_ESCALATION_TO="$SOL_EFFORT_ESCALATION_TO"
ESCALATION_REASON="$SOL_ESCALATION_REASON"; INSUFFICIENCY_CLASS="$SOL_INSUFFICIENCY_CLASS"
INPUT_SUFFICIENT="$SOL_INPUT_SUFFICIENT"; MEASURED_INSUFFICIENCY_REF="$SOL_MEASURED_INSUFFICIENCY_REF"
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

Sol が各 `Rn` を実測した直後に、実際の verdict と evidence を requirement ごとに append します。

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
```

各 reviewer report 完了直後は concrete role と同じ cycle index を渡し、tester report 完了直後は
`tester` role を渡します。generic `reviewer` role の行は作りません。

```sh
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

## ステップ 2: レビュー (Codex reviewer ハイブリッド並列)

### 2-1: REVIEWER_SET 決定（非 planner 系：自動選定がデフォルト）

`REVIEWER_SET` を決定する:

1. **ユーザーフラグのパース**: `$ARGUMENTS` に `--reviewers=<roles>` が含まれていればカンマ区切りを観点集合として採用（未知 role は無視）。`--all-reviewers` が含まれていれば全 5 観点を採用。両方指定時は `--reviewers=` を優先。フラグ抽出後の残りをタスク説明として扱う
2. **フラグ未指定時の自動選定**（以下を上から評価し該当観点を集合に追加）:
   1. `correctness` は常に含める（動作正否の最低限ゲート）
   2. 実装がコード変更を含む（ドキュメント・設定のみでない。workerの完了報告にある変更ファイル一覧で判定） → `consistency` を追加
   3. タスク文言または `{RUN_DIR}/implementation-{IMPL_INDEX}.md` の差分テキストに**セキュリティ関連語句**（認証 / 認可 / auth / token / secret / password / credential / SQL / XSS / CSRF / シリアライズ / 外部API / ユーザー入力 / validate / sanitize / 権限 / 暗号 / crypto / 脆弱性）が含まれる → `security` を追加
   4. 実装で**新規ファイル追加**・**新規ディレクトリ作成**・**複数モジュール/レイヤー跨ぎ** → `architecture` を追加
   5. 実装で**新規関数・メソッド・クラスの追加**、または**ロジック変更行数 > 20 行** → `quality` を追加
   6. **判断に迷う**（implementation-*.md が読めない・タスク文言が曖昧・上記ルールで 1 体しか選ばれないが自信なし） → **全 5 観点へ拡張**
3. 決定した `REVIEWER_SET` を最終サマリー（ステップ 4）に記録

### 2-2A: 起動宣言（Fan-Out Gate — 並列発火の直前に必ず書く）

reviewer 並列起動メッセージを送信する **直前のターン本文中** に、以下のテンプレートを必ず生成すること。このテンプレートが本文に出現していないターンで `spawn_agent` を発火させた場合は、ステップ完了判定を取り消して 2-2A からやり直す。

> **Fan-Out Gate（reviewer）**
> - REVIEWER_SET = [<観点をカンマ区切りで全列挙>]
> - 起動体数 = <N>（= len(REVIEWER_SET)、必ず一致）
> - 同一 collaboration 呼び出しブロックに <N> 個の `spawn_agent` 起動を並べる
> - 1 体ずつ起動・後追い起動・観点削減はいずれも違反

このブロックは「起動直前の自己コミットメント」であり、自分の手癖（1 体ずつ逐次起動する癖）を止めるためのフェンスとして機能する。再レビュー時（ステップ 3 の差し戻し時）にも毎回この宣言を書くこと。

### 2-2B: 並列発火（同一メッセージ内）

直前ターンで宣言した REVIEWER_SET の各観点について、同一の collaboration 呼び出しブロック内に `spawn_agent`（`agent_type="reviewer"`）を **N 個** 並べて 1 メッセージで同時送信する。各体は `REVIEWER_ROLE` を変えて担当観点を分割する。モデル引数は指定せず、`.codex/agents/reviewer.toml` の role 定義に委ねます。

詳細仕様（観点マッピング / 違反パターンと検出 / 違反検出時のリカバリ / reviewer 起動パラメータ）: `.codex/skills/pir2/references/fan-out-gate.md` を参照。

違反パターン（次のいずれかが発生したら違反として検出し 2-2A からやり直す）:
- collaboration 呼び出しブロックが 2 ターン以上に分かれる
- 並んだ `spawn_agent` 起動の数が宣言した N より少ない
- 観点を独自判断で減らした
- 直前ターンの宣言テンプレートが省略された

各体の起動パラメータ:

- プロンプト（共通。`REVIEWER_ROLE` のみ変える）:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `REVIEW_INDEX=01`（初回。再レビュー時はインクリメント。起動する全体で同じ番号を共有する）
  - `REVIEWER_ROLE=[correctness|consistency|quality|security|architecture]`（体ごとに変える。REVIEWER_SET に含まれる観点のみ）
  - `{RUN_DIR}/implementation-{最新 IMPL_INDEX}.md` のパス
  - 「plan.md は存在しません。implementation-*.md のみをレビュー対象としてください。レビューレポート本体は `{RUN_DIR}/review-{REVIEW_INDEX}-{REVIEWER_ROLE}.md` に書き出し、チャットには VERDICT + 要約のみ返してください」

### VERDICT 集約

**今回起動した reviewer** の VERDICT を以下のルールで集約する:

- **全体 VERDICT = PASS**: `REVIEWER_SET` の every reviewer が `VERDICT: PASS`、未報告・判定不能・Critical / High の未解決がない
- **全体 VERDICT = FAIL**: 1体でも non-PASS、未報告、判定不能、または未解決の Critical / High

---

## ステップ 3: レビューループ (最大2回)

**LOOP_COUNT = 0 から始めてください。**

全体 `VERDICT: FAIL` の場合:

1. `LOOP_COUNT += 1`
2. `LOOP_COUNT >= 2` に達した場合は overall FAIL の hard stop としてユーザー判断を待つ。tester または成功完了へ進めない
3. Sol orchestrator がFAILを返した全 reviewer の `{RUN_DIR}/review-{最新}-{ROLE}.md` を読み、requirementsと具体的な修正タスクを更新して、`worker-delegation` の actor ladder（Luna Max → measured Terra High → evidence-only Terra Max → measured Sol High worker → evidence-only Sol Max）で再実装する。各遷移は capability/local-reasoning evidence と `automatic_fallback=no` を記録し、`IMPL_INDEX` / `PRE_IMPL_INDEX` を更新して固有 suffix の `WORKER_RAW_OUTPUT` と `IMPLEMENTATION_REPORT_PATH` を再計算する。runner の `--output-file` は raw pathだけにし、完了後は Sol normalization → deterministic gate → acceptance の順に戻す。
4. **2-2A（Fan-Out Gate 宣言）→ 2-2B（並列発火）の手順で** `reviewer` を **同じ REVIEWER_SET で**並列で再起動して VERDICT を確認する（`REVIEW_INDEX` をインクリメント、最新の canonical `$IMPLEMENTATION_REPORT_PATH` のパスだけを渡す。PASS を返した観点も再レビューする。観点集合は初回選定を維持し途中で追加・削除しない。**再レビュー時も Fan-Out Gate を省略しないこと**）
5. 全体 FAIL なら繰り返す

全体 `VERDICT: PASS` になったらステップ4へ進んでください。

---

## ステップ 3.5: tester（reviewer PASS 後に必須）

reviewer gate の every reviewer が PASS になった後、別系統の `spawn_agent(agent_type="tester")` を必ず起動します。tester role は `${PROJECT_ROOT}/.codex/agents/tester.toml` を使い、`PROJECT_MEMORY_DIR`、`RUN_DIR`、`TEST_INDEX=01`（再試行ごとに増分）、Sol が生成した canonical `$IMPLEMENTATION_REPORT_PATH`、検証対象を渡して `${RUN_DIR}/test-${TEST_INDEX}.md` に実測結果を書きます。raw `$WORKER_RAW_OUTPUT` は tester/verdict/CLAIMED の入力にしません。コード変更がない documentation/config-only でも適切な静的・構文・設定チェックを行い、tester を省略しません。worker report の自己申告は tester verdict として扱いません。

- `VERDICT: PASS` のときだけステップ4へ進む
- `VERDICT: FAIL` のときは `OUTER_LOOP_COUNT += 1`。3回到達時は overall FAIL の hard stop としてユーザー判断を待ち、成功扱いにしない
- 上限未到達なら tester report を根拠に correction task/requirements を作り、同じ Luna-first actor ladder で worker を起動する。worker report 直後にステップ1-1の決定論的 gateを再実行し、PASS後に acceptanceを記録する。次に以前に PASS だった role を含む `REVIEWER_SET` の every reviewer を再実行し、全員 PASS の後に testerを `TEST_INDEX += 1` で再実行する

---

## ステップ 4: 最終サマリーの提示

```
## IR 完了サマリー

### タスク
[タスクの説明]

### 変更ファイル
[実装完了レポートから抜粋]

### レビュー結果
- 最終 VERDICT: [PASS/FAIL]
- ループ回数: [LOOP_COUNT]
- REVIEWER_SET: [起動した観点をカンマ区切り、例: correctness,consistency]
- 観点別の VERDICT: [REVIEWER_SET に含まれる観点のみ。例: correctness=[...], consistency=[...]]
- [主な指摘事項があれば記載]
```
