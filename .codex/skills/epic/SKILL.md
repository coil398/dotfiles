---
name: "epic"
description: "大規模タスクを所有範囲の明確なサブタスクと依存グラフに分割し、Codex native collaboration と PIR² で独立 wave を並列実行する上位オーケストレーション。複数サブシステムを横断する改修、独立フィーチャの同時実装、段階的な大型移行に使う。ユーザーが /epic と入力したら必ず使う。"
---

# Epic — Codex native orchestration

epic の親Astra（通常 `gpt-6-astra` / high）が、ユーザー対話、探索結果の統合、計画、DAG 分解、作業配分、完了要件、受入、統合、最終判定を所有します。小さく全体文脈と分離できない変更はAstraが直接実装し、独立した具体作業は [worker-delegation](../worker-delegation/SKILL.md) の契約に従って委譲します。各サブタスクでは、読込済み `epic/SKILL.md` の実体パスの親の親を基準に解決した `${CODEX_SKILLS_DIR}/pir2/SKILL.md` を使います。

**タスク**: $ARGUMENTS

## 変更禁止の不変条件

- ユーザーに判断を求めるのは親Astraだけです。worker は判断に必要な事実と blocker をAstraへ返します。
- 各 Ti は1つの担当に割り当て、所有ファイルまたは所有責務、禁止範囲、完了条件を明示します。同じファイル、契約、schema、lockfile、生成物、共通設定、外部状態を共有する Ti は同じ wave に入れません。
- ユーザーや他エージェントの既存変更を戻さず、epic は `git add` / `git commit` / `git push` を行いません。
- `epic-runs.md` と親の状態ファイルはAstraだけが書きます。並列担当に共有状態を書かせません。
- 子エージェントの同時実行上限は6体です。6体を埋めることは要求せず、実行面の上限が低い場合は低い方に従います。
- 依頼と仕様から安全に解決できる通常の判断で全体を停止しません。権限、外部作用、不可逆操作、または成果物を変える選択が本当に未解決な場合だけ、影響する Ti を待機させます。

## Phase 0: run 初期化

`PROJECT_ROOT` は現在の workspace root の物理 path とし、`PROJECT_MEMORY_DIR` と実行 artifact は PIR² の契約に合わせます。`CODEX_SKILLS_DIR` は読込済み `epic/SKILL.md` の実体パスの親の親、または親Astraが同じ実体として確定したCodex skill directoryです。対象アプリリポジトリに `.codex/skills` があると仮定せず、参照はこの値の兄弟 skill から解決します。epic の `EPIC_RUN_DIR` は実体のある非 symlink directory として `$HOME/.ai-pir-runs` の直下に一意に作り、リポジトリ内へ run directory を作りません。詳細な path 検査は次を正とします。

- `${CODEX_SKILLS_DIR}/pir2/references/sanitized-cwd.md`
- `${CODEX_SKILLS_DIR}/pir2/SKILL.md`
- `${CODEX_SKILLS_DIR}/worker-delegation/SKILL.md`（artifact root と runner provenance の SSOT）

以下は run 名の衝突と root の取り違えを防ぐ最小初期化例です。`mkdir` の成功を予約の成否に使い、既存 path（ファイル・ディレクトリ・symlink を含む）を再利用しません。

```bash
PROJECT_ROOT="$(pwd -P)"
TASK="$ARGUMENTS"
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

```

`TASK=$ARGUMENTS` をそのまま扱い、別 runtime を選ぶ互換フラグは解釈しません。

`${EPIC_RUN_DIR}/epic-runs.md` は親Astraのオーケストレーション台帳として次の列で初期化します。これは runner の provenance 台帳ではありません。

```markdown
| Task | Actor/role | Session | Sub RUN_DIR | State | Acceptance | Quality | Updated |
|---|---|---|---|---|---|---|---|
```

State は `PENDING` / `RUNNING` / `WAITING_USER` / `PASS` / `FAIL` のいずれかです。必要なイベントだけ `${EPIC_RUN_DIR}/epic-events.md` に時刻、Ti、操作、結果を追記します。native collaboration またはAstraの直接実装では runner 用の `record-observation.sh`、canonical report、deterministic gate を初期化しません。artifact identity や CLI provenance が要件の Ti だけが、worker-delegation の runner 契約と観測手順を使います。

## Phase 1: 探索と分割

1. `list_agents` で現在の実行数と利用可能な同時枠を確認します。
2. 親Astraが対象リポジトリ、既存仕様、関連 artifact を read-only で探索し、確認済み事実、未解決点、候補の所有境界を `${EPIC_RUN_DIR}/epic-exploration.md` に記録します。独立した調査領域を委譲する場合は、topic、範囲、出力 path、実装禁止を明示した `explorer` に渡します。
3. Astraがタスクを Ti に分解し、各 Ti に一意な ASCII ID（`T1`、`T2` ...）、WHAT、所有範囲、禁止範囲、成果物、共有リソース、依存辺、`R1` から始まる実測可能な完了要件を定義して `${EPIC_RUN_DIR}/epic-plan.md` に書きます。DAG、wave、各 PIR² に渡す task 記述、必要な implementation shard の境界と依存もAstraが照合します。
4. 追加探索は完了判断に影響する具体的な問いに限ります。結果をAstraが読み、既存の `epic-exploration-<NN>.md` と `epic-plan.md` の該当箇所だけを更新します。解消できない問いは推測で埋めず、影響する Ti と blocker を記録します。

