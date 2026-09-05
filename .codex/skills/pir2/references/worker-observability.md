# Codex Worker Observability Protocol

明示 CLI runner job の artifact/provenance と受入測定を run 単位で記録する v1 schema
です。通常の native collaboration と Astra 直接実装にはこの台帳を作りません。actor 選択と
runner 契約は、今回ロードした `worker-delegation/SKILL.md` と同 skill の
`references/runner-contract.md` を SSOT とします。対象リポジトリ内に同名 skill があると
推測して参照しません。

既存の `sol-acceptance-v1.tsv`、`sol_measurement_result`、
`--sol-measurement-result` などの名称は CLI/schema 互換のため維持します。この文書でいう
それらの測定主体は現行の親 Astra です。

## 記録範囲と責任

- この台帳を適用した runner job の actor attempt だけを記録する。native collaboration の
  attempt や Astra 直接実装を runner 行へ変換しない。
- actor の完了報告、自己申告、runner の exit code は補助情報であり、Astra acceptance
  の根拠ではない。判定者と根拠は互換名 `sol-acceptance-v1.tsv` の `verdict`、
  `acceptance_basis`、`evidence_*` で固定する。
- reviewer と tester は worker acceptance と別系統である。実行した結果は `independent-verdicts-v1.tsv` にだけ記録し、`sol-acceptance-v1.tsv` の `verdict` に転記して結合しない。
- `experimental.md` は実験レジストリの仮説・集計・採用判断だけを持つ。実 run の actor 行や acceptance 行をそこへ移動・複製しない。retrospector はこの台帳を読み、実験の集計を更新するだけである。

## Run directory の成果物

観測を必要とする runner job では、初回 attempt 前に既存 helper で次の UTF-8 TSV を
初期化し、実行されたレコードだけを追記します。reviewer/tester を使わなかった場合、
verdict ledger は header-only のままであり、未実行 verdict を意味しません。

| ファイル | 1 行の単位 | 用途 |
| --- | --- | --- |
| `{RUN_DIR}/worker-observations-v1.tsv` | runner actor attempt 1 件 | provenance、結果、遷移、自己申告と Astra 実測の比較 |
| `{RUN_DIR}/sol-acceptance-v1.tsv` | 1 job × 1 requirement | Astra が差分とコマンドで判定した各 `Rn` の PASS/FAIL |
| `{RUN_DIR}/independent-verdicts-v1.tsv` | reviewer または tester の 1 verdict | worker acceptance と独立した品質/動作判定 |

既存の versioned Markdown や command output がある場合は `*_ref` から参照します。
存在しない implementation/review/test artifact を台帳のために作らず、実在する diff と
確認出力なしに acceptance を作りません。

### TSV 共通規約

- 先頭 1 行は固定ヘッダー、2 行目以降はデータ行とする。ヘッダー以外にコメント・空行を入れない。
- 各 run で `schema_version=1` を使い、列順を変更しない。将来の非互換変更は `-v2.tsv` として別ファイルにする。既存 v1 を上書きしない。
- すべての timestamp は UTC の RFC 3339（例 `2026-08-06T01:02:03Z`）、`duration_ms` は非負整数とする。`ended_at_utc` は provider/runner の終了、または Astra が起動失敗を観測した時刻とする。
- 値には literal の tab、改行、CR を入れない。詳細は `*_ref` のファイルに書き、短い要約が必要な場合は `%` を `%25`、tab を `%09`、LF を `%0A`、CR を `%0D` の順に percent-encode する。path は run directory からの相対 path を優先する。
- `record_id`、`run_id`、`job_id`、`attempt_id`、`acceptance_id`、`verdict_id` は run 内で一意な ASCII 識別子とする。`attempt_id` は `{run_id}:{job_id}:{attempt_key}` とし、`attempt_key` は2桁 index、または `NN-shard-SAFE`、`NN-review-fix-SAFE`、`NN-unit-SAFE` とする。raw/sidecar/canonical report は同じ key を使う。
- レコードは append-only とする。Astra acceptance の測定が変わる場合は既存行を編集せず、新しい actor/job attempt と理由を追記する。actor 行は acceptance 後に 1 回だけ書き、同じ `attempt_id` を上書きしない。

