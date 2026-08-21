---
name: "instruction-refactor"
description: "既存の CLAUDE.md / agents / skills の肥大化を Anthropic 公式基準（SKILL.md ≤ 500 行、bloat warning）と構造的悪さ（責務越境 / SSOT 逸脱 / DRY 違反 / 二重説明）の観点で検出し、Progressive Disclosure / 共通骨格の references 外出し / SSOT 参照への置換などで実際に整理する（検出だけで終わらない）。「instruction file 整理」「肥大化リファクタ」「skill の長さ大丈夫？」「定期メンテ」「棚卸し」「audit」「instruction bloat」「.codex/ 整理」「CLAUDE.md 削って」といった要望や、agents / skills を編集して肥大化・重複・SSOT 逸脱が気になったときの整合性確認にも使う。コードのリファクタ提案を出す refactor-advisor とは対象が違う（こちらは instruction file 専用、向こうはソースコード専用）。ユーザーがこれらに該当することを明示的に名指ししなくても積極的に使う。ユーザーが /instruction-refactor と入力したら必ずこのスキルを使う。"
argument-hint: "[--scope=user|project|all] [--no-implement] [path]"
---

# Instruction Refactor — instruction file 肥大化リファクタリング

CLAUDE.md / agents/*.md / skills/**/SKILL.md を **Anthropic 公式基準** と **構造的悪さ**（責務越境 / SSOT 逸脱 / DRY 違反 / 二重説明）の観点で検出し、Progressive Disclosure / 共通骨格の references 外出し / SSOT 参照への置換などで実際に整理します。**検出だけで終わらせず、改善実施までを 1 セットとするスキル** です。

> ℹ️ コードのリファクタ提案を出す `refactor-advisor` とは対象が違います（こちらは instruction file 専用、向こうはソースコード専用）。

このスキル本体（= Sol orchestrator）はオーケストレーターです。`explorer` role を `spawn_agent`（`agent_type="explorer"`）で起動して測定・分析し、対象範囲、整理方針、task/requirements、acceptance の実測と最終判断を Sol が所有します。モデル引数は指定せず `.codex/agents/explorer.toml` の role 定義に委ねます。具体的なリポジトリ変更は `.codex/skills/worker-delegation/SKILL.md` の共通契約へ委譲し、既定の Luna Max worker から開始します。Terra High は、十分な入力を与えた Luna の capability または local-reasoning insufficiency を Sol が実測した場合だけ明示的に起動し、Terra Max は許可された複雑性・リスク証拠がある場合に一度だけ許可します。Terra の測定済み不足後だけ Sol High worker、highest-complexity/high-risk evidence または documented Sol High insufficiency がある場合だけ Sol Max worker を明示起動します。Sol orchestrator は対象リポジトリを実装・修正しません。reviewer / tester の品質・動作判定は worker とは別系統です。

判断基準・整理戦略・公式引用は `references/` 配下にオンデマンドで切り出してあり、SKILL.md 本体は薄く保つ設計です。

## ステップ 0: run-state の初期化（全ステップより先に実行）

最初に次の Bash ブロックを **そのまま実行**し、この run の状態を確定してください。`PROJECT_ROOT` と
`sanitized_cwd` は `${PROJECT_ROOT}/.codex/skills/pir2/references/sanitized-cwd.md` の正規表現 SSOT
（`[^a-zA-Z0-9]` を `-` に置換）から導出します。`RUN_DIR` と以下の artifact は orchestration state であり、
リポジトリ実装や変更ファイルの申告集合ではありません。

