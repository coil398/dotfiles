# Codex Worker Observability Protocol

Codex native workflow の共通 `worker-delegation` 実行を、run 単位で機械集計するための観測スキーマです。このファイルが観測レコードの SSOT です。実作業の責任境界と actor ladder は `${PROJECT_ROOT}/.codex/skills/worker-delegation/SKILL.md`、実験の採用/廃止判断は `experimental.md` が SSOT であり、このファイルはそれらを置き換えません。

## 記録範囲と責任

- 1 run のすべての actor attempt（`luna`、明示昇格した `terra`、例外的な `sol` worker）を記録する。shard と reviewer/tester FAIL 後の修正も、各 job/attempt を別行にする。
- actor の完了報告、自己申告、runner の exit code は事実の補助情報であり、Sol acceptance の根拠ではない。acceptance の判定者と根拠は `sol-acceptance-v1.tsv` の `verdict`、`acceptance_basis`、`evidence_*` で固定する。
- reviewer と tester は worker acceptance と別系統である。実行した結果は `independent-verdicts-v1.tsv` にだけ記録し、`sol-acceptance-v1.tsv` の `verdict` に転記して結合しない。
- `experimental.md` は実験レジストリの仮説・集計・採用判断だけを持つ。実 run の actor 行や acceptance 行をそこへ移動・複製しない。retrospector はこの台帳を読み、実験の集計を更新するだけである。

## Run directory の成果物

各 `{RUN_DIR}` に、初回 actor attempt の前に次の UTF-8 TSV を作る。空のファイルを残すのではなく、実行されたレコードだけを追記する。

| ファイル | 1 行の単位 | 用途 |
| --- | --- | --- |
| `{RUN_DIR}/worker-observations-v1.tsv` | actor attempt 1 件 | actor、実モデル、時刻、結果、昇格、自己申告と Sol 実測の比較 |
| `{RUN_DIR}/sol-acceptance-v1.tsv` | 1 job × 1 requirement | Sol が差分とコマンドで判定した各 `Rn` の PASS/FAIL |
| `{RUN_DIR}/independent-verdicts-v1.tsv` | reviewer または tester の 1 verdict | worker acceptance と独立した品質/動作判定 |

既存の versioned Markdown は証拠本文として残す。少なくとも `implementation-{IMPL_INDEX}*.md`、`sol-acceptance-{IMPL_INDEX}*.md`、`review-{REVIEW_INDEX}-*.md`、`test-{TEST_INDEX}.md` を TSV の `*_ref` から参照する。TSV は要約と索引、Markdown と command output は詳細証拠であり、どちらか一方だけで acceptance を作らない。

### TSV 共通規約

- 先頭 1 行は固定ヘッダー、2 行目以降はデータ行とする。ヘッダー以外にコメント・空行を入れない。
- 各 run で `schema_version=1` を使い、列順を変更しない。将来の非互換変更は `-v2.tsv` として別ファイルにする。既存 v1 を上書きしない。
- すべての timestamp は UTC の RFC 3339（例 `2026-08-06T01:02:03Z`）、`duration_ms` は非負整数とする。`ended_at_utc` は provider/runner の終了、または Sol が起動失敗を観測した時刻とする。
- 値には literal の tab、改行、CR を入れない。詳細は `*_ref` のファイルに書き、短い要約が必要な場合は `%` を `%25`、tab を `%09`、LF を `%0A`、CR を `%0D` の順に percent-encode する。path は run directory からの相対 path を優先する。
- `record_id`、`run_id`、`job_id`、`attempt_id`、`acceptance_id`、`verdict_id` は run 内で一意な ASCII 識別子とする。`attempt_id` は `{run_id}:{job_id}:{attempt_key}` とし、`attempt_key` は2桁 index、または `NN-shard-SAFE`、`NN-review-fix-SAFE`、`NN-unit-SAFE` とする。raw/sidecar/canonical report は同じ key を使う。
- レコードは append-only とする。Sol acceptance の測定が変わる場合は既存行を編集せず、新しい actor/job attempt と理由を追記する。通常の actor 行は Sol acceptance 後に 1 回だけ書くため、同じ `attempt_id` を上書きしない。

## 1. Actor attempt ledger

`worker-observations-v1.tsv` の canonical header は次のとおりです。

