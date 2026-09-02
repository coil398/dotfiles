---
name: "pir2"
description: "コーディングタスクを Plan → Implement → Review → Retrospect の4フェーズで実行する。複雑なタスク・設計が必要なタスク・品質保証が重要なタスク、大きな機能追加・リファクタリング・アーキテクチャ変更に使う。「ちゃんと作りたい」「しっかり実装して」「品質重視で」といった要望にも対応する。ユーザーが /pir2 と入力したら必ずこのスキルを使う。"
argument-hint: "[タスクの説明]"
---

# PIR² — Plan → Implement → Review → Retrospect

PIR² は Plan → Implement → Review → Test → Retrospect を Sol orchestrator が進める。Sol は対象リポジトリを実装せず、具体的な変更を worker-delegation job の worker に委譲する。subagent が使えない場合も、Sol は repository write を行わず blocker を記録する。並列 writer は禁止する。

**タスク**: $ARGUMENTS

---

## ステップ 1: プロジェクトメモリパスと RUN_DIR の確定

実行前に `${PROJECT_ROOT}/.codex/skills/pir2/references/worker-observability.md` と `${PROJECT_ROOT}/.codex/skills/worker-delegation/SKILL.md` を必ず Read する。前者の Phase 0/init 順序と後者の artifact root 境界を確認してから、下記 command block を実行する。続けて `${PROJECT_ROOT}/.codex/skills/pir2/references/sanitized-cwd.md` を Read し、その正規表現で `sanitized_cwd` を計算する。親 epic から起動された場合は prompt に明示された `PIR2_RUN_DIR` と `PIR2_PARENT_EPIC_RUN_DIR` の組だけを信頼し、ambient な同名環境変数で別 path を推測しない。以下の条件を満たさない path は採用しない。

- `ARTIFACT_ROOT=$HOME/.ai-pir-runs` は実体ある非 symlink directory であること（なければ `umask 077; mkdir`）。物理 path を求め、run artifact はその配下に置く。
- 親指定がある場合は絶対 path、親 directory の実体、artifact root 配下、`PIR2_PARENT_EPIC_RUN_DIR` がある場合はその配下を確認する。既存 run は空であることを確認し、なければ排他的に `mkdir` する。
- 親指定がない場合は `${ARTIFACT_ROOT}/<timestamp>-<feature>` を使い、衝突時だけ suffix を増やして `mkdir` が成功した path を `RUN_DIR` とする。既存 path、file、symlink は再利用しない。