```bash
ARGS="${ARGUMENTS-}"
PROJECT_ROOT="$(pwd -P)"
if git -C "$PROJECT_ROOT" rev-parse --show-toplevel >/dev/null 2>&1; then
  PROJECT_ROOT="$(git -C "$PROJECT_ROOT" rev-parse --show-toplevel)"
  PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd -P)"
fi
# sanitized-cwd 計算は ${PROJECT_ROOT}/.codex/skills/pir2/references/sanitized-cwd.md を SSOT とする
sanitized_cwd="$(printf '%s' "$PROJECT_ROOT" | sed 's|[^a-zA-Z0-9]|-|g')"
PROJECT_MEMORY_DIR="${HOME}/.codex/projects/${sanitized_cwd}/memory"
run_ts="$(date +%Y%m%d-%H%M%S)"
run_feature="$(printf '%s' "$ARGS" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
[ -z "$run_feature" ] && run_feature="instruction-refactor"
RUN_ROOT="${HOME}/.ai-pir-runs/${sanitized_cwd}"
mkdir -p "$RUN_ROOT"
RUN_PREFIX="${RUN_ROOT}/${run_ts}-${run_feature}"
RUN_DIR="$RUN_PREFIX"
RUN_COLLISION=0
while ! mkdir "$RUN_DIR" 2>/dev/null; do
  RUN_COLLISION=$((RUN_COLLISION + 1))
  RUN_DIR="${RUN_PREFIX}-${RUN_COLLISION}"
done

# 0 は未起動を表す。worker/reviewer/tester を起動するたびに対応する index を増分する。
IMPL_INDEX="00"
REVIEW_INDEX="00"
TEST_INDEX="00"
CORRECTION_COUNT=0
PHANTOM_RETRY_COUNT=0
REVIEW_RETRY_COUNT=0
TEST_RETRY_COUNT=0
REVIEWER_ROLE="pending"

REPORT_SUFFIX="$IMPL_INDEX"
WORKER_RAW_OUTPUT="${RUN_DIR}/worker-output-${REPORT_SUFFIX}.md"
IMPLEMENTATION_REPORT_PATH="${RUN_DIR}/implementation-${REPORT_SUFFIX}.md"
VERIFY_REPORT_PATH="${RUN_DIR}/verify-${IMPL_INDEX}.md"
REVIEW_REPORT_PATH="${RUN_DIR}/review-${REVIEW_INDEX}-${REVIEWER_ROLE}.md"
TEST_REPORT_PATH="${RUN_DIR}/test-${TEST_INDEX}.md"

echo "PROJECT_ROOT=$PROJECT_ROOT"
echo "PROJECT_MEMORY_DIR=$PROJECT_MEMORY_DIR"
echo "RUN_DIR=$RUN_DIR"
echo "IMPL_INDEX=$IMPL_INDEX"
echo "REVIEW_INDEX=$REVIEW_INDEX"
echo "TEST_INDEX=$TEST_INDEX"
```

### 共通 observability（Phase 0 では初期化だけ）

Phase 0 では `${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/record-observation.sh` を `OBS_HELPER` に束縛し、台帳の `init` だけを worker 起動前に一度実行する。worker / acceptance / verdict の値はこの段階では未確定なので、ここで append してはいけない。具体的な CLI と固定 TSV header は `pir2/references/worker-observability.md` を SSOT とする。

```sh
OBS_HELPER="${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/record-observation.sh"
"$OBS_HELPER" init --run-dir "$RUN_DIR"
```

`RUN_DIR` は PID/時刻の推測ではなく `mkdir` の排他的作成ループで一意化します。以降の各 worker launch では
`IMPL_INDEX` と `PRE_IMPL_INDEX` を固定してから `WORKER_RAW_OUTPUT` を新しいパスへ更新し、worker が返す自由形式の
raw output を読むのは Sol だけです。Sol は実測した変更ファイルだけを `IMPLEMENTATION_REPORT_PATH`
（`implementation-${REPORT_SUFFIX}.md`）へ canonical report として正規化します。reviewer cycle の launch ごとに
`REVIEW_INDEX` を増分して `REVIEWER_ROLE` を設定し、`REVIEW_REPORT_PATH` を確定します。tester launch ごとに
`TEST_INDEX` を増分して `TEST_REPORT_PATH` を確定します。PHANTOM、reviewer FAIL、tester FAIL の correction では
`CORRECTION_COUNT` と該当 retry counter を増分し、実装 job の再起動前に必ず新しい `IMPL_INDEX` を割り当てます。

引数: $ARGUMENTS

---

## ステップ 1: 引数解釈

`$ARGUMENTS` を bash で解釈し、スコープ・実装フラグ・対象パスを分離してください:

```bash
ARGS="$ARGUMENTS"
SCOPE="user"
IMPLEMENT="true"
TARGET_PATH=""

for token in $ARGS; do
  case "$token" in
    --scope=*) SCOPE="${token#--scope=}" ;;
    --no-implement) IMPLEMENT="false" ;;
    --user) SCOPE="user" ;;
    --project) SCOPE="project" ;;
    --all) SCOPE="all" ;;
    *)
      if [ -z "$TARGET_PATH" ]; then
        TARGET_PATH="$token"
      else
        echo "⚠️ パスは1つだけ対象にします。無視: $token" >&2
      fi
      ;;
  esac
done

echo "SCOPE=$SCOPE"
echo "IMPLEMENT=$IMPLEMENT"
echo "TARGET_PATH=${TARGET_PATH:-（指定なし、SCOPE 全体を対象）}"
```

スコープのデフォルトはユーザースコープ（`~/.codex/` 配下）。プロジェクト固有の `.codex/` 配下を含めたい場合は `--scope=project` または `--scope=all` を指定する。短縮形 `--user` / `--project` / `--all` も `--scope=` と等価。位置引数のパスは **1 つだけ**対象になる（2 つ目以降は警告して無視）。

---

## ステップ 2: 対象ファイルの探索と測定（公式定量基準の照合）

`explorer` role を `spawn_agent`（`agent_type="explorer"`）で起動して測定を委譲してください。モデル引数は指定せず、`.codex/agents/explorer.toml` の role 定義に委ねます。構造列挙が中心なので 1 体を基本とし、user / project の対象を独立分割できる場合だけ最大 3 体まで並列起動します:

- **プロンプトに含めるパラメータ**:
  - `SCOPE`（user / project / all）
  - `TARGET_PATH`（指定があれば、ない場合はスコープ全体）
  - 「以下を測定してレポートを返してください:
    1. SCOPE に応じた対象ファイルを Glob で列挙する
       - `user`: `~/.codex/AGENTS.md`, `~/.codex/agents/*.toml`, `~/.agents/skills/**/SKILL.md`
       - `project`: `${PWD}/.codex/AGENTS.md`, `${PWD}/.codex/agents/**/*.toml`, `${PWD}/.agents/skills/**/SKILL.md`
       - `all`: 両方
    2. 各ファイルの行数を `wc -l` で計測
    3. 各 SKILL.md の `description` 文字数を計測
    4. 公式定量基準・スキーマ制約の違反を検出（SKILL.md > 500 行 / description > 1,024 文字 = ロード不可 / description + when_to_use > 1,536 文字 = listing 切り捨て / name > 64 文字 / name と親ディレクトリ名の不一致 = ロード不可）
    5. 平均からの外れ値を検出（同種ファイルの中央値 × 3 以上を外れ値とみなす）
    6. 計測結果を表形式で返す」
  - 「判断基準は `~/.codex/skills/instruction-refactor/references/official-criteria.md` を Read して使うこと」

> ⚠️ **定量ゲートが 0 件でもステップ 3 は必ず実行する**: 公式上限超過・外れ値（サイズ）と構造的悪さ（DRY / SSOT 逸脱 / 責務越境 / 二重説明）は **直交する** 軸であり、サイズ基準内のコンパクトなファイルにも構造的悪さは潜む（例: 150 行の agent が CLAUDE.md の節を逐語コピーしている＝ SSOT 逸脱 / DRY）。したがってサイズ違反が 0 件でも構造判定（ステップ 3）をスキップしてはならない。ステップ 5・6 をスキップするのは **ステップ 2（定量）とステップ 3（構造）の両方が 0 件**のときだけ。

---

## ステップ 3: 構造的悪さの判定（責務越境 / SSOT 逸脱 / DRY 違反 / 二重説明）

構造判定は **対象ファイル全件**を入力にする（ステップ 2 でサイズ違反だったファイルに限定しない。両ゲートは直交するため）。`explorer` role を再度 `spawn_agent` で起動して構造的悪さを判定してください。既存の測定担当を継続できる場合は `followup_task` を使い、継続できない場合だけ新しい `spawn_agent` を起動します。モデル引数は指定せず、`.codex/agents/explorer.toml` に委ねます。全件の pairwise 比較と意味理解が必要なため、深い読解の explorer は 1 体に限定します:

- **入力スコープ**: SCOPE / TARGET_PATH が示す対象ファイル全件。特に **DRY 違反（判定 2c）はファイル横断の pairwise 比較が前提**なので全件を渡す。逐語読解のコストが問題になる規模では、ステップ 2 のサイズ降順で読解優先度を付けてよいが、**全件を対象から外さない**（コスト最適化のために構造軸を取りこぼさないこと）
- **プロンプトに含めるパラメータ**:
  - 対象ファイルの絶対パス一覧（ステップ 2 で Glob した**全件**。サイズ違反だけに絞らない）
  - 「`~/.codex/skills/instruction-refactor/references/checklist.md` の判定 2（責務越境 / SSOT 逸脱 / DRY 違反 / 二重説明）と判定 3（description 適切性）と判定 4（グローバル汎用性）に従い、各ファイルの構造的悪さを検出してください。検出した場合は『該当箇所の行範囲』『種別』『理由』『推奨整理戦略』を報告してください」
  - 「整理戦略の詳細は `~/.codex/skills/instruction-refactor/references/strategies.md` を参照すること」
  - SCOPE に応じた SSOT ファイル一覧を渡す（例: `/skill-creator` の SKILL.md / `~/.codex/agents/reviewer.toml` / `~/.codex/AGENTS.md` 等。判定 2b の SSOT 逸脱検出に使う）

DRY 違反を疑う場合は、対象ファイル群を pairwise で比較して連続 5 行以上の重複を検出するよう指示する。

**判定 4（グローバル汎用性）は構造読解の副産物にしない**。explorer に「対象ファイル**全件**への独立した固有名 grep スイープを行い、候補語を `~/.codex/history.jsonl` / `~/.codex/memories/*/memory/` と cross-reference して generic な一般ツールと project-specific leak を実プロジェクト照合で区別する」よう明示する（checklist.md 判定 4 の 2 段階手順）。`make <固有ターゲット>` / `[a-z]+_id` / 具体 ORM 名 / ドメイン固有名詞 を見落とさないこと。**リファクタ適用後は候補語パターンを全件へ再 grep し残存ゼロを機械確認する**（部分スイープの取りこぼし防止）。

**`TARGET_PATH` に単一ファイルが指定された場合**は、判定 2d を「意味的重複クラスタリング」として重点実行するよう explorer に指示する: 「対象ファイルを通読し、意味的に重複する段落 / ルール / 手順をクラスタにグルーピングし、各クラスタについて『重複箇所の行範囲一覧』『各箇所の固有差分の有無』『統合先の推奨』を報告してください。字句一致だけでなく言い換え・パラフレーズによる重複も拾うこと」。これは単一ドキュメントを加筆し続けて生じた重複の正規化（戦略 6）が目的。

---

## ステップ 4: ユーザーへのレポート提示

以下のフォーマットでレポートを表示してください:

```
## Instruction Refactor レポート

### スコープ
[user / project / all]、対象 N ファイル

### 公式上限超過・スキーマ違反（判定 1）
- [ファイルパス]: N 行（公式上限 500 行を X% 超過）
- [ファイルパス]: description M 文字（フィールド上限 1,024 文字を超過 = ロード不可 / または listing truncate 1,536 文字を超過）
- [ファイルパス]: name が親ディレクトリ名と不一致（`<name>` vs `<dir>` = ロード不可）
（なければ「なし」）

### 平均外れ値（判定 1 派生）
- [ファイルパス]: N 行（同種ファイル中央値の M 倍）
（なければ「なし」）

### 構造的悪さ（判定 2）
- [ファイルパス] L[行範囲]: 種別 = 責務越境 / 理由: [...] / 推奨戦略: [...]
- [ファイルパス] L[行範囲]: 種別 = SSOT 逸脱（参照先: [SSOT パス]） / 理由: [...]
- [ファイル A] と [ファイル B] L[行範囲]: 種別 = DRY 違反 / 重複行数: N / 推奨戦略: [...]
- [ファイルパス]: 種別 = 意味的重複クラスタ / 重複箇所: L[範囲1], L[範囲2], … / 固有差分: あり/なし / 統合先: L[範囲] / 推奨戦略: 戦略 6
（なければ「なし」）

### description / name 不適切（判定 3）
- [ファイルパス]: pushy パターン未準拠（自然言語トリガー語句が N 個、推奨 3〜5）
（なければ「なし」）

### グローバル汎用性違反（判定 4、ユーザースコープのみ）
- [ファイルパス] L[行]: プロジェクト固有名 `<名前>` を検出
（なければ「なし」）

### 推奨整理戦略
[戦略選択フローチャートに従い、優先度順に提示。strategies.md 参照]
```