```tsv
schema_version	record_type	record_id	run_id	job_id	attempt_id	attempt_seq	actor	actual_model	actual_effort	started_at_utc	ended_at_utc	duration_ms	result	exit_code	validation_status	self_report_result	sol_measurement_result	mismatch	mismatch_reason	escalation_from	escalation_to	escalation_reason	effort_escalation_from	effort_escalation_to	automatic_fallback	insufficiency_class	input_sufficient	measured_insufficiency_ref	task_ref	requirements_ref	report_ref	changed_files_ref	verification_ref	observed_at_utc	notes
```

必須値と意味:

- `record_type` は常に `actor_attempt`。
- `actor` は `luna`、`terra`、`sol` のいずれか。`actual_model` は要求モデル名の写しではなく、実際に起動・実行されたモデル名を記録する。起動前に失敗して実モデルを観測できなかった場合は `unavailable` とし、`verification_ref` に起動エラーを置く。実行できた model は、それぞれ `gpt-5.6-luna`、`gpt-5.6-terra`、`gpt-5.6-sol` とする。
- `worker-observations-v1.tsv` の `actual_effort` は実際に起動された worker effort の `high|max`（起動前に実測不能なら `unavailable`）を記録する。Luna は `max`、Terra は `high` または `max`、Sol worker は `high` または `max` とし、Terra High/Max と Sol High/Max を別 attempt として識別できるようにする。worker attempt と escalation の effort domain は `high|max` のままである。
- `started_at_utc` は actor 起動直前、`ended_at_utc` は actor 終了/起動失敗を Sol が観測した時点。`result` は actor の事実上の `completed|failed|blocked|not_started` であり、acceptance ではない。`exit_code` は整数または `unavailable|na`。`validation_status` は runner-owned provenance sidecar の `validated|raw_invalid|codex_failed|codex_failed_no_output` をそのまま記録し、raw report の自己申告で補わない。
- `self_report_result` は `validation_status=validated` の canonical raw report の `STATUS` だけを正規化した `completed|failed|blocked`。raw が未公開の `raw_invalid|codex_failed|codex_failed_no_output` では必ず `not_provided` とし、Sol の worker status で代用しない。`sol_measurement_result` は Sol の測定を `accepted|rejected|blocked` で記録する。actor 行は、対応する job の Sol acceptance（または blocker の実測）を終えてから追記する。
- `insufficiency_class` は `none|capability|local-reasoning|requirement-failure|unavailable`、`input_sufficient` は `yes|no|not_applicable` とする。actor/effort escalation fields が両方 `none/none` の通常行は `insufficiency_class=none`、`escalation_reason=none`、`measured_insufficiency_ref=none` とする。
- `mismatch` は `match|mismatch|not_comparable`。`mismatch` は、worker が `completed` と自己申告したのに Sol の 1 つ以上の requirement が FAIL/未検証・範囲外だった場合、または worker が失敗/blocked と申告したのに Sol が全 requirement を PASS と実測した場合。`mismatch_reason` は `match` なら `none`、`mismatch|not_comparable` なら実測理由を必須で記録する。この列を数えることで自己申告と実測の不一致件数を得る。
- escalation fields は、現在 attempt を起動するに至った「直前 attempt → current attempt」の遷移を current attempt の actor row に記録する。初回 Luna は actor/effort とも `none/none`。Luna→Terra の current Terra 行は `escalation_from/to=luna/terra`、Terra→Sol の current Sol 行は `terra/sol` とし、`escalation_to` は provenance の current actor と一致させる。Terra High→Max または Sol High→Max の current max 行は actor fields を `none/none`、`effort_escalation_from/to=high/max` とし、effort target は provenance の current `max` と一致させる。非昇格は両組とも `none/none`、actor と effort の同時昇格は禁止する。
- actor 遷移または effort 遷移を行う場合、`escalation_reason`、`insufficiency_class`、`input_sufficient=yes`、`measured_insufficiency_ref` を必須とする。`insufficiency_class=capability|local-reasoning` は、十分な入力を与えた先行 actor の不足を差分・Sol acceptance・検証コマンドの実測証拠で示すために使う。requirements、environment、permission、external/CLI、一般 blocker だけでは actor/effort を上げない。
- Terra `high` → `max` は `multi-stage causality|design contradiction|cross-module invariants|security/data-integrity risk|documented-high-insufficiency` の証拠があり、同じ原因で未使用の場合に一度だけ許可する。Terra の測定済み capability/local-reasoning insufficiency 後に Sol worker を `high` で起動し、Sol `high` → `max` は highest-complexity/high-risk evidence または documented Sol High insufficiency があり、同じ原因で未使用の場合に一度だけ許可する。
- `automatic_fallback` は `no|yes` とする。正規の全 attempt と全遷移は必ず `automatic_fallback=no` とし、runner が actor/effort を自動切替した場合だけ `yes` として契約違反を記録し、成功扱いにしない。`escalation_reason` は Sol の明示判断として必須である。