```bash
PROJECT_ROOT="$(pwd -P)"
PROJECT_MEMORY_DIR="${HOME:?HOME is required}/.codex/projects/$(printf '%s' "$PROJECT_ROOT" | sed 's|[^a-zA-Z0-9]|-|g')/memory"
ARTIFACT_ROOT="${HOME:?HOME is required}/.ai-pir-runs"
[ -d "$HOME" ] || { echo "HOME must be a directory" >&2; exit 1; }
if [ -e "$ARTIFACT_ROOT" ] || [ -L "$ARTIFACT_ROOT" ]; then
  [ -d "$ARTIFACT_ROOT" ] && [ ! -L "$ARTIFACT_ROOT" ] || {
    echo "standard artifact root must be a real non-symlink directory: $ARTIFACT_ROOT" >&2
    exit 1
  }
else
  (umask 077; mkdir "$ARTIFACT_ROOT") || {
    echo "could not create standard artifact root: $ARTIFACT_ROOT" >&2
    exit 1
  }
fi
root_physical="$(cd -P "$ARTIFACT_ROOT" && pwd -P)" || exit 1
[ -d "$root_physical" ] && [ ! -L "$root_physical" ] || {
  echo "artifact root canonicalization did not produce a real directory: $ARTIFACT_ROOT" >&2
  exit 1
}
parent_run_dir="${PIR2_RUN_DIR:-}"; parent_epic_dir="${PIR2_PARENT_EPIC_RUN_DIR:-}"
[ -n "$parent_epic_dir" ] || parent_run_dir=''
if [ -n "$parent_run_dir" ]; then
  case "$parent_run_dir" in /*) ;; *) exit 1 ;; esac
  parent_dir="$(dirname "$parent_run_dir")"; [ -d "$parent_dir" ] && [ ! -L "$parent_dir" ] || exit 1
  parent_physical="$(cd -P "$parent_dir" && pwd -P)" || exit 1
  [ -d "$parent_physical" ] && [ ! -L "$parent_physical" ] || exit 1
  case "$parent_physical" in "$root_physical"|"$root_physical"/*) ;; *) exit 1 ;; esac
  if [ -n "$parent_epic_dir" ]; then
    [ -d "$parent_epic_dir" ] && [ ! -L "$parent_epic_dir" ] || exit 1
    epic_physical="$(cd -P "$parent_epic_dir" && pwd -P)" || exit 1
    [ -d "$epic_physical" ] && [ ! -L "$epic_physical" ] || exit 1
    case "$epic_physical" in "$root_physical"|"$root_physical"/*) ;; *) exit 1 ;; esac
    case "$parent_physical" in "$epic_physical"/*) ;; *) exit 1 ;; esac
  fi
  if [ -e "$parent_run_dir" ] || [ -L "$parent_run_dir" ]; then
    [ -d "$parent_run_dir" ] && [ ! -L "$parent_run_dir" ] || exit 1
    for child in "$parent_run_dir"/* "$parent_run_dir"/.[!.]* "$parent_run_dir"/..?*; do [ -e "$child" ] || [ -L "$child" ] || continue; exit 1; done
  else (umask 077; mkdir "$parent_run_dir") || exit 1; fi
  RUN_DIR="$parent_run_dir"
else
  run_base="${ARTIFACT_ROOT}/$(date +%Y%m%d-%H%M%S)-$(printf '%s' "$ARGUMENTS" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"; [ "${run_base##*-}" ] || run_base="${ARTIFACT_ROOT}/$(date +%Y%m%d-%H%M%S)-task"; n=0
  while :; do RUN_DIR="$run_base"; [ "$n" -eq 0 ] || RUN_DIR="${run_base}-${n}"; (umask 077; mkdir "$RUN_DIR") 2>/dev/null && break; [ -e "$RUN_DIR" ] || [ -L "$RUN_DIR" ] || exit 1; n=$((n+1)); done
fi
HANDOFF_PATH="${ARTIFACT_ROOT}/$(printf '%s' "$PROJECT_ROOT" | sed 's|[^a-zA-Z0-9]|-|g')/handoff.md"
OBS_HELPER="${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/record-observation.sh"
"$OBS_HELPER" init --run-dir "$RUN_DIR"
echo "PROJECT_ROOT=$PROJECT_ROOT" "PROJECT_MEMORY_DIR=$PROJECT_MEMORY_DIR" "ARTIFACT_ROOT=$ARTIFACT_ROOT" "RUN_DIR=$RUN_DIR" "HANDOFF_PATH=$HANDOFF_PATH"
```

`RUN_DIR` は唯一の run artifact root とし、`implementation-*`、`worker-output-*`、`sol-acceptance-*`、`review-*`、`test-*`、`user-decisions.md`、3台帳を別 path に再導出しない。以降の prompt に `PROJECT_MEMORY_DIR` と `RUN_DIR` を必ず含める。

次に `RESUME_MODE` を判定する。引継ぎ語が引数にあれば `resume`（Sol が handoff の未チェック項目だけを読み、既存 plan を上書きしない）、語がなく handoff が存在すれば `passive-notice`（通知して通常フロー）、それ以外は `new`（Sol が plan を確定した後に初期 handoff を Write）とする。retrospector 後は `${PROJECT_ROOT}/.codex/skills/pir2/references/handoff-cleanup.md` の手順で handoff を処理する。`PLAN_STRATEGY_CHANGED=false` も初期化し、ユーザーの方針切替でのみ `true` にする。

---

## ステップ 2: ブレインストーミング（状況に応じて実施）

要件が曖昧、設計選択肢が複数、または対話で設計を固める方が手戻りを減らせる場合だけ `brainstorm` を実行し、結果を Sol の計画判断に反映する。既存設計がある、タスクが明確、または関連する `docs/brainstorm/` がある場合はスキップする。完了後は自動でステップ3へ進む。ユーザー確認を挟めるのは本書が明示する既存パターン逸脱・ステップ4.6・ステップ6.5・ステップ8.2-Gだけである。

