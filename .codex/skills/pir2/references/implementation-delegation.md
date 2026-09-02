# Implementation Delegation Protocol

PIR² の具体実装と修正作業を、共通の `worker-delegation` 契約へ接続する
PIR² 固有プロトコルです。実作業の責任境界、入力検証、Sol acceptance、
actor の起動方法は `${PROJECT_ROOT}/.codex/skills/worker-delegation/SKILL.md`
を SSOT とし、このファイルでは PIR² の shard ゲート、適応 effort、成果物、
再実装の接続を定義します。観測レコードの schema は
`${PROJECT_ROOT}/.codex/skills/pir2/references/worker-observability.md`、
実験の採用判断は `experimental.md` を SSOT とします。決定論的な変更集合ゲートは
`${PROJECT_ROOT}/.codex/skills/worker-delegation/references/deterministic-completion-check.md`
とその verifier script を SSOT とし、この PIR² 固有文書で再定義しません。

## 責任境界と actor ladder

- **Sol orchestrator** はユーザー対話、探索、設計、scope、`task.md`、
  `requirements.md`、actor 選択、Sol acceptance、最終判断を所有します。
  orchestrator は対象リポジトリの実装・修正を行わず、worker の起動と
  非リポジトリの run artifact の管理だけを行います。
- **Luna Max worker** (`actor=luna`, `model=gpt-5.6-luna`,
  `effort=max`) が常に最初の具体作業を担当します。十分に具体化した入力と
  `R1...Rn` を先に用意し、worker に設計判断や別 actor の選択を委ねません。
- **Terra worker** は、入力が十分だったことを確認したうえで Luna の
  `capability` または `local-reasoning` insufficiency を差分・コマンド出力・
  Sol acceptance で測定できた場合だけ明示起動します。最初の Terra effort は
  常に `high` です。
- **Terra max** は同じ原因について最大 1 回だけ許可します。`high` から
  `max` へ上げられるのは、証拠が `multi-stage causality`、
  `design contradiction`、`cross-module invariants`、
  `security/data-integrity risk`、または `documented High insufficiency` の
  いずれかを示す場合だけです。requirements、environment、permission、
  external/CLI、または一般的な blocker の失敗は effort を上げる理由に
  なりません。該当証拠がなければ `high` の再試行や `max` への昇格をせず、
  Sol が入力・判断・環境を解消するかユーザーへ戻します。
- **Sol worker subagent** (`actor=sol`, `model=gpt-5.6-sol`,
  `effort=high`) は、Terra の attempt について capability または
  local-reasoning insufficiency を測定した場合だけ、Sol が明示起動できる
  例外的な最終 worker です。必須段ではなく、根拠がなければ起動しません。
  Sol High の同じ原因への `max` は一度だけ許可し、highest-complexity/high-risk
  evidence または documented Sol High insufficiency がある場合だけにします。
  これも対象リポジトリを変更する主体は worker subagent であり、Sol
  orchestrator の直接編集ではありません。

すべての遷移は明示的な actor と effort を持ち、runner の自動切替は使いません。
各 attempt と遷移には `automatic_fallback=no`、実際の model/effort、
evidence-backed `escalation_reason` を記録します。Luna の requirements failure、
入力不足、権限不足、環境 failure、外部/CLI failure は Terra に自動で進めず、
Terra `high` の failure も証拠なしに `max` や Sol worker へ進めません。

### 起動の形

task/requirements は各 attempt の前に Sol が作成し、同じ入力を保ったまま
必要な段だけを明示的に起動します。`--effort` は runner に渡す必須の実行
パラメータです。