`worker-observations-v1.tsv` には、開始時点で記録した actor を後から更新する代わりに、Sol acceptance（または blocker の実測）後、開始・終了時刻を含む完成行を 1 行 append する。既存 actor 行を編集してはならない。比較材料が存在しない場合だけ `mismatch=not_comparable` とし、その理由を `mismatch_reason` に記録する。

## 2. Sol acceptance ledger

`sol-acceptance-v1.tsv` は worker の status/report/exit code とは別に、Sol が requirements の各行を測定した結果を記録します。canonical header:

```tsv
schema_version	record_type	record_id	run_id	job_id	attempt_id	acceptance_id	requirement_id	verdict	evidence_ref	evidence_summary	acceptance_basis	worker_self_report_result	worker_exit_code	sol_observed_at_utc	notes
```

規則:

- `record_type` は `sol_acceptance`、`requirement_id` は `R<number>`、`verdict` は必ず `PASS|FAIL`。requirements の各 `Rn` に 1 行以上を追加し、同じ acceptance evaluation の全行で `acceptance_id` を共有する。別 actor attempt の再測定は新しい `acceptance_id` にする。
- `evidence_ref` は `git status -sb`、対象 `git diff`、変更ファイル、要求された検証コマンドの実際の出力、またはそれらを記録した `sol-acceptance-*.md` の path を列挙する。`evidence_summary` は結論ではなく、何を観測したかの短い percent-encoded 要約にする。
- `acceptance_basis` は `sol_measurement` 固定とし、`worker_self_report`、`worker_exit_code`、`runner_success` は禁止する。`worker_self_report_result` と `worker_exit_code` は比較・監査用の参考値であり、どちらも PASS の根拠にならない。
- 1 つでも `FAIL` があればその acceptance evaluation は FAIL、全 `Rn` が PASS なら `accepted`。actor 行の `sol_measurement_result` はこの evaluation と一致させる。worker の `STATUS: completed` や exit code 0 だけで `PASS` 行を作ってはならない。

Sol acceptance の Markdown は人間が読む証拠本文、TSV は requirement 別の索引です。Markdown にだけ PASS を書いて TSV を省略しないでください。

## 3. Reviewer/tester independent verdict ledger

`independent-verdicts-v1.tsv` は acceptance 後（または acceptance と並行して別系統で）実行した concrete reviewer role / tester の結果だけを記録します。canonical header:

```tsv
schema_version	record_type	record_id	run_id	target_attempt_id	verdict_id	cycle	source_role	actual_model	actual_effort	started_at_utc	ended_at_utc	verdict	evidence_ref	evidence_summary	sol_acceptance_ref	notes
```

- `record_type` は `independent_verdict`、`source_role` は `correctness|consistency|quality|security|architecture|tester` のいずれか（generic な `reviewer` は禁止）、`actual_model` と `actual_effort` は各独立実行で観測した値、`actual_effort` はこの verdict ledger に限り `medium|high|max`、`verdict` は `PASS|FAIL|BLOCKED|SKIPPED`。これは worker attempt と escalation の `high|max` domain を広げるものではない。
- `--target-attempt-index` は worker の `REPORT_SUFFIX`、`--cycle` は reviewer/tester の独立した2桁 cycle であり、混同しない。同じ target/cycle の複数 reviewer は role ごとに別行にし、`verdict_id={run_id}:{job_id}:{review|test}:{cycle}:{source_role}` で一意にする。reviewer の quality/correctness/security 等と tester の動作検証は別行にする。`actual_model`、時間、`evidence_ref` は各実行のものを記録する。
- `sol_acceptance_ref` は対応する `sol-acceptance-v1.tsv` または Markdown への参照に過ぎず、reviewer/tester の verdict を Sol acceptance に代入しない。acceptance が未実施なら `not_available` と明記する。
- reviewer/tester を起動しなかった場合は捏造した PASS/FAIL 行を追加しない。仕様上の skip を判定した場合だけ `SKIPPED` とその理由を `evidence_summary` に記録する。

