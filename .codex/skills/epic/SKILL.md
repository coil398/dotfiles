---
name: "epic"
description: "大規模タスクを所有範囲の明確なサブタスクと依存グラフに分割し、Codex subagent と PIR² を使って独立 wave を並列実行する上位オーケストレーション。複数サブシステムを横断する改修、独立フィーチャの同時実装、段階的な大型移行に使う。ユーザーが /epic と入力したら必ず使う。"
---

# Epic — Codex native orchestration

epic を起動したメイン Sol が、ユーザー対話、判断、計画、DAG 分解、完了要件、状態記録、最終判定の単一責任者です。Sol はオーケストレーターの座を子に譲らず、Codex native overlay の `.codex/skills/pir2/SKILL.md` をサブタスクごとに適用します。

**タスク**: $ARGUMENTS

## 変更禁止の不変条件

- 親 Sol のみがユーザーに判断を求める。worker は判断要請を構造化して Sol に戻す。
- 各サブタスクに所有ファイルまたは所有責務と禁止範囲を持たせる。所有範囲が重なるタスクは同じ並列 wave に入れない。
- ユーザーの既存変更と他エージェントの変更を戻さない。`git add` / `git commit` は行わない。
- subagent の起動可否や深さを固定的に仮定しない。実行時のツール説明と起動結果を優先し、不可でも Sol が同じ完了要件を維持する。
- 並列エージェントが同じ状態ファイルを書かない。`epic-runs.md` は親 epic のみが書く。

## Phase 0: run 初期化

`PROJECT_ROOT` は現在の workspace root とする。PIR² の sanitized cwd 契約に従って `PROJECT_MEMORY_DIR` を決め、すべての実行 artifact は実体のある非シンボリックリンク `$HOME/.ai-pir-runs` の配下に置く。epic 自身の `EPIC_RUN_DIR` は同 root 直下に一意に作成し、リポジトリ内へ run directory を作成してはならない。必要な安全条件と override 契約は次を参照する。

- `${PROJECT_ROOT}/.codex/skills/pir2/references/sanitized-cwd.md`
- `${PROJECT_ROOT}/.codex/skills/pir2/SKILL.md`
- `${PROJECT_ROOT}/.codex/skills/worker-delegation/SKILL.md`（artifact root と runner provenance の SSOT）

以下は run 名の衝突と root の取り違えを防ぐ最小初期化例です。`mkdir` の成功を予約の成否に使い、既存 path（ファイル・ディレクトリ・symlink を含む）を再利用しません。

```bash
PROJECT_ROOT="$(pwd)"
TASK="$ARGUMENTS"
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
ARTIFACT_ROOT_PHYSICAL="$(cd -P "$ARTIFACT_ROOT" && pwd -P)" || exit 1
[ "$ARTIFACT_ROOT_PHYSICAL" = "$ARTIFACT_ROOT" ] || {
  # A physical ancestor alias (for example /var -> /private/var) is allowed;
  # the artifact-root entry itself must still be the real directory above.
  [ -d "$ARTIFACT_ROOT_PHYSICAL" ] || exit 1
}

run_ts="$(date +%Y%m%d-%H%M%S)"
run_feature="$(printf '%s' "$TASK" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
[ -n "$run_feature" ] || run_feature="epic"
EPIC_RUN_BASE="${ARTIFACT_ROOT}/${run_ts}-epic-${run_feature}"
run_suffix=0
while :; do
  EPIC_RUN_DIR="$EPIC_RUN_BASE"
  [ "$run_suffix" -eq 0 ] || EPIC_RUN_DIR="${EPIC_RUN_BASE}-${run_suffix}"
  if (umask 077; mkdir "$EPIC_RUN_DIR") 2>/dev/null; then
    break
  fi
  [ -e "$EPIC_RUN_DIR" ] || [ -L "$EPIC_RUN_DIR" ] || {
    echo "could not create unique EPIC_RUN_DIR: $EPIC_RUN_DIR" >&2
    exit 1
  }
  run_suffix=$((run_suffix + 1))
done

# Keep the parent run observable as well.  The helper owns the ledger schema,
# provenance precedence, and append-only/symlink checks; epic does not copy
# those details into this skill.
OBS_HELPER="${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/record-observation.sh"
"$OBS_HELPER" init --run-dir "$EPIC_RUN_DIR"
```