---

## ステップ 3: 探索フェーズ（explorer）

初回探索は必須。subagent が使える場合は `explorer` を最低1体、独立領域だけ最大3体まで起動し、モデルは role 定義に任せる。使えない場合は Sol が read-only で探索する。結果は必ず `{RUN_DIR}/exploration-{NN}.md` に保存し、推測と確認済み事実を分ける。

- prompt には `PROJECT_MEMORY_DIR`、`RUN_DIR`、`EXPLORATION_INDEX`、レポート path、タスク、実装・git変更禁止を含める。
- 既存パターン、再利用可能な helper、分岐ごとのフィールド、framework の自動処理、必要なら公式 docs の裏取りを調査する。
- 不明点は既存 explorer の `followup_task`（不可なら同じ role の追加起動）で調べ、追加 index は既存最大値+1。新規ライブラリ選定だけは `tech-validator` role を使う。

---

## ステップ 4: Sol によるプラン策定

Sol orchestrator が全 exploration report、brainstorm 結果（実施時）、handoff（resume 時）、対象コードを read-only で照合し、`{RUN_DIR}/plan.md` を直接作成・更新する。Sol は目標、根拠、対象ファイル、scope、依存 DAG、実装手順、検証手順、禁止範囲、`R1` から始まる requirements、必要な `IMPLEMENTATION_SHARDS`（各 shard の所有範囲・依存・成果物）を確定する。plan の内容をそのまま信頼せず、対象コードと探索結果を Read して事実を確認する。

既存の plan がある場合は未完了項目と変更対象を保持し、影響するセクションだけを増分更新する。Sol は計画・DAG・scope・requirements・implementation shards の作成と最終判断を所有し、対象リポジトリの具体実装は行わない。

既存構造から逸脱するプランは、実装前に既存 N 件中 M 件、採用構成、理由、代替案をユーザーへ提示して承認を得る。

### ステップ 4.5: 能動的再探索ループ（最大5回）

実行前に `${PROJECT_ROOT}/.codex/skills/pir2/references/exploration-loop.md` を必ず Read する。`EXPLORATION_ROUND=0` から開始し、`plan.md` の `EXPLORATION_NEEDED` に `- topic` が残る間だけ、Sol が定義した topic の追加探索と plan.md の増分更新を最大5回行う。cap到達時は最終サマリーへ topic を記録する。計画の全破棄・再生成・計画担当の再起動は行わない。

### ステップ 4.6: プラン選択肢のユーザー確認（該当時のみ）

実行前に `${PROJECT_ROOT}/.codex/skills/pir2/references/plan-choice-gate.md` を必ず Read する。「複数案」「USER_DECISION_REQUIRED」「スコープ縮小」「外部依存不足」があればステップ5前に推奨案を明示してユーザー確認を待つ。別案・方針切替なら `PLAN_STRATEGY_CHANGED=true` とし、ユーザーの選択を `plan.md` の影響する方針・scope・DAG・requirements へ増分反映する。既存計画全体を破棄・再策定せず、Auto mode でもこの確認を省略しない。

---

## ステップ 5: プラン保存

`docs/plans/` がなければ作成し、`docs/plans/YYYY-MM-DD-<feature>.md` にタスク、目標、実装チェックリスト、`{RUN_DIR}/plan.md` の設計詳細、実装ログ（変更ファイルと内容は完了後に記録）、作成日と進行中ステータスを保存する。保存 path をユーザーに提示する。確認後に削除できる記録であることを明記する。

---

## ステップ 5.5: handoff.md 初期版生成（`RESUME_MODE=new` の場合のみ）

`resume` / `passive-notice` は既存 handoff を温存してスキップする。`new` の場合は `{RUN_DIR}/plan.md` を Read し、`~/.codex/pir-handoff.md` を実行前に必ず Read して、そのフォーマットに従い `$HANDOFF_PATH` へ `最終更新`、タスク、背景・決定事項、残 TODO（`- [ ]`）、既知の問題/要確認、関連 artifact を Write する。path を提示し、passive-notice なら resume 方法も通知する。

## ステップ 5.6: 次ステップキュー初期版生成