## Run ごとの手順

1. `RUN_DIR` と `run_id` を確定し、3 TSV のヘッダーを一度だけ作る。actor 起動ごとに固有の `job_id`、`attempt_id`、`attempt_seq` を割り当てる。
2. 起動直前の時刻、actor、実行予定モデル、task/requirements path を Sol の一時メモに取り、actor 終了後に実モデル、終了時刻、result、report、exit code を観測する。
3. `git status -sb`、対象 diff、変更ファイル、requirements ごとの Sol 検証コマンドを実行する。`sol-acceptance-v1.tsv` に R ごとの PASS/FAIL と evidence path を append する。
4. acceptance 測定後に actor 行の `sol_measurement_result` と mismatch を確定し、`worker-observations-v1.tsv` に一度だけ append する。worker raw 完了直後に actor 行を append してはならない。Terra または Sol worker へ進む場合は、先行 actor の行に actor/effort の遷移、reason、class、実測証拠、`automatic_fallback=no` を記録してから、次の attempt を明示開始する。入力不足・権限不足・CLI error は自動昇格のトリガーではない。
5. reviewer/tester のレポートが完成したら `independent-verdicts-v1.tsv` にそれぞれ append する。worker report の自己申告を verdict 欄へコピーしない。
6. retrospector は 3 TSV と versioned Markdown を読み、必要な experiment-level 集計だけを `experimental.md` の既存責務に従って更新する。TSV の schema/actor 行を再定義しない。

## 共通 helper CLI（実行可能な SSOT）

台帳の初期化と append は、各 concrete workflow が自前の TSV 書き込みを実装せず、次の POSIX helper に委譲する。

`${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/record-observation.sh` は、実行時の実体ある非シンボリックリンク `$HOME/.ai-pir-runs` 配下だけを受け付ける。`umask 077` で新規 run directory と 3 ledger を作り、既存 ledger は固定 header を検証するだけで上書きしない。引数、sidecar 値、短い説明に literal tab/newline/CR を渡すと拒否する（TSV の区切り tab は helper が生成する）。

```sh
OBS_HELPER="$PROJECT_ROOT/.codex/skills/worker-delegation/scripts/record-observation.sh"

# Phase 0: 初回 worker attempt より前に一度だけ実行
"$OBS_HELPER" init --run-dir "$RUN_DIR"

# Sol acceptance または blocker の実測確定後: runner が no-replace 公開した sidecar を authoritative source とする
"$OBS_HELPER" worker \
  --run-dir "$RUN_DIR" \
  --raw-output "$WORKER_RAW_OUTPUT" \
  --provenance "$WORKER_RAW_OUTPUT.provenance.tsv" \
  --job-id "$JOB_ID" --index "$REPORT_SUFFIX" --status "$WORKER_STATUS" \
  --sol-measurement-result "$SOL_MEASUREMENT_RESULT" --mismatch "$MISMATCH_RESULT" --mismatch-reason "$MISMATCH_REASON" \
  --escalation-from "$ESCALATION_FROM" --escalation-to "$ESCALATION_TO" \
  --effort-escalation-from "$EFFORT_ESCALATION_FROM" --effort-escalation-to "$EFFORT_ESCALATION_TO" --escalation-reason "$ESCALATION_REASON" \
  --insufficiency-class "$INSUFFICIENCY_CLASS" --input-sufficient "$INPUT_SUFFICIENT" --measured-insufficiency-ref "$MEASURED_INSUFFICIENCY_REF" \
  --task-ref "$TASK_FILE" --requirements-ref "$REQUIREMENTS_FILE" \
  --report-ref "$IMPLEMENTATION_REPORT_PATH" \
  --changed-files-ref "$CHANGED_FILES_REF" --verification-ref "$VERIFICATION_REF"

# Sol acceptance 後: requirement ごとに一行ずつ append
"$OBS_HELPER" acceptance \
  --run-dir "$RUN_DIR" --job-id "$JOB_ID" --index "$REPORT_SUFFIX" \
  --requirement-id R1 --verdict PASS --evidence-ref "$ACCEPTANCE_REF" \
  --evidence-summary "$EVIDENCE_SUMMARY"

# 各 reviewer/tester verdict 後: concrete role と cycle/index を指定
"$OBS_HELPER" verdict \
  --run-dir "$RUN_DIR" --job-id "$JOB_ID" --target-attempt-index "$REPORT_SUFFIX" --cycle "$REVIEW_OR_TEST_INDEX" \
  --role "$REVIEW_ROLE" --verdict "$REVIEW_VERDICT" --report-ref "$REVIEW_REPORT_PATH" \
  --model "$VERDICT_ACTUAL_MODEL" --effort "$VERDICT_ACTUAL_EFFORT" --evidence-ref "$VERDICT_EVIDENCE_REF" --sol-acceptance-ref "$ACCEPTANCE_REF"
```