## 1. Actor attempt ledger

`worker-observations-v1.tsv` の canonical header は次のとおりです。

```tsv
schema_version	record_type	record_id	run_id	job_id	attempt_id	attempt_seq	actor	actual_model	actual_effort	started_at_utc	ended_at_utc	duration_ms	result	exit_code	validation_status	self_report_result	sol_measurement_result	mismatch	mismatch_reason	escalation_from	escalation_to	escalation_reason	effort_escalation_from	effort_escalation_to	automatic_fallback	insufficiency_class	input_sufficient	measured_insufficiency_ref	task_ref	requirements_ref	report_ref	changed_files_ref	verification_ref	observed_at_utc	notes
```

必須値と意味:

- `record_type` は常に `actor_attempt`。
- `actor` は `luna`、`terra`、`sol` のいずれか。`actual_model` は要求モデル名の写しではなく、実際に起動・実行されたモデル名を記録する。起動前に失敗して実モデルを観測できなかった場合は `unavailable` とし、`verification_ref` に起動エラーを置く。実行できた model は、それぞれ `gpt-5.6-luna`、`gpt-5.6-terra`、`gpt-5.6-sol` とする。
- `worker-observations-v1.tsv` の `actual_effort` は実際に起動された worker effort の `high|max`（起動前に実測不能なら `unavailable`）を記録する。Luna は `max`、Terra は `high` または `max`、Sol worker は `high` または `max` とし、Terra High/Max と Sol High/Max を別 attempt として識別できるようにする。worker attempt と escalation の effort domain は `high|max` のままである。
- `started_at_utc` は actor 起動直前、`ended_at_utc` は actor 終了/起動失敗を Astra が観測した時点。`result` は actor の事実上の `completed|failed|blocked|not_started` であり、acceptance ではない。`exit_code` は整数または `unavailable|na`。`validation_status` は runner-owned provenance sidecar の `validated|raw_invalid|codex_failed|codex_failed_no_output` をそのまま記録し、raw report の自己申告で補わない。
- `self_report_result` は `validation_status=validated` の canonical raw report の `STATUS` だけを正規化した `completed|failed|blocked`。raw が未公開なら必ず `not_provided` とし、Astra の worker status で代用しない。互換列 `sol_measurement_result` は Astra の測定を `accepted|rejected|blocked` で記録する。
- `insufficiency_class` は `none|capability|local-reasoning|requirement-failure|unavailable`、`input_sufficient` は `yes|no|not_applicable` とする。actor/effort escalation fields が両方 `none/none` の通常行は `insufficiency_class=none`、`escalation_reason=none`、`measured_insufficiency_ref=none` とする。
- `mismatch` は `match|mismatch|not_comparable`。worker の自己申告と Astra が実測した requirement 結果が食い違う場合に `mismatch` とし、理由を必須で記録する。
- transition fields は「直前 attempt → current attempt」を current row に記録します。初手の Luna または direct Sol は actor/effort とも `none/none` です。難所の direct Sol に Luna/Terra の先行 attempt は要りません。
- 十分な入力を与えた Luna の capability/local-reasoning 不足を実測した場合は `luna→sol` を記録できます。Terra 経由は不要です。Terra transition は workload-specific exception を Astra が明示選択した場合だけ `luna→terra` または `terra→sol` を使います。
- actor 内の `high→max` は実測した複雑性・リスクまたは high insufficiency がある場合だけです。actor と effort の同時 transition は記録しません。
- transition には `automatic_fallback=no`、`input_sufficient=yes`、実測理由、evidence ref を必須とします。入力、仕様、権限、環境、外部/CLI failure は能力不足として actor/effort を上げる理由にしません。
- runner が actor/effort を自動変更した場合だけ `automatic_fallback=yes` の契約違反として記録し、成功扱いにしません。