実行前に `${PROJECT_ROOT}/.codex/skills/pir2/references/next-steps-queue.md` を必ず Read する。`{RUN_DIR}/next-steps.md` に以降の subagent 起動予定を checkbox で Write し、各ステップ完了直後に `[x]` と `<!-- done: ISO8601 -->` を付ける。ユーザー会話で中断した後は、次の判断前に必ずこのファイルを Read する。resume 時は handoff の未完了項目を統合する。

## ステップ 5.7: 破壊的変更チェックリスト + 動作変更チェック

実行前に `${PROJECT_ROOT}/.codex/skills/pir2/references/destructive-change-check.md` を必ず Read する。plan と探索 report から破壊的変更 a〜e、動作変更 f1〜f3 を独立判定し、`{RUN_DIR}/destructive-change-check.md` に記録して reviewer / refactor-advisor / tester の戦略を決める。ON時の軽量化はユーザー確認なしに行わない。

## ステップ 5.8: 直前追加 feedback の自己照合ゲート

実行前に `${PROJECT_ROOT}/.codex/skills/pir2/references/feedback-conflict-gate.md` を必ず Read する。過去14日以内の5件を実装 prompt 案と照合し、矛盾があれば実装を中断してユーザー確認、矛盾がなくても `{RUN_DIR}/feedback-conflict.md` に件数と結果を記録する。

---

## ステップ 6: 実装（worker-delegation）

実行前に次の3つを必ず Read する: `${PROJECT_ROOT}/.codex/skills/worker-delegation/SKILL.md`、`${PROJECT_ROOT}/.codex/skills/pir2/references/implementation-delegation.md`、`${PROJECT_ROOT}/.codex/skills/pir2/references/worker-observability.md`。前者が責任境界・actor ladder・runner・acceptance、後二者が PIR² の shard/effort/artifact 接続と観測をSSOTとして定義するため、本文に共通手順やCLIを複製しない。

`INNER_LOOP_COUNT=0`、`OUTER_LOOP_COUNT=0` から開始する。Sol は一時 `task.md`（目的、所有範囲、実装指示、禁止事項）と `requirements.md`（`- R<number>:` 形式で差分・ファイル・検証コマンドから判定可能）を作り、対象 repo を直接変更せず worker を起動する。初回は必ず `IMPL_INDEX=01` の Luna Max。`WORKER_RAW_OUTPUT` と `IMPLEMENTATION_REPORT_PATH` は別 artifact として毎回新しい suffix/path を使う。runner の実装・actor ladder の正規 invocation はSSOTの `${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/run-worker.sh` に委譲し、初回は `--actor luna`、`--effort max`、`--output-file "$WORKER_RAW_OUTPUT"` を使う。

PIR²固有の shard は、plan に `IMPLEMENTATION_SHARDS` があり、許可/禁止ファイル、依存、成果物が明示され、所有範囲が重ならず、共有型/API/schema/migration/lockfile/生成物/golden/config/helper に競合せず、依存順序がなく、統合後に一つの reviewer/tester で確認できる場合だけ最大3件を並列化する。条件不成立なら単一 Luna job に戻す。single / initial shard / review-fix shard / sequential unit の suffix 規則と correction 接続は implementation-delegation SSOT に従う。

worker完了後は raw → Sol canonical → deterministic gate → acceptance → reviewer → tester の順とし、rawの自己申告・runner終了だけで acceptance/PASS を作らない。reviewer/tester は worker と別系統の判定者である。各 attempt と correction は同じ契約へ戻し、actor昇格は測定済み capability/local-reasoning insufficiency がある場合だけ明示する。

### 実装 job の observability

Phase 0 は init のみ。Sol が acceptance または blocker と各 `Rn` を実測してから、SSOT の順序で `worker` を job ごとに一度、各 `Rn` の `acceptance` を一行ずつ、各 reviewer/tester report 完了後に concrete role の `verdict` を append する。未確定値を先行記録せず、generic `reviewer` 行を作らない。`JOB_ID`、`REPORT_SUFFIX`、raw/provenance/canonical は attempt ごとに固有とし、correction/shard は新しい job/index を割り当てる。`--effort-escalation-from "$EFFORT_ESCALATION_FROM"` / `--effort-escalation-to "$EFFORT_ESCALATION_TO"` を含むhelperの全引数はSSOTの実測後CLIへ委譲する。

### 完了後