`worker` は sidecar の `started_at_utc ended_at_utc duration_ms actor model effort codex_exit validation_status` を読み、raw の ACTOR/MODEL/EFFORT を採用しない。`validation_status=validated` のときだけ canonical raw が必須で、その他の failure attempt は raw 未公開でも sidecar と Sol blocker evidence で記録する。`acceptance` は `R<number>` と `PASS|FAIL`、`verdict` は concrete role、実測 model/effort、evidence ref と `PASS|FAIL|BLOCKED|SKIPPED` を必須とする。reviewer/tester を実行しない場合、捏造した verdict 行を追加してはならない。

## 追加依存なしの集計例

TSV は POSIX `awk` だけで集計できる。ヘッダー名から列を引くため、列の番号を手で固定しない。

```sh
# actor attempt 数（actor 別）
awk -F '\t' '
  NR == 1 { for (i = 1; i <= NF; i++) col[$i] = i; next }
  $(col["record_type"]) == "actor_attempt" { count[$(col["actor"])]++ }
  END { for (actor in count) print actor "\t" count[actor] }
' "${RUN_DIR}/worker-observations-v1.tsv" | sort

# Sol acceptance の PASS/FAIL（requirement 別）
awk -F '\t' '
  NR == 1 { for (i = 1; i <= NF; i++) col[$i] = i; next }
  $(col["record_type"]) == "sol_acceptance" {
    key = $(col["job_id"]) "\t" $(col["requirement_id"]) "\t" $(col["verdict"])
    count[key]++
  }
  END { for (key in count) print key "\t" count[key] }
' "${RUN_DIR}/sol-acceptance-v1.tsv" | sort

# worker 自己申告と Sol 実測の mismatch 件数
awk -F '\t' '
  NR == 1 { for (i = 1; i <= NF; i++) col[$i] = i; next }
  $(col["record_type"]) == "actor_attempt" && $(col["mismatch"]) == "mismatch" { count++ }
  END { print count + 0 }
' "${RUN_DIR}/worker-observations-v1.tsv"

# reviewer / tester の独立 verdict
awk -F '\t' '
  NR == 1 { for (i = 1; i <= NF; i++) col[$i] = i; next }
  $(col["record_type"]) == "independent_verdict" {
    print $(col["source_role"]) "\t" $(col["verdict"])
  }
' "${RUN_DIR}/independent-verdicts-v1.tsv" | sort | uniq -c
```

`awk`、`sort`、`uniq` は新規依存ではなく、空の TSV に対する集計結果は 0 件として扱う。集計時は同一 `attempt_id` の訂正行を重複計上せず、常に run の実行記録と `record_id` を突合する。

## 実行形態の境界

この仕様は actor の自動選択・自動 fallback・実装の再試行を追加しません。`worker-delegation` の actor ladder に従い、Luna Max を既定に、十分な task/requirements と capability/local-reasoning insufficiency の実測があるときだけ Sol が Terra High を明示起動します。許可された証拠があるときだけ Terra Max、測定済み Terra insufficiency があるときだけ Sol High worker、highest-complexity/high-risk evidence または documented Sol High insufficiency があるときだけ Sol Max worker を明示起動します。記録を残すこと自体は、昇格の許可や acceptance の代替ではありません。