`TASK=$ARGUMENTS` をそのまま使う。Codex 内で別 runtime を選ぶ互換フラグは解釈しない。

`${EPIC_RUN_DIR}/epic-runs.md` を次の列で初期化する。

```markdown
| Task | Actor/role | Session | Sub RUN_DIR | State | Acceptance | Quality | Updated |
|---|---|---|---|---|---|---|---|
```

State は `PENDING` / `RUNNING` / `WAITING_USER` / `PASS` / `FAIL` のいずれかにする。イベントの追記が必要な場合は `${EPIC_RUN_DIR}/epic-events.md` に時刻、Ti、操作、結果を記録する。

## Phase 1: 探索と分割

1. `list_agents` で現在のエージェント状態を確認する。
2. 利用可能なら `spawn_agent` で `agent_type="epic-planner"` を1体起動する。安定した小文字 `task_name` を付け、原則 `fork_turns="none"` として必要な文脈だけをプロンプトで注入する。
3. プロンプトに `PROJECT_MEMORY_DIR`、`EPIC_RUN_DIR`、`PROJECT_ROOT`、タスク、所有範囲分離、レポート出力先を必ず含める。分割結果は `EPIC_RUN_DIR/epic-plan.md` に書かせる。
4. `epic-planner` が深さ制約で explorer を起動できない場合は、同エージェント自身がリポジトリを読み取って探索を完遂するよう指示する。`epic-planner` 自体を起動できなければ、親 epic が同じ探索・DAG 作成・レポート出力を直接行う。
5. 探索不足が残る場合は、修正・追加探索を `followup_task` で同じ planner に戻す。エージェントが再利用できなければ、既存レポートパスを含めて代替を起動する。最大5回で収束しなければ未解決 topic をユーザーに示す。

`epic-plan.md` には各 Ti の WHAT、所有範囲、禁止範囲、成果物、依存辺、共有リソース、完了条件を必須とする。共有ファイル、schema、lockfile、生成物、共通 config、同一外部状態は暗黙依存として直列化する。

`epic-planner` の出力は助言であり、承認済み計画ではない。Sol が探索根拠、所有範囲、DAG、完了要件を自ら照合し、必要な修正と最終の分解判断を行う。

## Phase 1.5: 計画レビューと自動継続

親 epic が `epic-plan.md` を読み、サブタスク一覧、DAG、所有範囲、各 PIR² に渡すタスク記述、未解決事項を commentary でユーザーに進捗共有する。この提示は既定では承認ゲートではない。次の順で扱う。

1. 元の依頼が実行まで明示的に許可しており、計画がその範囲内なら、`EPIC_RUN_DIR/user-decisions.md` に `EXECUTION_AUTHORIZED_BY_ORIGINAL_REQUEST` と根拠を記録し、回答ターンを終了せず待機なしで Phase 2 へ進む。`/goal`、「最後まで」「全部実行」「Issue を作成」などの終端条件はこの扱いとする。終端条件は権限を拡張しないが、内部計画の再承認理由にもならない。
2. 実行権限はあるものの任意の異論受付が有益な **soft review** では、推奨案と「異論がなければ30秒後に自動継続する」旨を commentary で示し、そのターンを終了しない。安全な read-only / no-regret 作業を続け、必要なら利用可能な待機機構を一度だけ最大30秒使う。新しい反対・変更入力がなければ `AUTO_CONTINUE_AFTER_30S` を `user-decisions.md` に記録して Phase 2 へ進む。カウントダウンの反復や無期限ポーリングは禁止する。
3. 次の **hard gate** だけは `HARD_WAITING_USER` として停止し、タイムアウトで越えない: ユーザーが計画のみ・実行前承認を明示した場合、未許可の破壊的／不可逆操作、新たな外部書き込み・送信・課金・本番変更、資格情報や権限の欠如、成果物を実質的に変える複数案から選択が不可欠な場合。無応答を新しい権限の同意とみなしてはならない。