ステップ5.6の checkbox 規則で実装項目を更新する。複数の `IMPL_INDEX` は初回項目を一度だけ完了にし、以後を「中断・再開ログ」に追記する。

---

## ステップ 6.1: 決定論的完了証拠ゲート（必須）

実行前に `${PROJECT_ROOT}/.codex/skills/worker-delegation/references/deterministic-completion-check.md` と `${PROJECT_ROOT}/.codex/skills/pir2/references/worker-observability.md` を必ず Read する。初回、shard、review-fix、tester FAIL 後 correction、actor昇格の全 job で、worker report 直後・Sol acceptance/reviewer/tester 前に同じ gate を実行する。

- 起動直前に `IMPL_INDEX`、`PRE_IMPL_INDEX`、job固有 `REPORT_SUFFIX`、未作成の raw/canonical path を決め、pre-set を一度保存する。runner には raw path だけを渡す。shard/unit は canonical report 全件だけを union し、raw を CLAIMED に含めない。
- worker 後は Sol が実測した変更ファイルだけを canonical report に正規化し、SSOT の post-set / delta / CLAIMED を計算する。`verify-deterministic-check.sh` で8 fixtureも検証し、判定 report と pre/post/delta path を evidence に残す。
- `PHANTOM_CLAIM` は hard fail。reviewer/tester/acceptance へ進まず、原因を渡して `IMPL_INDEX` と `PHANTOM_RETRY_COUNT` を更新した一度だけの correction に戻す。二度目も解消しなければユーザーゲートで停止し、自動巻き戻しをしない。`UNDECLARED_CHANGE` は warn として実差分を確認する。
- gate PASS 後、Sol は各 `Rn` を差分・要求コマンド・verifier output で測定して acceptance evidence を作る。worker/acceptance/verdict の append、sidecar の実測 identity、append-only ledger、attempt の固有性は observability SSOTの順序を使い、本文でCLIを再実装しない。

完了後は next-steps の deterministic 項目を更新する。最終 verifier の実行は `bash "${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/verify-deterministic-check.sh"` とする。

---

## ステップ 6.5: worker の未解決事項ユーザー確認（該当時のみ）

`{RUN_DIR}/implementation-{最新}.md` の `### 注意点・未解決事項` を Read し、worker要約が「あり」なら必ず停止してユーザーへ `(A) スコープ縮小を承認してレビューへ`、`(B) 影響する plan の implementation path だけを増分更新`、`(C) 追加指示で worker 再実装` を提示する。Sol が仕様変更・scope縮小を独断しない。選択と理由を `{RUN_DIR}/user-decisions.md` に記録し、Aは繰越しを plan に追記、Bは該当セクション・requirements・必要な shard だけを更新、Cは `IMPL_INDEX++` で同じ actor ladder に戻る。計画全体の再策定や先頭への巻き戻しは行わない。「なし」ならスキップする。完了またはスキップ後は next-steps を更新する。

---

## ステップ 7: レビューループ（reviewer ハイブリッド並列、最大3回）

実行前に `${PROJECT_ROOT}/.codex/skills/pir2/references/fan-out-gate.md` を必ず Read する。

### 7-1: 観点セット

`--reviewers=<roles>` があれば未知 role を除いて採用し、`--all-reviewers` は全5観点、両方なら `--reviewers=` を優先する。未指定の `REVIEWER_SET` は `[correctness, consistency, quality, security, architecture]` 固定。フラグを除いた文字列をタスク説明として扱い、集合を最終サマリーに記録する。

### 7-2: Fan-Out Gate とレビュー実行

実行前に `${PROJECT_ROOT}/.codex/skills/pir2/references/fan-out-gate.md` を必ず Read する。同SSOTの観点 mapping、違反検出/recovery、起動パラメータに従い、reviewer 起動または read-only 複数観点レビューを開始する直前に次を本文へ出す。

> **Fan-Out Gate（reviewer）**
> - `REVIEWER_SET = [<全観点>]`
> - `起動体数 = N`（`len(REVIEWER_SET)` と一致）
> - 利用可能なら同一 collaboration block に N 個の `spawn_agent(agent_type="reviewer")`、不可なら同一 cycle に N 観点を実行
> - 逐次後追い起動、観点削減、宣言省略は違反