---

## ステップ 5: 改善ゲート（IMPLEMENT=true の場合のみ）

`IMPLEMENT=false`（`--no-implement` 指定）の場合はステップ 5・6 をスキップしてレポートのみで終了する。

`IMPLEMENT=true` の場合、ユーザーに以下の選択肢を提示して応答を待つ:

```
検出の結果、N 件の改善候補があります。どう進めますか？

- all: すべての候補を改善する
- 1,3,5: 番号指定で部分改善
- none: 改善せずレポートのみで終了
- pir2: 改善作業を /pir2 で進める（5 ファイル以上の影響なら推奨）
```

---

## ステップ 6: 改善実施（all / 番号指定の場合のみ）

`pir2` が選ばれた場合は `Skill` ツールで `pir2` を起動し、本スキルでの実施は終了する。

`all` または番号指定の場合も、Sol orchestrator はリポジトリ変更を適用しません。Sol が選択候補を具体的な `task.md` と、ファイル・差分・検証コマンドで判定できる `R1...Rn` の `requirements.md` に落とし込み、`.codex/skills/worker-delegation/SKILL.md` の委譲契約へ渡します。task/requirements と run の記録は非リポジトリのオーケストレーション成果物として Sol が管理し、具体的なリポジトリ変更は worker の責務です。

既定の実装試行は Luna Max です:

```sh
IMPL_INDEX="$(printf '%02d' "$((10#$IMPL_INDEX + 1))")"
PRE_IMPL_INDEX="$IMPL_INDEX"
REPORT_SUFFIX="$IMPL_INDEX"
WORKER_RAW_OUTPUT="${RUN_DIR}/worker-output-${REPORT_SUFFIX}.md"
IMPLEMENTATION_REPORT_PATH="${RUN_DIR}/implementation-${REPORT_SUFFIX}.md"
VERIFY_REPORT_PATH="${RUN_DIR}/verify-${IMPL_INDEX}.md"
.codex/skills/worker-delegation/scripts/run-worker.sh \
  --actor luna --effort max \
  --cwd "$PROJECT_ROOT" \
  --task-file <task.md> \
  --requirements-file <requirements.md> \
  --output-file "$WORKER_RAW_OUTPUT"
```

worker の raw output（`$WORKER_RAW_OUTPUT`）や runner の終了コードだけを acceptance とみなさず、Sol が raw output を Read して実測した変更ファイルだけを `$IMPLEMENTATION_REPORT_PATH`（`implementation-${REPORT_SUFFIX}.md`）へ正規化します。`$WORKER_RAW_OUTPUT` は各 launch で新しいパスにし、deterministic gate の CLAIMED 抽出元は canonical report だけに限定します。Sol は `git status -sb`、対象 diff、変更ファイル、各 `Rn` の検証コマンド出力を実測します。入力不足、requirements、environment、permission、external/CLI failure は Terra/Sol の effort を上げる理由にならず、`automatic_fallback=no` で不足を解消するか blocker としてユーザーへ戻します。task/requirements が十分で Luna の capability または local-reasoning insufficiency を実測できた場合だけ、その根拠を記録して同じ契約を `--actor terra --effort high` で明示的に再実行します。Terra High の同じ原因への Max は multi-stage causality、design contradiction、cross-module invariants、security/data-integrity risk、または documented High insufficiency がある場合に一度だけ許可します。Terra の測定済み capability/local-reasoning insufficiency の場合だけ、Sol worker subagent を `--actor sol --effort high` で明示起動します。Sol High の同じ原因への Max は highest-complexity/high-risk evidence または documented Sol High insufficiency がある場合に一度だけ許可します。全段は条件付きであり、Sol orchestrator は対象リポジトリを実装・修正しません。

### 6-1. 決定論的完了ゲート（worker report 直後）

ここでいう **pre-set** は worker 起動直前の基準スナップショットです。