planner の `USER_DECISION_REQUIRED` / `EXPLORATION_NEEDED` はラベルだけで hard gate と判定しない。既存の依頼・仕様・リポジトリから安全に解決できるものは推奨案を採用して記録し、自動継続する。hard gate に該当する未解決事項だけをユーザーへ提示する。方針変更時は決定を `EPIC_RUN_DIR/user-decisions.md` に記録し、`followup_task` で planner を再開するか親が再分割する。

## Phase 2: DAG wave 実行

Sol は Ti ごとに PIR² の探索・計画・実装・レビュー・テスト・振り返りを管理する。計画と完了要件が確定するまで worker を起動しない。各 Ti の `SUB_RUN_DIR` は Phase 0 で確定した `ARTIFACT_ROOT` 配下に一意に予約し、PIR² 起動 prompt の明示フィールド `PIR2_RUN_DIR=$SUB_RUN_DIR` として渡す。これは PIR² Phase 0 の run base だけを上書きし、他のフェーズ境界、ゲート、レポート、ループ上限は維持する。

各 Ti の割り当ては親 epic が行います。`EPIC_RUN_DIR` 自体を実体のある非 symlink directory として作成済みであることを前提に、その下の `sub-runs` を実体化し、`mkdir` 成功で一意 path を予約します。Ti の起動 prompt には `PIR2_RUN_DIR` と親の `PIR2_PARENT_EPIC_RUN_DIR` を明記し、子が別の run path を推測しないようにします。

```bash
SUB_RUN_ROOT="${EPIC_RUN_DIR}/sub-runs"
if [ -e "$SUB_RUN_ROOT" ] || [ -L "$SUB_RUN_ROOT" ]; then
  [ -d "$SUB_RUN_ROOT" ] && [ ! -L "$SUB_RUN_ROOT" ] || {
    echo "sub-run root must be a real non-symlink directory: $SUB_RUN_ROOT" >&2
    exit 1
  }
else
  (umask 077; mkdir "$SUB_RUN_ROOT") || exit 1
fi
allocate_sub_run_dir() {
  ti_slug="$1"
  ti_ts="$(date +%Y%m%d-%H%M%S)"
  ti_base="${SUB_RUN_ROOT}/${ti_ts}-ti-${ti_slug}"
  ti_suffix=0
  while :; do
    SUB_RUN_DIR="$ti_base"
    [ "$ti_suffix" -eq 0 ] || SUB_RUN_DIR="${ti_base}-${ti_suffix}"
    if (umask 077; mkdir "$SUB_RUN_DIR") 2>/dev/null; then
      export SUB_RUN_DIR
      return 0
    fi
    [ -e "$SUB_RUN_DIR" ] || [ -L "$SUB_RUN_DIR" ] || return 1
    ti_suffix=$((ti_suffix + 1))
  done
}

# For each Ti, before launching PIR²:
allocate_sub_run_dir "$TI_SLUG" || exit 1
PIR2_PARENT_EPIC_RUN_DIR="$EPIC_RUN_DIR"
PIR2_PROMPT="PIR2_RUN_DIR=$SUB_RUN_DIR
PIR2_PARENT_EPIC_RUN_DIR=$PIR2_PARENT_EPIC_RUN_DIR
Use this exact run directory for every report, acceptance record, and user-decision path."
```

The child PIR² runner must accept the explicit `PIR2_RUN_DIR` only after its Phase 0 canonical-root, physical-parent, non-symlink, and collision checks. If any check fails, it must stop rather than silently choosing a different path.

### 2.1 worker-delegation 接続点

epic は actor / model の選択、昇格基準、runner の実行仕様を内包しない。これらの SSOT は全 Codex workflow 共通の `${PROJECT_ROOT}/.codex/skills/worker-delegation/SKILL.md` とし、epic は Ti 単位の具体作業をその委譲契約へ渡す接続点だけを持つ。各 Ti について次の入力を用意する。

- Ti、sub RUN_DIR、目的、具体的な実装指示
- 所有範囲、禁止範囲、先行依存の成果物
- `R1` から始まる実測可能な完了要件
- 既存変更を戻さないこと、判断不足時は独断せず Sol へ戻すこと

worker-delegation から返る完了報告は事実の引き渡しとして Sol が受領し、Ti、session / run、状態、変更ファイル、観測結果を `${EPIC_RUN_DIR}/epic-runs.md` に記録する。共有状態ファイルは親 epic だけが書き、worker には書かせない。worker-delegation の actor 選択、model、昇格、fallback、入力検証、報告形式を epic 本文で再定義しない。