`epic-plan.md` の分割判断はAstraが所有します。共有ファイル、schema、lockfile、生成物、共通 config、同一外部状態を複数 Ti が変更・操作する場合は、依存辺を張って直列化します。各独立 Ti は1担当・非重複所有として初めて同じ wave に置きます。

## Phase 1.5: 計画レビューと継続

親Astraは `epic-plan.md` のサブタスク一覧、DAG、所有境界、各 PIR² の task 記述、未解決事項を commentary で共有します。これは既定では承認ゲートではありません。

1. 元の依頼が実行まで許可しており計画がその範囲内なら、`${EPIC_RUN_DIR}/user-decisions.md` に `EXECUTION_AUTHORIZED_BY_ORIGINAL_REQUEST` と根拠を記録して Phase 2 へ進みます。
2. soft review や `USER_DECISION_REQUIRED` / `EXPLORATION_NEEDED` のラベルだけでは停止しません。既存の依頼、仕様、実測から保守的に決められる内容はAstraが記録して継続します。
3. ユーザーが計画のみ・実行前承認を指定した場合、未許可の破壊的／不可逆操作や外部書き込みが必要な場合、資格情報・権限が欠ける場合、または成果物を実質的に変える複数案の選択が不可欠な場合だけ `HARD_WAITING_USER` とします。待機するのは影響する Ti だけで、依存しない ready set は進めます。

方針変更は `${EPIC_RUN_DIR}/user-decisions.md` に記録し、影響する Ti、辺、scope、完了要件だけをAstraが増分更新します。計画全体を破棄・再策定しません。

## Phase 2: DAG wave 実行

親Astraは Ti ごとに PIR² の探索・計画・実装・レビュー・テスト・振り返りを管理します。計画と完了要件が確定するまで worker を起動しません。各 Ti の `SUB_RUN_DIR` は Phase 0 で確定した `ARTIFACT_ROOT` 配下に一意に予約し、PIR² 起動 prompt の明示フィールド `PIR2_RUN_DIR=$SUB_RUN_DIR` として渡します。これは PIR² Phase 0 の run base だけを上書きし、他のフェーズ境界、ゲート、レポート、ループ上限は維持します。

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
  ti_slug="$(printf '%s' "$1" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
  [ -n "$ti_slug" ] || return 1
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