実装を選択した場合、初回 worker と reviewer/tester FAIL 後のすべての correction で、起動直前に `PRE_IMPL_INDEX="$IMPL_INDEX"` を記録し、`VERIFY_REPORT_PATH="${RUN_DIR}/verify-${IMPL_INDEX}.md"`、`VERIFY_PRE_PATH="${RUN_DIR}/verify-${PRE_IMPL_INDEX}-pre.list"`、`VERIFY_POST_PATH="${RUN_DIR}/verify-${IMPL_INDEX}-post.list"`、`VERIFY_DELTA_PATH="${RUN_DIR}/verify-${IMPL_INDEX}-delta.list"` を確定します。worker report 直後（Sol acceptance、reviewer、tester の前）に共通 SSOT `${PROJECT_ROOT}/.codex/skills/worker-delegation/references/deterministic-completion-check.md` の post-set / delta / CLAIMED 手順を実行します。`bash "${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/verify-deterministic-check.sh"` で8 fixtureを検証し、`$VERIFY_REPORT_PATH` と pre/post/delta の paths を acceptance evidence に保存します。instruction-refactor 固有の `IMPL_INDEX` / `REVIEW_INDEX` / `TEST_INDEX` と correction/retry counters だけを追加記録し、共通 protocol 本文は複製しません。

`PHANTOM_CLAIM` は hard fail です。`PHANTOM_RETRY_COUNT` が上限未満なら `PHANTOM_RETRY_COUNT` と `CORRECTION_COUNT` を増分し、`IMPL_INDEX` を増分して acceptance、reviewer、testerへ進まず、verifier path と原因を含む correction task/requirements を同じ Luna-first actor ladder に戻します。上限到達時は overall FAIL の hard stop としてユーザー判断を待ちます。`UNDECLARED_CHANGE` は warn として Sol が実差分を確認します。`--no-implement` はレポートのみで終了し、実装成功とは扱いません。

### 6-1A. observability の実イベント（各 concrete job / correction / shard）

各 worker job の raw → canonical → deterministic gate の後、Sol が acceptance または blocker と
`Rn` ごとの測定を確定した直後に、job ごとの実測値を束縛して `worker` を一度だけ append します。
`JOB_ID`、`WORKER_STATUS`、`SOL_MEASUREMENT_RESULT`、`MISMATCH_RESULT` は未確定値のまま Phase 0
に置かず、Sol が実測した enum 値をここで設定します。correction / shard では新しい job/index と
raw/provenance/canonical artifact を使います。