各 reviewer に `PROJECT_MEMORY_DIR`、`RUN_DIR`、同じ `REVIEW_INDEX`（初回=`01`）、role、plan、最新 canonical implementation report、固有 report path を渡す。review cycle の起動ごとに `REVIEW_INDEX` を増分し、モデルは role 定義に任せる。宣言と同数の全観点を同一ターンで起動し、再レビューでも同じ集合と宣言を使う。各 report と provenance を Sol が確認した後、worker/acceptance と分離した concrete role の verdict ledger に append し、起動しなかった行は捏造しない。

### 7-3: verdict と inner loop

`every reviewer in REVIEWER_SET returns PASS` で未解決 Critical/High がない場合だけ reviewer gate PASS。欠落、未報告、判定不能、non-PASS、未解決 Critical/High は FAIL とする。

FAIL 時は `INNER_LOOP_COUNT += 1`。`INNER_LOOP_COUNT >= 3` なら overall FAIL の hard stop とし、refactor-advisor、tester、または成功完了を進めない。ユーザーの判断を求める。未解決事項を報告する。上限未到達なら FAIL を返した全 report と plan を Read し、各指摘を直接根拠に影響する plan.md の検証・scope・DAG・requirements・shard を増分更新してから修正 task/requirements を作り、worker-delegation の correction（まず Luna、必要な昇格のみ）へ戻す。`IMPL_INDEX`、pre-set、suffix、canonical report を更新し、raw → canonical → deterministic → acceptance を再実行した後、PASS済み role を含む `REVIEWER_SET` の every reviewer を同じ cycle 規則で再起動する。全員 PASS まで反復する。完了後は next-steps を更新する。

---

## ステップ 7.5: リファクタ提案（refactor-advisor → ゲート → 任意適用）

実行前に `${PROJECT_ROOT}/.codex/skills/pir2/references/refactor-advisor-gate.md` を必ず Read する。reviewer 全員 PASS、Critical/High 解消後にだけ refactor-advisor を一体・一回だけ起動する。提案がある場合のみ `all` / 番号指定 / `none` / `custom` のユーザーゲートを開き、適用は workerへ委譲する。適用後は Fan-Out Gate を通して全 reviewer を再実行し、FAIL は `INNER_LOOP_COUNT` 継続でステップ7-3へ戻す。retry-cap hard stop から本ステップへ入らない。完了後は next-steps を更新する。

---

## ステップ 8: テストループ（tester、最大3回）

### 8-1: tester 起動

reviewer gate PASS（every reviewer PASS、Critical/Highなし）の後だけ tester を起動する。実行前に `${PROJECT_ROOT}/.codex/skills/pir2/references/tester-prompt.md` を必ず Read し、plan の最小テストと destructive/dynamic flags から `TEST_SCOPE` を組み立てる。利用可能なら `spawn_agent(agent_type="tester")` を使い、OFF/OFF の tester skip は同SSOTに従いユーザー確認を取る。他の組合せでは、同SSOTの scope・report・cleanup 制約に従う。`TEST_INDEX=01` から開始し、再テストごとに増分する。tester には `PROJECT_MEMORY_DIR`、`RUN_DIR`、plan、最新 canonical report、TEST_SCOPE、`{RUN_DIR}/test-${TEST_INDEX}.md` path を渡し、モデルは role 定義に任せる。tester report と実行 provenance 確認後にのみ独立 verdict を append する。

### 8-2: verdict と outer loop

`VERDICT: PASS` のみステップ9へ進む。FAIL 時は次の順序を厳守する。

1. `OUTER_LOOP_COUNT += 1`。
2. `OUTER_LOOP_COUNT >= 3` なら、worker correction、`task.md` / `requirements.md` の作成、または次の tester の起動より先に、
   8-2-G へ直ちに分岐する。上限判定前に correction を開始してはいけない。
3. `OUTER_LOOP_COUNT < 3` の場合だけ `INNER_LOOP_COUNT=0` に戻し、`IMPL_INDEX++`、最新 test report の Read、影響する plan.md の検証・scope・requirements・shard の増分更新、修正 task/requirements の作成を行う。上限未満のときだけ `worker correction` → deterministic gate → Sol acceptance → ステップ7で `REVIEWER_SET` の every reviewer（PASS済みも含む）→ tester再起動（`TEST_INDEX++`）の順に繰り返す。workerの完了報告は tester verdict ではない。計画全体を再策定せず、必要な箇所だけを更新する。