`worker-observations-v1.tsv` には、Astra acceptance（または blocker の実測）後、開始・終了時刻を含む完成行を 1 行 append します。既存 actor 行を編集しません。比較材料が存在しない場合だけ `mismatch=not_comparable` とし、理由を記録します。

## 2. Astra acceptance ledger（互換ファイル名: sol-acceptance-v1.tsv）

`sol-acceptance-v1.tsv` は worker の status/report/exit code とは別に、Astra が requirements の各行を測定した結果を記録します。canonical header:

```tsv
schema_version	record_type	record_id	run_id	job_id	attempt_id	acceptance_id	requirement_id	verdict	evidence_ref	evidence_summary	acceptance_basis	worker_self_report_result	worker_exit_code	sol_observed_at_utc	notes
```

規則:

- `record_type` は `sol_acceptance`、`requirement_id` は `R<number>`、`verdict` は必ず `PASS|FAIL`。requirements の各 `Rn` に 1 行以上を追加し、同じ acceptance evaluation の全行で `acceptance_id` を共有する。別 actor attempt の再測定は新しい `acceptance_id` にする。
- `evidence_ref` は `git status -sb`、対象 `git diff`、変更ファイル、要求された検証コマンドの実際の出力、またはそれらを記録した `sol-acceptance-*.md` の path を列挙する。`evidence_summary` は結論ではなく、何を観測したかの短い percent-encoded 要約にする。
- `acceptance_basis` は互換値 `sol_measurement` 固定とし、意味上は Astra の実測です。`worker_self_report`、`worker_exit_code`、`runner_success` は禁止し、比較・監査用の値だけで PASS にしません。
- 1 つでも `FAIL` があればその acceptance evaluation は FAIL、全 `Rn` が PASS なら `accepted`。actor 行の `sol_measurement_result` はこの evaluation と一致させる。worker の `STATUS: completed` や exit code 0 だけで `PASS` 行を作ってはならない。

Astra acceptance の実在する証拠本文または command output を TSV から参照します。台帳を適用した runner job では Markdown だけに PASS を書いて TSV を省略しません。

## 3. Reviewer/tester independent verdict ledger

`independent-verdicts-v1.tsv` は acceptance 後（または acceptance と並行して別系統で）実行した concrete reviewer role / tester の結果だけを記録します。canonical header:

```tsv
schema_version	record_type	record_id	run_id	target_attempt_id	verdict_id	cycle	source_role	actual_model	actual_effort	started_at_utc	ended_at_utc	verdict	evidence_ref	evidence_summary	sol_acceptance_ref	notes
```

- `record_type` は `independent_verdict`、`source_role` は `correctness|consistency|quality|security|architecture|tester` のいずれか（generic な `reviewer` は禁止）、`actual_model` と `actual_effort` は各独立実行で観測した値、`actual_effort` はこの verdict ledger に限り `medium|high|max`、`verdict` は `PASS|FAIL|BLOCKED|SKIPPED`。これは worker attempt と escalation の `high|max` domain を広げるものではない。
- `--target-attempt-index` は worker の `REPORT_SUFFIX`、`--cycle` は reviewer/tester の独立した2桁 cycle であり、混同しない。同じ target/cycle の複数 reviewer は role ごとに別行にし、`verdict_id={run_id}:{job_id}:{review|test}:{cycle}:{source_role}` で一意にする。reviewer の quality/correctness/security 等と tester の動作検証は別行にする。`actual_model`、時間、`evidence_ref` は各実行のものを記録する。
- `sol_acceptance_ref` は対応する `sol-acceptance-v1.tsv` または実在する証拠への参照に過ぎず、reviewer/tester の verdict を Astra acceptance に代入しない。acceptance が未実施なら `not_available` と明記する。
- reviewer/tester を起動しなかった場合は捏造した PASS/FAIL 行を追加しない。仕様上の skip を判定した場合だけ `SKIPPED` とその理由を `evidence_summary` に記録する。