```sh
# Every invocation (initial, correction, shard, or actor promotion) gets a
# fresh index/suffix and two distinct artifacts before the runner is called.
REPORT_SUFFIX="${IMPL_INDEX}"
WORKER_RAW_OUTPUT="${RUN_DIR}/worker-output-${REPORT_SUFFIX}.md"
IMPLEMENTATION_REPORT_PATH="${RUN_DIR}/implementation-${REPORT_SUFFIX}.md"

# 1. 必須の初回 attempt（runner は raw output だけを受け取る）
${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/run-worker.sh \
  --actor luna --effort max \
  --cwd "${PROJECT_ROOT}" \
  --task-file <task.md> \
  --requirements-file <requirements.md> \
  --output-file "${WORKER_RAW_OUTPUT}"

# 直前 attempt が終わったら IMPL_INDEX と上の 2 パスを更新してから、
# 同じ形で必要な昇格/correction を起動する（同じ raw/canonical path を再利用しない）。
# 2. Luna の capability/local-reasoning insufficiency を測定した場合だけ
${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/run-worker.sh \
  --actor terra --effort high \
  --cwd "${PROJECT_ROOT}" \
  --task-file <task.md> \
  --requirements-file <requirements.md> \
  --output-file "${WORKER_RAW_OUTPUT}"

# 3. 許可された証拠があり、同じ原因への max 使用がまだ無い場合だけ
${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/run-worker.sh \
  --actor terra --effort max \
  --cwd "${PROJECT_ROOT}" \
  --task-file <task.md> \
  --requirements-file <requirements.md> \
  --output-file "${WORKER_RAW_OUTPUT}"

# 4. Terra の measured capability/local-reasoning insufficiency の場合だけ
${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/run-worker.sh \
  --actor sol --effort high \
  --cwd "${PROJECT_ROOT}" \
  --task-file <task.md> \
  --requirements-file <requirements.md> \
  --output-file "${WORKER_RAW_OUTPUT}"

# 5. Sol High の同じ原因について highest-complexity/high-risk evidence または
#    documented Sol High insufficiency があり、max が未使用の場合だけ
${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/run-worker.sh \
  --actor sol --effort max \
  --cwd "${PROJECT_ROOT}" \
  --task-file <task.md> \
  --requirements-file <requirements.md> \
  --output-file "${WORKER_RAW_OUTPUT}"
```

上の 2〜5 は条件付きであり、すべての段を必ず実行する意味ではありません。
各起動前に直前 attempt の Sol acceptance と測定証拠を記録し、同じ原因に対する
Terra `max` と Sol `max` はそれぞれ 1 回で打ち切ります。Terra High/Max の
capability/local-reasoning insufficiency が測定できた場合だけ Sol High worker
へ移行し、Sol Max は上記の追加証拠がある場合だけ許可します。requirements、
environment、permission、external/CLI、一般 blocker の失敗は effort を上げる
理由になりません。runner が actor や effort を選び直すことはなく、各 attempt は
`automatic_fallback=no` と実際の actor/model/effort を記録します。

## 共通 worker job の入力と成果物

各 job の起動前に、リポジトリ内に残す必要がなければ `mktemp -d` で次を用意します。

- `task.md`: 目的、作業範囲/所有範囲、具体的な実装指示、禁止事項、必要な入力パス。
- `requirements.md`: 差分、変更ファイル、検証コマンドで真偽を判定できる
  `- R<number>:` 要件。「良い感じ」のような抽象要件だけで起動しない。
- worker raw output: runner の `--output-file` に渡す未信頼の自由形式 artifact。
  単一 job は `{RUN_DIR}/worker-output-{IMPL_INDEX}.md`、初回 shard は
  `{RUN_DIR}/worker-output-{IMPL_INDEX}-shard-{SHARD_ID}.md`、review-fix shard は
  `{RUN_DIR}/worker-output-{IMPL_INDEX}-review-fix-{REVIEW_FIX_SHARD_ID}.md`、
  sequential unit は `{RUN_DIR}/worker-output-{IMPL_INDEX}-unit-{UNIT_ID}.md`。
- Sol canonical implementation report: raw output と実測結果を Sol が独立に
  正規化して作る artifact。上記と同じ suffix で、それぞれ
  `{RUN_DIR}/implementation-{IMPL_INDEX}.md`、
  `{RUN_DIR}/implementation-{IMPL_INDEX}-shard-{SHARD_ID}.md`、
  `{RUN_DIR}/implementation-{IMPL_INDEX}-review-fix-{REVIEW_FIX_SHARD_ID}.md`、
  `{RUN_DIR}/implementation-{IMPL_INDEX}-unit-{UNIT_ID}.md` とする。
  raw と canonical は常に別パスであり、同じ index/suffix の既存 artifact を
  上書き・再利用しない。