### 8-2-G: 続行可能ゲート（`OUTER_LOOP_COUNT` 上限到達時のみ）

実行前に `${PROJECT_ROOT}/.codex/skills/pir2/references/continuation-gate.md` を必ず Read し、`OUTER_LOOP_COUNT >= 3` 到達時は自動で続行しない。4条件が全て満たされる場合だけユーザーへ Y/N gate を出す。Y は4条件が全て成立した場合だけ許可し、`OUTER_LOOP_COUNT=4` として worker correction → deterministic gate → acceptance → 全 reviewer → tester の一周だけ追加する。N、4条件の不足、または追加周回後の tester FAIL は overall FAIL の hard stop とし、追加 correction を作らず、成功完了・ステップ9の walkthrough・ステップ11の retrospect へ進めない。tester PASSなしに成功扱いせず、1 cycle で gate を通過できるのは一回だけ。完了後は next-steps を更新する。

---

## ステップ 9: ウォークスルー生成（read-only）

実行前に `${PROJECT_ROOT}/.codex/skills/pir2/references/walkthrough-templates.md` を必ず Read する。変更ファイルを実際に Read し、フル版を実装記録の実装ログへ、サマリー版を最終サマリーへ作る。引用は Read 済みコードだけにする。完了後は next-steps を更新する。

## ステップ 10: メモリへの記録

`mkdir -p "$PROJECT_MEMORY_DIR"` の後、`$PROJECT_MEMORY_DIR/pir_skill_log.md` に `## [タスク名] — [気づき・課題・パターン]` を追記する。実行形態スイープ用に、実測した explorer/worker/reviewer/tester/retrospector の model・体数、`EXPLORATION_ROUND`、`INNER_LOOP`、`OUTER_LOOP` を固定 prefix で記録し、worker は actor:model:effort、未使用 Sol worker は `none` とする。完了後は next-steps を更新する。

## ステップ 11: 振り返り（retrospector、常に実行）

実行前に `${PROJECT_ROOT}/.codex/skills/pir2/references/retrospector-prompt.md` を必ず Read する。小規模または subagent 不可なら Sol が行い、分離価値がある場合だけ `retrospector` role を起動する。`PROJECT_MEMORY_DIR`、`PROJECT_ROOT`、`RUN_DIR`、`META_MODE=false`、`INNER_LOOP_COUNT`、`OUTER_LOOP_COUNT`、`EXPLORATION_ROUND`、`PLAN_STRATEGY_CHANGED`、experimental/worker-observability SSOT、3 TSV、review/test report path、最終 verdict、`ワークフロー種別: pir2` を渡す。TSVのschema/actor/acceptance/verdict 行は編集せず、メタ改善推奨があれば最終サマリーへ転記して `/retro --meta` の判断をユーザーに委ねる。完了後は next-steps を更新する。

## ステップ 11.5: handoff.md 完了判定と後処理

実行前に `${PROJECT_ROOT}/.codex/skills/pir2/references/handoff-cleanup.md` を必ず Read する。`$HANDOFF_PATH` が存在する場合のみ、全 TODO が `[x]` なら削除し、残項目があれば最終更新行を更新する。結果を最終サマリーに記載する。存在しなければスキップし、完了後は next-steps を更新する。

## ステップ 12: 最終サマリーの提示

実行前に `${PROJECT_ROOT}/.codex/skills/pir2/references/final-summary-template.md` を必ず Read する。タスク、実装記録、変更ファイル、レビュー結果と `INNER_LOOP_COUNT`、refactor-advisor 提案/適用、tester verdict と `OUTER_LOOP_COUNT`、`EXPLORATION_ROUND`、RUN_DIR、retrospector、メタ改善推奨をテンプレートどおり提示する。next-steps 全項目完了ならその旨を記載する。

## ステップ 13: ウォークスルーの提示

ステップ9のサマリー版を提示し、フル版は内部記録として保持する。詳細を求められた場合だけフル版を提示し、末尾に「詳細なウォークスルーが必要な場合はお知らせください。」と添える。