# For each Ti, before launching PIR², use its epic-plan.md ID:
allocate_sub_run_dir "$TI_ID" || exit 1
PIR2_PARENT_EPIC_RUN_DIR="$EPIC_RUN_DIR"
PIR2_PROMPT="PIR2_RUN_DIR=$SUB_RUN_DIR
PIR2_PARENT_EPIC_RUN_DIR=$PIR2_PARENT_EPIC_RUN_DIR
Use this exact run directory for every report, acceptance record, and user-decision path."
```

子PIR²は Phase 0 の canonical root、physical parent、非 symlink、衝突検査を通過した場合だけ明示 `PIR2_RUN_DIR` を採用します。検査や起動が拒否された場合は実際の出力と影響する Ti を記録し、別 runtime、別 path、別 actor、権限回避へ黙って迂回しません。

### 2.1 worker-delegation 接続点

actor / model、昇格基準、runner の入力検証・証跡形式は `${CODEX_SKILLS_DIR}/worker-delegation/SKILL.md` がSSOTです。epic はその契約へ Ti の具体作業を渡すだけで、ladder や runner を再定義しません。各 Ti の PIR² は次の経路を判断します。

- 小さく全体文脈と分離できない変更: 親Astraが直接実装。
- 所有範囲と終了条件が明確な独立変更: native collaboration の `worker`（通常 `gpt-5.6-luna` / max）。
- 原因・状態・競合・性能などの難所: `expert`（`gpt-5.6-sol` / high）または `expert_max`（`gpt-5.6-sol` / max）を初手から選択可能。
- Terra は標準経路ではなく、同種 workload の実測で明確な利点がある場合だけ親Astraが例外として明示。

入力には Ti、目的、具体的な指示、所有／禁止範囲、先行成果物、`R1` からの完了要件、焦点を絞った確認、未解決時にAstraへ戻す条件を含めます。自動 fallback、自己判断の再試行、未測定の actor／effort 変更は行いません。

worker の返却は事実の引き渡しであり、Astraは実際の `git status -sb`、対象 diff、変更ファイル、要求したコマンド結果で各 `Rn` を独立に確認します。確認結果は `${SUB_RUN_DIR}/acceptance-<NN>.md` に記録し、worker report、runner exit、未解決事項の一言だけで PASS や停止を決めません。runner を選んだ Ti だけは worker-delegation の実測 report / provenance を読み、必要な証跡を `epic-runs.md` に対応付けます。native/direct Ti に runner の canonical report、deterministic gate、観測台帳を追加しません。

### 2.2 独立 wave の並列化

1. 完了済み依存を除いた入次数0の Ti を ready set とします。
2. ready set の所有範囲と共有リソースが非重複であることを再確認します。重なる場合は依存辺を追加して直列化します。
3. 独立 Ti は、各 Ti に1担当・専有の所有範囲と別の `SUB_RUN_DIR` を割り当て、同じ wave で並列起動します。起動前に `list_agents` で生存数を確認し、生存する子エージェントは最大6体に収めます。reviewer / tester を起動する場合も同じ上限と実行面の上限を守ります。
4. 依存 Ti は先行 Ti が acceptance PASS かつ、必要な quality check を PASS または「不要」と実測根拠付きで判定するまで起動しません。wave 内の他 Ti は、失敗 Ti に依存しなければ継続します。

### 2.3 品質ゲートと修正ループ

各 Ti の acceptance 後、PIR²の `REVIEWER_SET` は変更のリスクと実際の diff から必要な観点だけを選びます。5観点を固定起動せず、起動した reviewer は worker とは別系統で実際の diff、plan、受入条件を読みます。runtime、データ整合性、生成物、外部挙動に影響する変更、またはユーザーが明示した確認がある場合だけ tester を別系統で起動します。documentation/config-only や no-op は、Astraまたは worker が行う適切な静的・構文・設定確認で足りる場合があります。

reviewer / tester を起動した場合、その実在する report と verdict を `epic-runs.md` に記録します。起動していない role の PASS や証跡を作りません。FAIL は再現可能な指摘を根拠に、影響する Ti の plan、scope、DAG、完了要件だけを増分更新し、直接実装または worker / expert に修正を渡します。修正後は影響した reviewer / tester と必要な確認だけを再実行し、無関係な Ti や完了済みの観点を最初からやり直しません。

worker の入力不足、権限・環境・CLI の失敗は能力不足とみなさず、Astraが解消できるかを先に確認します。解消不能な hard gate だけを該当 Ti の `WAITING_USER` とし、依存しない ready set を止めません。

## Phase 3: 統合確認

1. 全 Ti の終了後、親Astraが実際の `git diff` と全 sub RUN_DIR の実在する report を読みます。
2. 所有範囲違反、Ti 間の interface / schema / 命名不整合、未接続実装、重複抽象、未検証の結合点を確認します。
3. 問題が1 Tiに閉じるならその Ti の所有境界で修正し、複数 Ti にまたがるなら競合しない所有範囲を定めた統合 Ti を追加して、依存辺・受入・必要な review / test をAstraが更新します。
4. 統合点に実行時・データ・外部挙動の実害がある場合だけ、影響範囲に絞った reviewer / tester を追加します。分離価値がある場合の retrospector は任意とし、不可ならAstraが `${EPIC_RUN_DIR}/retrospective.md` に記録します。実験記録を参照する場合は `${CODEX_SKILLS_DIR}/pir2/references/experimental.md` を使います。

## Phase 4: 完了判定とサマリー

次のすべてを実際の差分と確認結果で満たした場合だけ epic 全体を `PASS` にします。

- すべての Ti が `PASS` で、`WAITING_USER` / `PENDING` / `RUNNING` が残っていない。
- 各 Ti の sub RUN_DIR、実在する変更ファイル、acceptance、起動した reviewer / tester の結果が `epic-runs.md` から追跡できる。未起動の品質工程は未実施として扱い、不要とした根拠を記録します。
- 親Astraの統合確認が完了し、未解決の本質的判断、所有範囲違反、未接続の結合点がありません。

最終出力には、全体 VERDICT、サブタスク一覧、DAG / wave、actor / session と sub RUN_DIR の対応、実在する変更ファイル、acceptance の実測根拠、実際に起動した reviewer / tester の結果、deferred decisions、統合確認、必要な runner provenance、`EPIC_RUN_DIR` を含めます。

## Codex 実行上の注記

- role、model、effort は実行面で公開された定義と worker-delegation の契約に従い、epic 本体が推測で上書きしません。
- runner は明示的に artifact identity、CLI 実行、provenance、物理境界付き証拠が必要な Ti だけで使います。runner が拒否された場合は出力を報告し、通常経路へ無断で迂回しません。
- tool error、未実行の確認、未対応事項、外部状態の blocker は成功扱いにせず、該当 Ti と親統合の状態に記録します。
- ユーザーの依頼と必要な確認が完了したら、追加のメタゲートや無関係な再試行を増やさず、未実行の確認と残るリスクを明記して報告します。