```sh
JOB_ID="instruction-refactor-${REPORT_SUFFIX}"
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

各 `Rn` の Sol 実測直後に acceptance 行を append し、全 reviewer report 完了直後は concrete role
と同じ cycle index、tester report 完了直後は `tester` role を渡します。generic `reviewer` role は
使いません。

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

### 6-2. 品質・動作ゲート（実装を選択した場合に必須）

deterministic gate PASS と Sol acceptance の後、`REVIEWER_SET`（デフォルトは correctness / consistency / quality / security / architecture、ユーザー指定時も選択集合を固定）の **every reviewer が `VERDICT: PASS`** になるまで完了へ進みません。reviewer cycle の launch ごとに `REVIEW_INDEX="$(printf '%02d' "$((10#$REVIEW_INDEX + 1))")"` とし、各 `REVIEWER_ROLE` を設定して `REVIEW_REPORT_PATH="${RUN_DIR}/review-${REVIEW_INDEX}-${REVIEWER_ROLE}.md"` を確定してから、`spawn_agent(agent_type="reviewer")` で起動します。1 roleでも non-PASS、未報告、判定不能、Critical / High 未解決なら `REVIEW_RETRY_COUNT` と `CORRECTION_COUNT` を増分して correction task/requirements を作り、`IMPL_INDEX` を増分した同じ Luna-first actor ladder → deterministic gate → Sol acceptance → **以前に PASS だった role を含む every reviewer** の再レビューを行います。reviewer retry cap 到達時は overall FAIL の hard stop とし、ユーザー判断を待ちます。

reviewer gate が PASS の後、別系統の `spawn_agent(agent_type="tester")` を必ず起動します。`TEST_INDEX="$(printf '%02d' "$((10#$TEST_INDEX + 1))")"` とし、`TEST_REPORT_PATH="${RUN_DIR}/test-${TEST_INDEX}.md"` を確定してから、`.codex/agents/tester.toml`、`RUN_DIR`、最新 implementation report（`IMPLEMENTATION_REPORT_PATH`）、対象 scope を渡し、`$TEST_REPORT_PATH` に**実際の静的・構文・設定・runtime 検証**を書き出します。documentation/config-only の変更にも適切な validation を適用し、tester を省略しません。tester `VERDICT: FAIL` は `TEST_RETRY_COUNT += 1` として correction worker → deterministic gate → acceptance → 全 reviewer 再実行 → tester 再実行へ戻し、`CORRECTION_COUNT` と `IMPL_INDEX` を増分します。cap（3回）到達時は overall FAIL / ユーザー判断の hard stop とします。tester PASS のときだけ実装成功として最終サマリーへ進みます。

> ⚠️ **実行前に必ず性能保全ゲートを通す**: 各候補を `references/strategies.md` の「性能保全ゲート」に通し、**subagent の運用指示（クエリ・出力テンプレ・必須チェック手順）の外出し**や **消費側が読まない SSOT 複写の prune** で性能が落ちる候補を除外する。行数を最も減らせる候補が最も性能を下げる候補と一致しやすいため、削減量ではなく配達経路の保全で採否を決める。除外した候補は「性能保全のため見送り」とラベルしてサマリーに残す。

ゲートを通った候補に整理戦略を適用する。**問題種別 → 戦略の対応は `references/strategies.md` の「戦略選択フローチャート」が SSOT**（齟齬時はそちらを正とする）。要点: 公式超過・DRY → 戦略 2／SSOT 逸脱・責務越境 → 戦略 1／二重説明・意味的重複 → 戦略 6（和集合統合 + **情報点包含チェック** + diff 提示、要約・圧縮はしない）／description 不適切 → `/skill-creator` の Description Optimization 提案／プロジェクト固有名混入 → スコープ移動か参照化。

実施後、変更前後の行数を比較してサマリーをユーザーに提示:

```
## Instruction Refactor 完了サマリー

### 変更ファイル
- [ファイルパス]: Before X 行 → After Y 行（Z 行削減）

### 新規 references/
- [ファイルパス]: N 行

### 達成した整理
- 公式 500 行ライン: N ファイル超過 → M ファイル超過
- DRY 違反: N 箇所 → 0
- SSOT 逸脱: N 件 → 0

### 次のステップ
- git commit で変更を保存（個別 git add でファイルを指定）
- /skill-creator の Description Optimization が必要な skill: ...
- (5 ファイル以上に影響した場合): /pir2 でレビューを通すことを検討
```

---

## 注意事項

- **CORE セクションは触らない**: `agents/*.md` の `<!-- CORE -->` で囲まれたセクションは変更禁止（retrospector のメタモードでもユーザー承認が必要)
- **削除する前に SSOT が存在することを確認**: 抜粋を消す前に、参照先 SSOT を Read して同等以上の情報があることを必ず確認
- **削除する前に「消費側が SSOT を読む」ことを確認（性能保全）**: SSOT が存在するだけでは不十分。その内容を使う agent が当該 SSOT を実際に Read する手順を持つかを grep で確認する。読まないなら inline が唯一の配達経路なので prune しない。詳細は `references/strategies.md` の「性能保全ゲート」
- **Dead Code 削除の後は同一ファイル全体を grep で残存確認**: dead code（互換ブロック等）を削除したら、削除キーワードを `grep -n <キーワード> <file>` で同一ファイル全体に残存確認する。入力セクションを消しても返り値テンプレ・プロセス手順・出力フォーマットに残骸が残りやすく、複数イテレーションを要しやすい。残存ゼロを機械確認して削除完了とする。詳細は `references/strategies.md` 戦略 5
- **大きな構造変更は `/pir2` へ**: 5 ファイル以上に影響する大規模リファクタは独断せず `/pir2` 経由でレビューを通す
- **本スキル自身もリファクタ対象**: SKILL.md と `references/` も他の skill と同じ基準でリファクタ対象に含める（自己言及性）