Sol は worker の自己申告を acceptance PASS の根拠にしない。各 Rn を対象差分、ファイル、実行出力で自ら実測し、`${SUB_RUN_DIR}/sol-acceptance-<NN>.md` に `満たす / 満たさない` と根拠を記録する。全 Rn を満たす場合だけ acceptance PASS にする。

### 2.2 独立 wave の並列化

1. 完了済み依存を除いた入次数0の Ti を ready set とする。
2. ready set 内の所有範囲が重ならないことを再確認する。重なる場合は辺を追加して直列化する。
3. 独立 Ti の worker は、所有範囲が非重複であることを確認したうえで、実行面の実際の上限を超えない範囲で、間に待機を挟まず起動する。各 Ti は別の一時ディレクトリと結果ファイルを使う。
4. planner / reviewer / tester などを collaboration API で起動するときは `list_agents` で実行中の体数を確認し、現行のルートを含む7 slot 上限と実行面の実際の上限の両方を超えない。`fork_turns="none"` を原則とし、入力パスと完了要件を直接渡す。
5. 後続 Ti はすべての依存が acceptance PASS かつ quality PASS になるまで起動しない。wave 内の他 Ti は、失敗 Ti に依存しなければ継続できる。

### 2.3 品質ゲートと修正ループ

acceptance PASS 後に、Sol は PIR² の reviewer セットと tester を worker とは別系統で実行する。reviewer は worker の出力を信用せず、plan、Sol acceptance、実際の diff を読む。reviewer / tester が FAIL したら、Sol が指摘を計画と Rn に反映し、修正の具作業を改めて worker-delegation 契約に渡す。品質判定自体を worker に差し戻さない。

ユーザー判断が必要でも、まず Phase 1.5 と同じ soft review / hard gate 判定を行う。soft review と、元の依頼・仕様・リポジトリから保守的に解決できる判断は Sol が記録して自動継続する。hard gate の影響を受ける Ti だけを `WAITING_USER` とし、Sol が推奨案と必要最小限の選択肢を示す。その間も依存しない ready-set の Ti は止めずに起動する。回答は `${SUB_RUN_DIR}/user-decisions.md` に記録する。

## Phase 3: 統合確認

1. 全 Ti が終了したら、親 epic が `git diff` と全 sub RUN_DIR のレポートを読む。
2. 所有範囲違反、サブタスク間の interface / schema / 命名不整合、未接続実装、重複抽象、未検証の結合点を確認する。
3. 問題がタスク所有範囲に閉じるならその Ti を worker-delegation 契約で再実行する。複数 Ti にまたがるなら所有範囲を新たに定めた統合 Ti を追加する。Sol はいずれも実測と独立品質ゲートを再実行する。
4. 可能で有益な場合のみ `agent_type="retrospector"` を起動する。不可なら親が振り返りを `${EPIC_RUN_DIR}/retrospective.md` に記録する。実験記録を参照する場合は `${PROJECT_ROOT}/.codex/skills/pir2/references/experimental.md` を使う。

## Phase 4: 完了判定とサマリー

次のすべてを満たしたときだけ epic 全体を `PASS` にする。

- すべての Ti が `PASS`。`WAITING_USER` / `PENDING` / `RUNNING` が残っていない。
- 各 Ti の sub RUN_DIR、変更ファイル、レビュー、テスト結果が `epic-runs.md` から追跡できる。
- 親の統合確認が完了し、未解決の本質的判断や未接続の結合点がない。

最終出力には、全体 VERDICT、サブタスク一覧、DAG / wave、actor / session と sub RUN_DIR の対応、変更ファイル、acceptance の実測根拠、レビュー / テスト結果、deferred decisions、統合確認、メタ改善推奨、`EPIC_RUN_DIR` を含める。

## Codex 実行上の注記

- role は実行面で公開された `agent_type` のみ使う。未公開の role を推測で指定しない。
- モデル固定はエージェント定義またはユーザー指示に委ね、epic 本体が利用できるモデル名を推測して上書きしない。
- ツールエラーは記録し、権限拡張や設定変更がなくても実行できる fallback を先に試す。完了要件は弱めない。