- raw output は worker の事実引き渡し（`ACTOR`、`ACTUAL_MODEL`、
  `ACTUAL_EFFORT`、`STATUS`、`CHANGED_FILES`、`OBSERVED_RESULTS`、
  `BLOCKERS`、`ESCALATION_REASON` の canonical 8 fields）であり、acceptance
  判定ではない。Sol は worker 完了直後に raw の8 fieldsを Read し、`git status -sb`、
  diff、実在ファイル、requirementsごとのコマンド結果を独立に確認したうえで
  canonical report を Write する。raw の rename/copy を canonical report として
  扱ってはいけない。

各 `task.md` には次も明記します:

- `PROJECT_MEMORY_DIR=[パス]`
- `RUN_DIR=[パス]`
- `IMPL_INDEX=NN`
- `{RUN_DIR}/plan.md` のパス（IR のように plan がない workflow は明記）
- `IMPLEMENTATION_ACTOR=worker-delegation`
- shard の場合だけ `SHARD_ID` または `REVIEW_FIX_SHARD_ID` と許可/禁止ファイル。
- `WORKER_RAW_OUTPUT` と `IMPLEMENTATION_REPORT_PATH` の両方を入力に明記し、
  「worker は raw output を `WORKER_RAW_OUTPUT` に書き、Sol は canonical report を
  `IMPLEMENTATION_REPORT_PATH` に書く。チャットには要約のみ返す」と指定する。
- 独立した tester の verdict は tester 専任。worker は task.md が指定する
  task-scoped の静的検証、型チェック、ビルド、コード生成、焦点を絞った
  check、diff 確認を実行してよいが、tester verdict を自己申告しない。

## Raw → canonical → deterministic の順序（全 job / correction）

各 worker job（初回、shard、review-fix、tester FAIL 後の correction、actor 昇格を
含む）は、起動前に固有の `WORKER_RAW_OUTPUT` と `IMPLEMENTATION_REPORT_PATH` を
割り当てる。runner の `--output-file` には必ず前者だけを渡す。runner が終了した
直後に Sol は raw report の canonical 8 fields を Read し、実際のファイル集合・diff・
requirements のコマンド結果を独立に測定してから、後者へ canonical metadata と次の
見出しを Write する:

```markdown
ACTOR: luna|terra|sol
ACTUAL_MODEL: gpt-5.6-luna|gpt-5.6-terra|gpt-5.6-sol
ACTUAL_EFFORT: high|max
STATUS: completed|blocked|failed
CHANGED_FILES: Sol が実測した相対パス
OBSERVED_RESULTS: Sol が実行したコマンドと結果
BLOCKERS: なければ none
ESCALATION_REASON: なければ none

### 変更ファイル一覧
- `path/to/changed-file` — Sol が確認した変更概要

### 注意点・未解決事項
なし
```

`### 変更ファイル一覧` の各 path は canonical report のみが決定し、raw の
`CHANGED_FILES` を信頼して転記するだけではいけない。raw は forensic input として
保存する。正規化が完了した後にだけ common deterministic SSOT の post-set / delta /
CLAIMED 抽出を行い、さらに Sol acceptance → reviewer → tester の順へ進む。CLAIMED
入力は canonical report（shard/unit は該当 suffix 全件の union）のみとし、raw 単独や
raw+canonical の和集合を使ってはならない。

### Suffix と union の規則

- single: `REPORT_SUFFIX="$IMPL_INDEX"`
- initial shard: `REPORT_SUFFIX="${IMPL_INDEX}-shard-${SHARD_ID}"`
- review-fix shard: `REPORT_SUFFIX="${IMPL_INDEX}-review-fix-${REVIEW_FIX_SHARD_ID}"`
- sequential unit: `REPORT_SUFFIX="${IMPL_INDEX}-unit-${UNIT_ID}"`