## Run ごとの手順

1. 観測を必要とする runner job でだけ `RUN_DIR` と `run_id` を確定し、helper で3 TSV の header を一度初期化する。各 attempt に固有 id を割り当てる。
2. Astra が起動前後の時刻、選択 actor、provenance、result、exit を観測する。
3. Astra が `git status`、対象 diff、変更ファイル、requirements ごとの確認を実行し、互換ファイル `sol-acceptance-v1.tsv` へ結果を append する。
4. acceptance または blocker の実測後に、actor 行の `sol_measurement_result` と mismatch を確定して一度 append する。transition がある場合は current attempt の行に `automatic_fallback=no` と実測証拠を記録する。direct Sol は transition なし、Luna からの能力昇格は `luna→sol` を許可する。
5. reviewer/tester を必要に応じて実行した場合だけ、その実在する verdict を `independent-verdicts-v1.tsv` に append する。自己申告をコピーしない。
6. retrospector は実在する台帳・証拠だけを集計し、未使用 actor や未実行 verdict を補わない。

## 共通 helper CLI（実行可能な SSOT）

台帳の初期化と append は、各 concrete workflow が自前の TSV 書き込みを実装せず、次の POSIX helper に委譲する。

今回ロードした `worker-delegation/SKILL.md` の親を
`WORKER_DELEGATION_SKILL_DIR` とし、その
`scripts/record-observation.sh` を使います。helper は実体ある非 symlink の標準
artifact root 配下だけを受け付け、`umask 077`、固定 header、no-overwrite、TSV 値の
検証を維持します。

```sh
OBS_HELPER="$WORKER_DELEGATION_SKILL_DIR/scripts/record-observation.sh"

# Phase 0: 初回 worker attempt より前に一度だけ実行
"$OBS_HELPER" init --run-dir "$RUN_DIR"

# Astra acceptance または blocker の実測確定後
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

# Astra acceptance 後: requirement ごとに一行ずつ append
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

`worker` は sidecar の identity/time/exit/validation を正とし、raw の
ACTOR/MODEL/EFFORT を identity 証明に使いません。validated のときだけ canonical raw を
要求し、それ以外は sidecar と Astra blocker evidence で記録します。reviewer/tester を
実行しない場合、捏造した verdict 行を追加しません。

## 追加依存なしの集計例

TSV は POSIX `awk` だけで集計できる。ヘッダー名から列を引くため、列の番号を手で固定しない。

```sh
# actor attempt 数（actor 別）
awk -F '\t' '
  NR == 1 { for (i = 1; i <= NF; i++) col[$i] = i; next }
  $(col["record_type"]) == "actor_attempt" { count[$(col["actor"])]++ }
  END { for (actor in count) print actor "\t" count[actor] }
' "${RUN_DIR}/worker-observations-v1.tsv" | sort

# Astra acceptance の PASS/FAIL（互換列名を使用、requirement 別）
awk -F '\t' '
  NR == 1 { for (i = 1; i <= NF; i++) col[$i] = i; next }
  $(col["record_type"]) == "sol_acceptance" {
    key = $(col["job_id"]) "\t" $(col["requirement_id"]) "\t" $(col["verdict"])
    count[key]++
  }
  END { for (key in count) print key "\t" count[key] }
' "${RUN_DIR}/sol-acceptance-v1.tsv" | sort

# worker 自己申告と Astra 実測の mismatch 件数
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

この schema は actor 選択、自動 fallback、再試行、acceptance、review/test を追加しません。
通常経路は native collaboration の worker、難所は初手から expert/expert_max、小さく
密結合した変更は Astra 直接実装です。Terra は実測根拠のある例外だけです。

台帳は runner が必要な job の観測手段に限ります。runner の安全境界を変更していない
通常 job で8 fixtureを再実行せず、native collaboration に runner artifact や v1 TSV を
要求しません。記録を残すこと自体は actor transition や acceptance の代替ではありません。