各 job は suffix ごとに raw/canonical の2パスを更新し、存在する artifact を上書き
しない。shard/unit の deterministic gate は canonical report のみを suffix 全件から
union して `CLAIMED` を作り、raw は union に含めない。詳細な pre-set/post-set/delta/
CLAIMED 判定は共通 SSOTへ委譲し、この reference で再定義しない。

## 決定論的完了ゲート（全 job / correction）

各 worker job（初回、shard、review-fix、tester FAIL 後の correction、actor 昇格を
含む）は上記の canonical report 作成直後に、起動直前に固定した
`PRE_IMPL_INDEX="$IMPL_INDEX"` と common SSOT の post-set、delta、CLAIMED 抽出を
実行します。Sol acceptance / reviewer / tester はこの gate の後です。

`PHANTOM_CLAIM` は hard fail として原因付き correction task/requirements を
worker ladder に戻し、reviewer、tester、acceptanceへ進みません。
`UNDECLARED_CHANGE` は warn として Sol が実差分を確認します。verifier report と
pre/post/delta の各 path を acceptance evidence と起動記録に残します。
検証コマンドは次です（8 fixtureを含む）。

```sh
bash "${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/verify-deterministic-check.sh"
```

## Sol acceptance と独立 verdict

worker の自己申告、完了報告、runner の終了コードだけを acceptance PASS の根拠に
しません。各 attempt の後に Sol が `git status -sb`、対象 diff、変更ファイル、
全 requirements の検証コマンド出力を実測し、`{RUN_DIR}/sol-acceptance-{IMPL_INDEX}.md`
と `sol-acceptance-v1.tsv` に記録します。全 `Rn` を差分と実測出力で満たした場合
だけ acceptance を PASS とします。

reviewer は品質、tester は動作を判定する別系統です。両者の verdict は
`independent-verdicts-v1.tsv` に別行で記録し、worker report や Sol acceptance の
verdict に転記・統合しません。

## 初回 shard 許可条件

Sol が作成した `{RUN_DIR}/plan.md` に `IMPLEMENTATION_SHARDS` があり、各 shard に
`SHARD_ID`、目的、許可/禁止ファイル、依存 shard（なければ `none`）、成果物が
明記されている場合だけ、最大 3 件の worker job を並列にできます。

さらに Sol orchestrator は次を確認します:

- 許可ファイル集合が shard 間で重ならない。
- 共通型、API schema、migration、lockfile、生成物、golden、共有 config、
  共通 helper を複数 shard が触らない。
- shard 間の実装順序依存がなく、未確定の命名・抽象・データ形状を参照しない。
- 統合後に一つの reviewer/tester ループで全体確認できる。

条件を一つでも満たさない場合は単一の Luna Max worker job に戻します。旧 actor
名への縮退や runner の自動 fallback は使いません。全 shard の worker report、
Sol acceptance、対象 diff を統合確認してから reviewer へ進みます。

## 再実装ルール

### reviewer FAIL 後

失敗 reviewer の各レポートを読み、指摘から修正用 `task.md` / `requirements.md`
を具体化します。指摘が完全に独立し、共有契約・生成物・共通 helper に波及せず、
修正方針が一意なら最大 5 件の review-fix worker job を並列にできます。各 job は
まず Luna Max から開始し、上記の測定済み effort ladder に従います。条件を満たさない
場合は統合済み diff を対象とする単一 job にします。修正後も Sol acceptance と
同じ `REVIEWER_SET` の reviewer を再実行します。

### tester FAIL 後

原則として統合済み diff を対象とする単一の worker job に戻します。修正方針が
単一 shard に完全に閉じることを Sol が実測した場合だけ、その shard の job を
再起動できます。修正後は Sol acceptance、reviewer、tester をそれぞれ再実行し、
worker の完了報告を品質・動作判定として扱いません。

既存の `INNER_LOOP_COUNT`、`OUTER_LOOP_COUNT`、続行可能 gate、ユーザー gate、
決定論的完了検証はこのプロトコルで変更しません。
