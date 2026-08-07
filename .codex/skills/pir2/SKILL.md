---
name: "pir2"
description: "コーディングタスクを Plan → Implement → Review → Retrospect の4フェーズで実行する。複雑なタスク・設計が必要なタスク・品質保証が重要なタスク、大きな機能追加・リファクタリング・アーキテクチャ変更に使う。「ちゃんと作りたい」「しっかり実装して」「品質重視で」といった要望にも対応する。ユーザーが /pir2 と入力したら必ずこのスキルを使う。"
argument-hint: "[タスクの説明]"
---

# PIR² — Plan → Implement → Review → Retrospect

PIR²ワークフローを実行します。このスキル本体（= Sol orchestrator）が、Plan → Implement → Review → Test → Retrospect を進めます。Sol orchestrator は対象リポジトリを実装・修正せず、具体的な変更は明示された worker-delegation job の worker に委譲します。

Codex では subagent は明示依頼された並列・委譲作業に使う補助機構です。`/pir2` の明示起動を subagent 使用許可とみなしてよい。既存PIR²と同じく、探索 → 計画 → worker → レビュー → テストの分業を基本形にする。並列 writer は禁止し、subagent 機能が現在の実行面で利用できない場合も、Sol orchestrator は repository write を行わず、正確な blocker を記録してユーザーへ戻してください。

**タスク**: $ARGUMENTS

---

## ステップ 1: プロジェクトメモリパスと RUN_DIR の確定

以下の Bash コマンドで `PROJECT_ROOT` / `PROJECT_MEMORY_DIR` / `RUN_DIR` / `HANDOFF_PATH` を確定し、以降のすべてのステップで使用してください。親 epic から起動された場合、親が prompt に明示した `PIR2_RUN_DIR`（および検証用の `PIR2_PARENT_EPIC_RUN_DIR`）を最優先し、ambient な同名環境変数を信頼して別 path を推測してはいけません。指定 path は canonical artifact root、実体 parent、非 symlink、空き/未衝突の全条件を満たすときだけ採用します。

```bash
PROJECT_ROOT="$(pwd)"
# sanitized-cwd 計算は ${PROJECT_ROOT}/.codex/skills/pir2/references/sanitized-cwd.md を SSOT とする
# （Codex harness の sanitize 仕様変更時はこの SSOT のみを更新し、9 ファイルに横展開）
sanitized_cwd="$(pwd | sed 's|[^a-zA-Z0-9]|-|g')"
PROJECT_MEMORY_DIR="${HOME}/.codex/projects/${sanitized_cwd}/memory"
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
[ -d "$ARTIFACT_ROOT_PHYSICAL" ] || { echo "artifact root is not a directory" >&2; exit 1; }

parent_run_dir="${PIR2_RUN_DIR:-}"
parent_epic_dir="${PIR2_PARENT_EPIC_RUN_DIR:-}"
# A bare ambient PIR2_RUN_DIR is not a trusted parent override.  Only the
# explicit pair emitted by epic is eligible; otherwise generate a fresh run.
if [ -n "$parent_run_dir" ] && [ -z "$parent_epic_dir" ]; then
  parent_run_dir=''
fi
if [ -n "$parent_run_dir" ]; then
  case "$parent_run_dir" in
    /*) ;;
    *) echo "PIR2_RUN_DIR must be absolute" >&2; exit 1 ;;
  esac
  parent_dir="$(dirname "$parent_run_dir")"
  [ -d "$parent_dir" ] && [ ! -L "$parent_dir" ] || {
    echo "PIR2_RUN_DIR parent must be an existing real directory: $parent_dir" >&2
    exit 1
  }
  parent_dir_physical="$(cd -P "$parent_dir" && pwd -P)" || exit 1
  case "$parent_dir_physical" in
    "$ARTIFACT_ROOT_PHYSICAL"|"$ARTIFACT_ROOT_PHYSICAL"/*) ;;
    *) echo "PIR2_RUN_DIR must be below the canonical artifact root" >&2; exit 1 ;;
  esac
  if [ -n "$parent_epic_dir" ]; then
    [ -d "$parent_epic_dir" ] && [ ! -L "$parent_epic_dir" ] || {
      echo "PIR2_PARENT_EPIC_RUN_DIR must be a real directory" >&2; exit 1
    }
    parent_epic_physical="$(cd -P "$parent_epic_dir" && pwd -P)" || exit 1
    case "$parent_epic_physical" in
      "$ARTIFACT_ROOT_PHYSICAL"|"$ARTIFACT_ROOT_PHYSICAL"/*) ;;
      *) echo "PIR2_PARENT_EPIC_RUN_DIR must be below the canonical artifact root" >&2; exit 1 ;;
    esac
    case "$parent_dir_physical" in
      "$parent_epic_physical"/*) ;;
      *) echo "PIR2_RUN_DIR must be allocated by the parent epic" >&2; exit 1 ;;
    esac
  fi
  if [ -e "$parent_run_dir" ] || [ -L "$parent_run_dir" ]; then
    [ -d "$parent_run_dir" ] && [ ! -L "$parent_run_dir" ] || {
      echo "PIR2_RUN_DIR is not a real directory" >&2; exit 1
    }
    for run_child in "$parent_run_dir"/* "$parent_run_dir"/.[!.]* "$parent_run_dir"/..?*; do
      [ -e "$run_child" ] || [ -L "$run_child" ] || continue
      echo "PIR2_RUN_DIR is already occupied" >&2
      exit 1
    done
  else
    (umask 077; mkdir "$parent_run_dir") || {
      echo "PIR2_RUN_DIR was lost or collided before adoption" >&2; exit 1
    }
  fi
  RUN_DIR="$parent_run_dir"
else
  # No trusted parent override: create a fresh, collision-free child directly
  # below the canonical root.  mkdir is the uniqueness gate; never reuse a
  # pre-existing path, file, or symlink.
  run_ts="$(date +%Y%m%d-%H%M%S)"
  run_feature="$(printf '%s' "$ARGUMENTS" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
  [ -n "$run_feature" ] || run_feature="task"
  run_base="${ARTIFACT_ROOT}/${run_ts}-${run_feature}"
  run_suffix=0
  while :; do
    RUN_DIR="$run_base"
    [ "$run_suffix" -eq 0 ] || RUN_DIR="${run_base}-${run_suffix}"
    if (umask 077; mkdir "$RUN_DIR") 2>/dev/null; then
      break
    fi
    [ -e "$RUN_DIR" ] || [ -L "$RUN_DIR" ] || {
      echo "could not create unique RUN_DIR: $RUN_DIR" >&2; exit 1
    }
    run_suffix=$((run_suffix + 1))
  done
fi

# Handoff remains a stable project-level notice, but every PIR² report,
# acceptance record, and user decision below uses the actual RUN_DIR above.
HANDOFF_PATH="${ARTIFACT_ROOT}/${sanitized_cwd}/handoff.md"
OBS_HELPER="${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/record-observation.sh"
"$OBS_HELPER" init --run-dir "$RUN_DIR"
echo "PROJECT_ROOT=$PROJECT_ROOT"
echo "PROJECT_MEMORY_DIR=$PROJECT_MEMORY_DIR"
echo "ARTIFACT_ROOT=$ARTIFACT_ROOT"
echo "PIR2_PARENT_EPIC_RUN_DIR=${parent_epic_dir:-none}"
echo "RUN_DIR=$RUN_DIR"
echo "HANDOFF_PATH=$HANDOFF_PATH"
```

次に `RESUME_MODE` を Sol orchestrator が判定する:

- `$ARGUMENTS` に `引継い` / `続き` / `resume` / `Resume` / `RESUME` / `handoff` / `Handoff` / `HANDOFF` / `carry on` のいずれかが含まれる → `RESUME_MODE=resume`
- 含まれず、かつ `$HANDOFF_PATH` のファイルが存在する → `RESUME_MODE=passive-notice`
- それ以外 → `RESUME_MODE=new`

`RESUME_MODE` に応じて以降の挙動を分岐させる（詳細プロトコル: `~/.codex/pir-handoff.md`）:

- `resume`: ステップ 2（ブレスト）をスキップし、planner への入力に `HANDOFF_PATH=$HANDOFF_PATH` を含めて「handoff.md の未チェック項目のみを planning 対象にせよ」と指示する。スキル本体は handoff.md を上書きしない
- `passive-notice`: 「💡 前回の handoff が残っています: `$HANDOFF_PATH`」とユーザーに表示し、通常の新規タスクフローで続行する（handoff.md は触らない）
- `new`: 通常の新規タスクフロー。planner の plan.md 完成直後にスキル本体が handoff.md 初期版を Write する（プランのステップを `[ ]` チェックリスト化）

`RUN_DIR` は Phase 0 で採用した実体 path の唯一の run artifact root です。`implementation-*` / `worker-output-*` / `sol-acceptance-*` / `review-*` / `test-*` / `user-decisions.md` と、worker-observability の3台帳は必ず `${RUN_DIR}` に置き、`PROJECT_ROOT` や推測で再導出した別の run path に書いてはいけません。親 epic の `PIR2_RUN_DIR` を採用した場合もこの不変条件は変わりません。

retrospector フェーズ完了後、スキル本体は handoff.md を Read し、全項目が `[x]` なら削除、残項目ありなら「最終更新」タイムスタンプを更新する。

このステップで内部状態フラグ `PLAN_STRATEGY_CHANGED=false` を初期化してください。これはユーザー方針切替（ステップ 4.6 の「別案」選択など）による plan 再策定が発生した場合のみ `true` にセットされ、planner 側 3.3「v1 判断白紙化チェック」の発動条件として使われます。EXPLORATION_NEEDED ループ（ステップ 4.5）の追加探索による再策定では立てません。

以降の各フェーズまたはsubagentへのプロンプトには必ず `PROJECT_MEMORY_DIR=[パス]` および `RUN_DIR=[パス]` を含めてください。

---

## ステップ 2: ブレインストーミング（状況に応じて実施）

タスクの仕様を評価し、以下のいずれかに該当する場合は brainstorm スキルを実行してから次のステップへ進んでください：

- 要件が曖昧で複数の解釈が可能
- アーキテクチャ上の選択肢が複数あり、どれを選ぶかユーザーに確認が必要
- ユーザーとの対話を通じて設計を固めたほうが手戻りリスクを減らせると判断される

実行方法: Codex skill invocationで `skill: "brainstorm"` を呼び出す。ユーザーとの対話で固まった設計はステップ4の planner に渡してください。

該当しない場合（タスクが明確、既存の設計がある、`docs/brainstorm/` に関連する設計ドキュメントが存在する）はスキップしてください。

> **brainstorm 完了後は必ず自動でステップ3へ進むこと**。「設計ドキュメントを保存しました」と単独ターンで区切ってユーザーの承認を待つのは禁止。`/pir2` は一度起動されたら最終サマリー（ステップ12）まで止まらず進める設計であり、brainstorm の最終出力「次のステップとして `/writing-plan` で実装プランを作成できます」は `/brainstorm` 単独起動時向けの案内なので、`/pir2` 経由では無視して続行する。承認を挟んでよいのは `${PROJECT_ROOT}/.codex/skills/pir2/SKILL.md` 内で明示的にユーザー確認が指定されているポイント（既存パターン逸脱の事前申告・ステップ6.5 未解決事項確認）のみ。

---

## ステップ 3: 探索フェーズ（explorer）

コードベース探索は read-heavy なので、subagent が利用可能なら `explorer` を優先して委譲してください。subagent が利用できない、または小規模変更で直接探索の方が明らかに速い場合は、Sol orchestrator が `rg` / `rg --files` / Read で read-only 探索してよい。ただし探索結果は必ず `{RUN_DIR}/exploration-{NN}.md` に保存し、推測と確認済み事実を分けて扱うこと。

### 起動ルール

- **最低1回実行**: タスクの規模にかかわらず初回探索は必須。subagent 利用可なら最低1体、利用不可なら Sol orchestrator が read-only で実行
- **最大3体並列**: 調査領域が独立している場合のみ並列起動
- **role dispatch**: `spawn_agent` に `agent_type="explorer"` を渡して起動し、モデル引数は指定しない。専門モデルの選択は `.codex/agents/explorer.toml` の role 定義に委ねる
- **浅い探索 tier**: ファイル構造、パターン列挙、grep 結果の収集を担当する `explorer` を 1〜3 体。調査領域が独立している場合だけ並列起動する
- **深い探索 tier**: 既存ロジックの意味、設計意図、高度な間接参照、メタプログラミング、複雑な状態遷移を担当する `explorer` を 1 体。浅いレポートだけでは意図を確定できない、または追跡が途切れる場合に限って起動する
- **ミックス起動**: 広さと深さの両方が必要なら、浅い探索の `explorer` 群と深い探索の `explorer` 1 体を同一ターンで並列起動してよい。深い探索を常用しない
- **深掘りフォローアップ**: 既存 explorer が継続可能なら `followup_task`、継続できなければ同じ `explorer` role を `spawn_agent` で追加起動する。同じ role をモデル名だけでフォールバックさせない

### プロンプトに必ず含めるパラメータ
- `PROJECT_MEMORY_DIR=[パス]`
- `RUN_DIR=[パス]`
- `EXPLORATION_INDEX=NN`（初回=`01`、並列起動時はスキル本体が `01`/`02`/`03` と割り振る）
- 「探索レポート本体は `{RUN_DIR}/exploration-{NN}.md` に書き出し、チャットには要約のみ返してください」
- 「探索フェーズではタスクのコード実装を行わず、`git add` / `git commit` などリポジトリ状態を変更する git 操作も一切行わないでください。実装が必要だと判明したら探索レポートの『呼び出し元への依頼』に回してください」（explorer は `Write` / `Bash` を持つため、明示しないと探索の延長で実装・コミットまで踏み込むロール逸脱が起こりうる）

### プロンプトに必ず含める調査観点

- 変更対象と同一ドメイン・同一レイヤーの既存実装パターン（類似機能がどう実装されているか）
- 再利用可能な既存ユーティリティ・ヘルパー関数
- 変更対象のメソッド/関数内の他分岐が設定しているフィールド・処理の一覧
- フレームワークが自動処理する機能（新規コードで手動実装すべきでないもの）
- 調査対象がライブラリ・フレームワークの API 仕様に関わる場合は、公式 README / doc / Issue を WebFetch/WebSearch で裏取りし参照 URL をレポートに含めること（推測や記憶で結論を埋めさせない）

### 追加探索

初回レポートで不明点があれば、既存 explorer を再利用できる場合は `followup_task`、できない場合は `spawn_agent`（`agent_type="explorer"`）で追加探索を依頼してください。回数上限なし。推測でプランを埋めるくらいなら追加探索を回す。追加探索時は `EXPLORATION_INDEX` を既存 `{RUN_DIR}/exploration-*.md` の最大値+1 に設定する。

### ライブラリ選定が必要な場合

新しいライブラリ・フレームワークの導入判断が必要なら `spawn_agent` で `agent_type="tech-validator"` を起動する（既存の依存関係で解決できる場合はスキップ）。モデル引数は指定せず `.codex/agents/tech-validator.toml` に委ねる。

---

## ステップ 4: プラン策定（planner）

設計判断が重い場合は `planner` role を `spawn_agent`（`agent_type="planner"`）で起動し、タスク内容と探索レポート全文を渡してください。モデル引数は指定せず `.codex/agents/planner.toml` の role 定義に委ねます。小規模・明確な変更では、Sol orchestrator が planner 観点を read-only に適用して非リポジトリ artifact の `{RUN_DIR}/plan.md` を作成してよい。

- プロンプト:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `PLAN_STRATEGY_CHANGED=$PLAN_STRATEGY_CHANGED`（現在の値。初回起動時は `false`、ステップ 4.6 で「別案」が選ばれた直後の再起動時のみ `true`）
  - タスク内容
  - `{RUN_DIR}/exploration-*.md` のパス一覧（planner は本文を自分で Read する）
  - ブレインストーミング結果（ステップ2で実施した場合）
  - 「完全に独立した実装 shard がある場合のみ `IMPLEMENTATION_SHARDS` を提案してください。判定基準は `${PROJECT_ROOT}/.codex/skills/pir2/references/implementation-delegation.md` に従うこと」
  - 「プランレポート本体は `{RUN_DIR}/plan.md` に書き出し、チャットには要約＋EXPLORATION_NEEDED の有無のみ返してください」

planner からプラン要約を受け取ってください。

### 既存パターン逸脱の事前申告

planner から「既存構造と異なる構成を採用する」判断が含まれたプランが返ってきた場合、実装着手前にユーザーに差分（既存 N 件中 M 件の構成 / 今回採用しようとしている構成 / 逸脱理由 / 代替案）を提示し、承認を得ること。承認なしに次のステップに進んではならない。

---

## ステップ 4.5: 能動的再探索ループ（最大5回）

詳細プロトコル: `${PROJECT_ROOT}/.codex/skills/pir2/references/exploration-loop.md` を参照（収束判定ロジック / ループ本体 / 既存パターン逸脱の事前申告タイミング）。

要点: planner の返り値要約に `### EXPLORATION_NEEDED` の `- topic` が残る間、追加探索 → planner 再起動を最大 5 回繰り返す。収束したらステップ 5 へ進む。`REPLAN_COUNT = 0` から開始し、ハードキャップ到達時は最終サマリー（ステップ12）に「**planner が依然追加探索を要求中（ハードキャップ5回到達）**: [topic 一覧]」と明記する。

---

## ステップ 4.6: プラン選択肢のユーザー確認（該当時のみ・Auto mode でも例外なし）

詳細プロトコル: `${PROJECT_ROOT}/.codex/skills/pir2/references/plan-choice-gate.md` を参照（検出トリガー / 確認フォーマット / 運用ルール / 別案の字義解釈確認 / v2→v3 切替の真意確認）。

要点: planner レポートに「複数案」「USER_DECISION_REQUIRED」「スコープ縮小」「外部依存不足」のいずれかが含まれたら**ステップ 5 前にユーザー確認必須（Auto mode でも例外なし）**。planner の推奨案を必ず明示する。ユーザーが別案 or 方針切替した場合は `PLAN_STRATEGY_CHANGED=true` をセットして planner を再起動（字義解釈確認を先に実施）。該当なしはスキップしてステップ 5 へ。

---

## ステップ 5: プラン保存

`docs/plans/` ディレクトリがなければ作成し、以下の形式でプランを保存してください:

**保存先**: `docs/plans/YYYY-MM-DD-<feature>.md`（YYYY-MM-DD は今日の日付）

保存したらユーザーにパスを提示:

```
プラン: docs/plans/YYYY-MM-DD-<feature>.md
```

ファイル内容のテンプレート:

```markdown
# [タスク名] 実装記録

_作成: YYYY-MM-DD | ステータス: 進行中_

## 目標

[タスクの概要]

## 実装計画

- [ ] ステップ1: [ステップ名]
- [ ] ステップ2: [ステップ名]
...

---

## 設計詳細

[{RUN_DIR}/plan.md を Read し、その内容をここに転記する]

---

## 実装ログ

### 実装完了

- 変更ファイル: （実装完了後に埋める）
- 実装内容: （実装完了後に埋める）

---

> このドキュメントは内容を確認後に削除してください。
> `rm docs/plans/YYYY-MM-DD-<feature>.md`
```

---

## ステップ 5.5: handoff.md 初期版生成（`RESUME_MODE=new` の場合のみ）

`RESUME_MODE=resume` または `passive-notice` の場合はこのステップをスキップしてください（既存 handoff.md を温存する）。

`RESUME_MODE=new` の場合のみ実行:

1. `{RUN_DIR}/plan.md` を Read し、「実装ステップ」に相当する項目を抽出する
2. `$HANDOFF_PATH` に `~/.codex/pir-handoff.md` の「フォーマット」節に従った内容で Write する:
   - `最終更新`: 現在時刻 + `run: $(basename $RUN_DIR)`
   - `タスク`: ユーザー指示の一行要約
   - `背景・決定事項`: plan.md から抽出した主要決定（なければ空セクションのまま）
   - `残 TODO`: 抽出した実装ステップを `- [ ] <ステップ名>` 形式に変換
   - `既知の問題 / 要確認`: 空セクションで用意
   - `関連 artifact`: `最新 plan: {RUN_DIR}/plan.md`

handoff.md のパスをユーザーに提示:

```
handoff: $HANDOFF_PATH
```

`RESUME_MODE=passive-notice` だった場合はこの時点で「💡 前回の handoff が残っています: `$HANDOFF_PATH`（`引継いで` で resume 可能）」とユーザーに表示してから次ステップへ。

---

## ステップ 5.6: 次ステップキュー初期版生成

詳細プロトコル: `${PROJECT_ROOT}/.codex/skills/pir2/references/next-steps-queue.md` を参照（初期 Write テンプレート / 5.6-2 checkbox 更新手順 / 5.6-3 中断後の Read ルール / スキップ条件）。

要点: `{RUN_DIR}/next-steps.md` にsubagent起動予定 checkbox リストを Write する。**ユーザー会話による中断後、スキル本体は次の判断前に必ずこのファイルを Read してから動く**。各ステップ完了直後に checkbox を `[x]` + `<!-- done: ISO8601 -->` に更新する（必須運用）。`RESUME_MODE=resume` の場合は handoff.md 由来の未完了項目を統合する。

---

## ステップ 5.7: 破壊的変更チェックリスト + 動作変更チェック（worker 起動前に必ず実行）

詳細プロトコル: `${PROJECT_ROOT}/.codex/skills/pir2/references/destructive-change-check.md` を参照（pir2 専用の 2 軸マトリクス判定 / 判定項目 a〜e・f1〜f3 / 書き出しフォーマット / 軽量化確認 / スキップ条件）。

要点: plan.md と explorer レポートを Read して「破壊的変更フラグ（a〜e）」と「動作変更フラグ（f1〜f3）」を独立に判定。結果を `{RUN_DIR}/destructive-change-check.md` に書き出し、後段（reviewer / refactor-advisor / tester）の戦略をマトリクスで決定。フラグ ON で軽量化したい場合はユーザー確認必須。完了後は 5.6-2 に従い next-steps.md の checkbox を更新する。

---

## ステップ 5.8: 直前追加 feedback の自己照合ゲート（実装開始前に必ず実行）

詳細プロトコル: `${PROJECT_ROOT}/.codex/skills/pir2/references/feedback-conflict-gate.md` を参照（feedback Read → プロンプト照合 → 矛盾検出時の中断フォーマット → 記録 → スキップ条件）。

要点: 過去 14 日以内の feedback_*.md 5 件を Read し、実装プロンプト案の除外指示・スコープ縮小と突合。矛盾 1 件でも検出したら実装開始を中断 → ユーザー確認。矛盾なしも `{RUN_DIR}/feedback-conflict.md` に「照合 N 件、矛盾なし」を記録。完了後は 5.6-2 に従い next-steps.md の checkbox を更新する。

---

## ステップ 6: 実装（worker-delegation）

`INNER_LOOP_COUNT = 0`、`OUTER_LOOP_COUNT = 0` から開始してください。

具体的な実作業 actor 契約の SSOT は `${PROJECT_ROOT}/.codex/skills/worker-delegation/SKILL.md` です。このスキルは責任境界、actor ladder、入力ファイル、runner の使い方、Sol による acceptance 実測を同契約に従わせます。PIR² 固有の shard ゲート、adaptive effort、成果物の扱いだけを `${PROJECT_ROOT}/.codex/skills/pir2/references/implementation-delegation.md` に定義します。

要点:

- 通常の具体実装は `worker-delegation` とし、Sol orchestrator が一時ディレクトリに具体的な `task.md`（目的、所有範囲、実装指示、禁止事項）と `requirements.md`（差分・ファイル・コマンドで判定できる `- R<number>:` 要件）を作成してから起動する。Sol orchestrator は対象リポジトリを実装・修正しない。
- **必須の初回 worker** は Luna Max です。runner の actor と effort を明示し、worker に別 actor の選択や自動切替を委ねない。worker raw output と Sol canonical implementation report は別 artifact とし、初回・correction・shard/unit で固有 suffix を割り当てる。
  ```sh
  IMPL_INDEX="01"
  PRE_IMPL_INDEX="$IMPL_INDEX"
  REPORT_SUFFIX="$IMPL_INDEX"
  WORKER_RAW_OUTPUT="$RUN_DIR/worker-output-$REPORT_SUFFIX.md"
  IMPLEMENTATION_REPORT_PATH="$RUN_DIR/implementation-$REPORT_SUFFIX.md"
  ${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/run-worker.sh \
    --actor luna --effort max --cwd "$PROJECT_ROOT" \
    --task-file <task.md> --requirements-file <requirements.md> \
    --output-file "$WORKER_RAW_OUTPUT"
  ```
- **worker provenance は Sol が acceptance または blocker と各 `Rn` を実測・確定した直後に append** します。raw report の `ACTOR` / model / effort は identity の根拠にせず、runner が no-replace 公開した `${WORKER_RAW_OUTPUT}.provenance.tsv` を `record-observation.sh` に渡します。helper の schema、append-only、root 境界は `${PROJECT_ROOT}/.codex/skills/pir2/references/worker-observability.md` と `${PROJECT_ROOT}/.codex/skills/worker-delegation/SKILL.md` を SSOT とし、PIR² 本文で再実装しません。
  ```sh
  JOB_ID="pir2-${REPORT_SUFFIX}"
  WORKER_STATUS="$SOL_MEASURED_WORKER_STATUS"
  SOL_MEASUREMENT_RESULT="$SOL_MEASURED_RESULT"
  MISMATCH_RESULT="$SOL_MEASURED_MISMATCH"
  MISMATCH_REASON="$SOL_MEASURED_MISMATCH_REASON"
  ESCALATION_FROM="$SOL_ESCALATION_FROM"; ESCALATION_TO="$SOL_ESCALATION_TO"; ESCALATION_REASON="$SOL_ESCALATION_REASON"
  EFFORT_ESCALATION_FROM="$SOL_EFFORT_ESCALATION_FROM"; EFFORT_ESCALATION_TO="$SOL_EFFORT_ESCALATION_TO"
  INSUFFICIENCY_CLASS="$SOL_INSUFFICIENCY_CLASS"; INPUT_SUFFICIENT="$SOL_INPUT_SUFFICIENT"; MEASURED_INSUFFICIENCY_REF="$SOL_MEASURED_INSUFFICIENCY_REF"
  "$OBS_HELPER" worker \
    --run-dir "$RUN_DIR" \
    --raw-output "$WORKER_RAW_OUTPUT" \
    --provenance "${WORKER_RAW_OUTPUT}.provenance.tsv" \
    --job-id "$JOB_ID" --index "$REPORT_SUFFIX" --status "$WORKER_STATUS" \
    --sol-measurement-result "$SOL_MEASUREMENT_RESULT" --mismatch "$MISMATCH_RESULT" --mismatch-reason "$MISMATCH_REASON" \
    --escalation-from "$ESCALATION_FROM" --escalation-to "$ESCALATION_TO" \
    --effort-escalation-from "$EFFORT_ESCALATION_FROM" --effort-escalation-to "$EFFORT_ESCALATION_TO" --escalation-reason "$ESCALATION_REASON" \
    --insufficiency-class "$INSUFFICIENCY_CLASS" --input-sufficient "$INPUT_SUFFICIENT" --measured-insufficiency-ref "$MEASURED_INSUFFICIENCY_REF" \
    --task-ref "$TASK_FILE" --requirements-ref "$REQUIREMENTS_FILE" \
    --report-ref "$IMPLEMENTATION_REPORT_PATH" \
    --changed-files-ref "$CHANGED_FILES_REF" --verification-ref "$VERIFICATION_REF"
  ```
- worker 完了直後、Sol は `$WORKER_RAW_OUTPUT` を Read して `ACTOR`、`ACTUAL_MODEL`、`ACTUAL_EFFORT`、`STATUS`、`CHANGED_FILES`、`OBSERVED_RESULTS`、`BLOCKERS`、`ESCALATION_REASON` の canonical 8 fields を確認する。raw を rename/copy するだけではなく、Sol が `git status -sb`、対象 diff、実在ファイル、要求された検証コマンド出力を独立に測定し、`$IMPLEMENTATION_REPORT_PATH` に canonical metadata、正確な `### 変更ファイル一覧`（各項目は backtick path）、`### 注意点・未解決事項` を Write する。raw は CLAIMED source にせず、canonical report のみが deterministic gate と reviewer/tester の入力になる。順序は raw → Sol normalization → deterministic post/CLAIMED → acceptance → reviewer → tester とする。Luna の完了報告・自己申告・runner の終了コードは acceptance の根拠にしない。Sol は実測結果を各 `Rn` の根拠とともに `{RUN_DIR}/sol-acceptance-<IMPL_INDEX>.md` に記録する。
- task/requirements が十分で、Luna の **capability** または **local-reasoning** insufficiency を差分・コマンド出力で実測できた場合だけ、理由・時点・不足内容を記録して Terra High を明示起動する。
  ```sh
  ${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/run-worker.sh \
    --actor terra --effort high --cwd "$PROJECT_ROOT" \
    --task-file <task.md> --requirements-file <requirements.md> \
    --output-file "$WORKER_RAW_OUTPUT"
  ```
- Terra High の同じ原因への再試行を Max に上げるのは **一度だけ**、かつ証拠が `multi-stage causality`、`design contradiction`、`cross-module invariants`、`security/data-integrity risk`、または documented High insufficiency のいずれかを示す場合だけとする。
  ```sh
  ${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/run-worker.sh \
    --actor terra --effort max --cwd "$PROJECT_ROOT" \
    --task-file <task.md> --requirements-file <requirements.md> \
    --output-file "$WORKER_RAW_OUTPUT"
  ```
- Terra High/Max で capability または local-reasoning insufficiency を実測した場合だけ、例外的な **Sol worker subagent** を High で明示起動する。Sol worker が repository を変更する主体であり、Sol orchestrator は変更しない。
  ```sh
  ${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/run-worker.sh \
    --actor sol --effort high --cwd "$PROJECT_ROOT" \
    --task-file <task.md> --requirements-file <requirements.md> \
    --output-file "$WORKER_RAW_OUTPUT"
  ```
- Sol High の同じ原因への再試行を Max に上げるのは **一度だけ**、highest-complexity/high-risk evidence または documented Sol High insufficiency がある場合だけとする。
  ```sh
  ${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/run-worker.sh \
    --actor sol --effort max --cwd "$PROJECT_ROOT" \
    --task-file <task.md> --requirements-file <requirements.md> \
    --output-file "$WORKER_RAW_OUTPUT"
  ```
- requirements、入力不足、環境、権限、external/CLI、一般 blocker は actor の能力不足ではなく、Terra/Sol の effort を上げる理由にしない。これらは `automatic_fallback=no` で Sol orchestrator が入力・判断・環境を解消するか、ユーザーへ blocker として戻す。各段は条件付きであり、Luna → Terra High → Terra Max（証拠時のみ）→ Sol High → Sol Max（証拠時のみ）の全段を必ず実行するものではない。
- reviewer / tester は worker と別系統の判定者であり、worker の自己申告を acceptance、品質、動作の PASS 根拠にしない。実装後の修正も同じ ladder、同じ effort 上限、同じ実測 acceptance を使う。
- planner が `IMPLEMENTATION_SHARDS` を提示し、shard 同士の所有範囲・依存順序・共有生成物が完全に分離している場合のみ、各 shard を独立した `worker-delegation` job として最大3体まで並列実装してよい。各 job に固有の `task.md`、`requirements.md`、raw/canonical artifact を用意し、`REPORT_SUFFIX="${IMPL_INDEX}-shard-${SHARD_ID}"`、`WORKER_RAW_OUTPUT="$RUN_DIR/worker-output-${REPORT_SUFFIX}.md"`、`IMPLEMENTATION_REPORT_PATH="$RUN_DIR/implementation-${REPORT_SUFFIX}.md"` とする。Sol が全 shard の raw を読み、独立測定して各 canonical report を作成した後、canonical report 全件を union して deterministic CLAIMED を求め、acceptance を実測してから統合確認する。条件不成立時は単一の Luna Max 起動に戻す。

reviewer/tester FAIL 後の修正も同じ契約で行います。Sol orchestrator は指摘レポートを Read し、修正用 task/requirements を具体化して worker を起動します。Sol worker への昇格は Terra の capability/local-reasoning insufficiency を実測できた場合だけです。修正を worker に任せたことや worker の報告だけで PASS とせず、修正後も reviewer/tester を別系統で再実行します。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する（`IMPL_INDEX` が複数回ループする場合は最初の 1 回のみマーク。2 回目以降のループは「中断・再開ログ」セクションに追記する）。

---

## ステップ 6.1: 決定論的完了証拠ゲート（必須）

実装 job の完了報告を受けた直後、Sol acceptance と reviewer/tester 起動の前に、必ず `${PROJECT_ROOT}/.codex/skills/worker-delegation/references/deterministic-completion-check.md` を Read してこのゲートを実行してください。worker の自己申告、runner の終了コード、チャット要約だけで次へ進むことは禁止です。

### 6.1-1: 実装開始前の pre-set

各 worker-delegation job（単一 job / shard / review-fix / tester FAIL 後の修正）の開始直前に、`IMPL_INDEX` を決め、`PRE_IMPL_INDEX="$IMPL_INDEX"` を保持したまま job 固有 suffix を決定します。single は `${IMPL_INDEX}`、initial shard は `${IMPL_INDEX}-shard-${SHARD_ID}`、review-fix shard は `${IMPL_INDEX}-review-fix-${REVIEW_FIX_SHARD_ID}`、sequential unit は `${IMPL_INDEX}-unit-${UNIT_ID}` とし、毎回 `WORKER_RAW_OUTPUT="$RUN_DIR/worker-output-${REPORT_SUFFIX}.md"` と `IMPLEMENTATION_REPORT_PATH="$RUN_DIR/implementation-${REPORT_SUFFIX}.md"` を新しい未作成 path に更新します。runner の `--output-file` には raw pathだけを渡し、reference の pre-set bash ブロックを実行します。pre-set は `${RUN_DIR}/verify-${PRE_IMPL_INDEX}-pre.list` に保存し、実装開始後に作り直しません。`git diff`、`git diff --cached`、`git ls-files --others --exclude-standard` を pre/post の両方で union することが必須です。

### 6.1-2: 完了後の canonical report と集合照合

worker の自由形式 raw output（`$WORKER_RAW_OUTPUT`）を Sol が Read し、8 fields を確認した後、Sol が実測したリポジトリ相対の変更ファイルだけを `$IMPLEMENTATION_REPORT_PATH`（single は `${RUN_DIR}/implementation-${IMPL_INDEX}.md`、shard/unit は対応する suffix report）へ、次の見出しを含む canonical report として正規化します。raw の変更申告を信頼して rename/copy するだけではいけません。`git status -sb`、対象 diff、実在ファイル、requirementsごとの検証コマンド出力を独立に確認し、存在しないパスを推測で追加してはいけません。正規化前に deterministic post-set/CLAIMED、acceptance、reviewer、testerへ進んではいけません。

```markdown
### 変更ファイル一覧
- `path/to/changed-file` — 変更概要

### 注意点・未解決事項
なし
```

編集不要の場合は canonical report の変更ファイル一覧を `なし` とし、注意点・未解決事項に `NO_OP_JUSTIFIED: <理由>` を記録します。その後、canonical reportだけを source にして reference の post-set / delta / CLAIMED 抽出ブロックを実行し、`${RUN_DIR}/verify-${IMPL_INDEX}.md` に判定を記録します。shard/unit の場合は canonical report 全件を union し、raw report は union に含めません。

判定は次のとおりです。

- `phantom.list` が空でない場合は `PHANTOM_CLAIM`（hard fail）。reviewer を起動せず、原因を含む verifier report を worker に渡して、`PRE_IMPL_INDEX` を据え置いたまま `IMPL_INDEX` を増やして1回だけ再実行できます。
- 2回目も `PHANTOM_CLAIM` の場合は自動で進めず、`${RUN_DIR}/user-decisions.md` に記録してユーザー確認を待ちます。git の変更を自動で巻き戻してはいけません。
- `undeclared.list` が空でない場合は `UNDECLARED_CHANGE` の warn として記録し、実際の変更ファイルを Sol が確認します。warn だけを理由に差分を隠したり、申告集合を推測で補ったりしてはいけません。
- 上記以外は `PASS` とし、Sol acceptance の evidence path に verifier report、pre/post/delta list を記録してからステップ 6.5 と reviewer へ進みます。

Sol acceptance を確定したら、requirements の **各 `Rn` を省略せず** helper へ一行ずつ append します。`ACCEPTANCE_REF` は実際の `${RUN_DIR}/sol-acceptance-<IMPL_INDEX>.md`（および verifier / command output）を指し、worker status や runner exit code を `acceptance_basis` にしてはいけません。

```sh
for REQUIREMENT_ID in $REQUIREMENT_IDS; do
  # REQUIREMENT_IDS は requirements.md から抽出した R<number> の集合。
  "$OBS_HELPER" acceptance \
    --run-dir "$RUN_DIR" --job-id "$JOB_ID" --index "$REPORT_SUFFIX" \
    --requirement-id "$REQUIREMENT_ID" --verdict "$REQUIREMENT_VERDICT" \
    --evidence-ref "$ACCEPTANCE_REF" --evidence-summary "$EVIDENCE_SUMMARY"
done
```

再実装・shard/unit も同じ規則で、各 job/attempt の acceptance ledger 行を新しい attempt として追加します。ledger の列定義と `PASS|FAIL` / `R<number>` 制約は worker-observability SSOT に従います。

このゲートは Luna、Terra、Sol worker のいずれの実装 attempt でも省略しません。reviewer / tester FAIL 後の修正 job では、その job の直前に新しい pre-set を記録し、完了後に同じ照合を再実行します。最終的な verifier の構文と8シナリオは、次で確認できます。

```bash
bash "${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/verify-deterministic-check.sh"
```

完了後はステップ 5.6-2 に従って next-steps.md のステップ 6.1 checkbox を `[x]` に更新します。初期キューにステップ 6.1 がない場合は、ステップ 6 と 6.5 の間に追加してから完了印を付けます。

---

## ステップ 6.5: worker の未解決事項ユーザー確認（該当時のみ）

worker の返り値要約で「注意点・未解決事項の有無」が **「あり」** の場合、次ステップへ進む前に必ずユーザーに判断を仰ぐ。スキル本体がスコープ縮小や仕様変更を独断してはならない。

### 6.5-1: 内容の確認

1. `{RUN_DIR}/implementation-{最新 IMPL_INDEX}.md` の「注意点・未解決事項」セクションを Read する
2. 未解決事項の性質を分類する:
   - **(a) プラン逸脱の報告**（プランの一部が実装できなかった / 前提が崩れた）
   - **(b) プラン通りに実装したが新たに発見した問題**（スコープ外の副次的な気づき）
   - **(c) 判断を委ねる事項**（worker が明示的に「planner/ユーザーに判断を委ねる」と記載した箇所）

### 6.5-2: ユーザーへの提示

未解決事項の要点と分類を1〜3文で要約し、以下の選択肢を提示してユーザーの判断を受け取る:

- **(A) スコープ縮小を承認してレビューへ進む**: 未解決事項を次フェーズ繰越しとして記録し、ステップ 7 へ。`docs/plans/YYYY-MM-DD-*.md` の「注意点・未解決事項」セクションにも繰越し内容を明記する
- **(B) 再プラン**: ステップ 4 に戻り、planner に現在の implementation 状態と未解決事項を渡してプラン再策定（設計の切り替え）。`{RUN_DIR}/implementation-{最新}.md` のパスも planner に渡すこと
- **(C) 追加指示で再実装**: worker-delegation の actor ladder に戻り、ユーザーからの追加指示を渡して再試行。`IMPL_INDEX` をインクリメントする

### 6.5-3: 判断の記録

ユーザーの選択と理由を `{RUN_DIR}/user-decisions.md` に追記する（ファイルがなければ作成）。形式:

```
## [YYYY-MM-DD HH:MM:SS] 未解決事項ユーザー確認

### 未解決事項の要約
[1〜3文]

### 選択
[A / B / C]

### 理由（ユーザーから得られた場合）
[理由]
```

### 6.5-4: スキップ条件

worker の返り値要約で「注意点・未解決事項の有無」が **「なし」** の場合は本ステップをスキップし、ステップ 7 へ直接進む。

> **重要**: 仕様変更判断（スコープ縮小・フェーズ繰越し・API 変更等）はスキル本体ではなくユーザーに委ねる。「小さな変更だから」「代替経路で動くから」を理由にユーザー確認を省略してはならない。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。スキップした場合も「スキップ済み」として `[x]` にする。

---

## ステップ 7: レビューループ（reviewer ハイブリッド並列、最大3回）

### 7-1: 観点セット決定

`REVIEWER_SET` を決定する（planner 系スキルなのでデフォルトは全 5 観点固定）:

1. **ユーザーフラグのパース**: `$ARGUMENTS` に `--reviewers=<roles>` が含まれていればカンマ区切りを観点集合として採用（未知 role は無視）。`--all-reviewers` が含まれていれば全 5 観点を採用。両方指定時は `--reviewers=` を優先
2. **フラグ未指定時のデフォルト**: 全 5 観点 `[correctness, consistency, quality, security, architecture]`（planner が動くタスクは設計判断・多ファイル変更を含むため）
3. フラグ抽出後の残り文字列をタスク説明として扱う（以降のサマリ等で `$ARGUMENTS` をそのまま使っていた箇所は、フラグ除去後のタスク説明を使う）
4. 決定した `REVIEWER_SET` を最終サマリーに `REVIEWER_SET=correctness,consistency,...` として記録

### 7-2A: 起動宣言（Fan-Out Gate — 並列レビューの直前に必ず書く）

reviewer 並列起動または Sol orchestrator による read-only 複数観点レビューの **直前のターン本文中** に、以下のテンプレートを必ず生成すること。このテンプレートが本文に出現していないターンでレビューを開始した場合は、ステップ完了判定を取り消して 7-2A からやり直す。

> **Fan-Out Gate（reviewer）**
> - REVIEWER_SET = [<観点をカンマ区切りで全列挙>]
> - 起動体数 = <N>（= len(REVIEWER_SET)、必ず一致）
> - subagent 利用時: 同一ターンで <N> 個の `spawn_agent`（`agent_type="reviewer"`）を起動する
> - subagent 非利用時: Sol orchestrator が <N> 観点を同一レビューサイクル内で read-only 実行する
> - 1 体ずつの後追い起動・観点削減はいずれも違反

このブロックは「レビュー直前の自己コミットメント」であり、ユーザーへの報告ではなく観点漏れを止めるためのフェンスとして機能する。再レビュー時（7-4 からの差し戻し時）にも毎回この宣言を書くこと。REVIEWER_SET は初回選定を維持し、再レビュー時に観点を勝手に減らさないこと。

### 7-2B: 並列レビュー実行

直前ターンで宣言した REVIEWER_SET の各観点について、subagent が利用可能なら `spawn_agent` に `agent_type="reviewer"` を渡して同一ターンで **N 個** 起動する。モデル引数は指定せず、`.codex/agents/reviewer.toml` の role 定義に委ねる。subagent が利用できない場合は、Sol orchestrator が各 `REVIEWER_ROLE` の観点を read-only で分割して同一レビューサイクル内で実行し、`{RUN_DIR}/review-{REVIEW_INDEX}-{ROLE}.md` を観点ごとに書き出す。

詳細仕様（観点マッピング / 違反パターンと検出 / 違反検出時のリカバリ / reviewer 起動パラメータ）: `${PROJECT_ROOT}/.codex/skills/pir2/references/fan-out-gate.md` を参照。

> **注**: refactor-advisor はこのステップでは起動しない。reviewer 全員 PASS 後のステップ 7.5 で 1 回だけ起動する。

### 7-3: VERDICT 集約

**今回起動した reviewer** の VERDICT を以下のルールで集約する。まず
`REVIEWER_SET` の各 role について、当該レビューサイクルの個別 report と
明示的な VERDICT を確認する。report の欠落、未報告、判定不能、`PASS` 以外の
VERDICT、または未解決の Critical / High は reviewer gate の non-PASS として
扱い、見落としや後段への持ち越しを許さない。

- **全体 VERDICT = PASS**: `every reviewer in REVIEWER_SET returns PASS`、かつ
  未解決の Critical / High がない場合だけ
- **全体 VERDICT = FAIL**: 1 role でも non-PASS、未報告、判定不能、または
  未解決の Critical / High がある場合

各 reviewer の verdict は、Sol が report と実行 provenance を確認した直後に
独立 ledger へ append します。worker の自己申告を reviewer の identity / verdict
に流用せず、実測した model / effort と実在 report path を渡してください。
reviewer を起動しなかった場合は、行を捏造しません。

```sh
for REVIEW_ROLE in $REVIEWER_SET; do
  REVIEW_VERDICT="$SOL_MEASURED_REVIEW_VERDICT"
  REVIEW_REPORT_PATH="$RUN_DIR/review-${REVIEW_INDEX}-${REVIEW_ROLE}.md"
  "$OBS_HELPER" verdict \
    --run-dir "$RUN_DIR" --job-id "$JOB_ID" --target-attempt-index "$REPORT_SUFFIX" --cycle "$REVIEW_INDEX" \
    --role "$REVIEW_ROLE" --verdict "$REVIEW_VERDICT" \
    --report-ref "$REVIEW_REPORT_PATH" \
    --model "$REVIEW_ACTUAL_MODEL" --effort "$REVIEW_ACTUAL_EFFORT" --evidence-ref "$REVIEW_EVIDENCE_REF" \
    --sol-acceptance-ref "$ACCEPTANCE_REF"
done
```

### 7-4: 判定

- 全体 `VERDICT: PASS` → ステップ 7.5 へ（refactor-advisor の起動 + 提案ゲート）
- 全体 `VERDICT: FAIL` →
  1. `INNER_LOOP_COUNT += 1`
  2. `INNER_LOOP_COUNT >= 3` で、1 role でも non-PASS、未報告、判定不能、または未解決の Critical / High が残る場合は、**overall FAIL** として直ちに停止する。各 role の未解決事項を report から列挙してユーザーに報告し、ユーザーの判断を求める。この retry-cap hard stop では refactor-advisor、tester、または成功完了を進めない。追加の修正 job や再レビューで上限を回避してはならない。
  3. 上限未到達の場合だけ実装修正を行う（`IMPL_INDEX` をインクリメントし、`PRE_IMPL_INDEX` と review-fix suffix を更新して固有の `WORKER_RAW_OUTPUT` / `IMPLEMENTATION_REPORT_PATH` を作成する。**FAIL を返した全 reviewer の `{RUN_DIR}/review-{最新}-{ROLE}.md` パスを全て読む**、`{RUN_DIR}/plan.md` も読む。マージ要約は作らず、各レポートを直接根拠にする）。修正用の `task.md` / `requirements.md` を Sol orchestrator が具体化し、`${PROJECT_ROOT}/.codex/skills/pir2/references/implementation-delegation.md` の review-fix shard ルールに従って各修正 job をまず Luna Max へ渡す。runner の `--output-file` は raw pathだけにし、完了後は raw → Sol normalization → deterministic gate → acceptance の順で進める。分離できない場合も単一の worker-delegation job として actor ladder を開始する。Terra High/Max、Sol High/Max はそれぞれの capability/local-reasoning evidence がある場合だけ明示起動し、修正後の acceptance は必ず差分とコマンドで Sol が実測する
  4. **7-2A（Fan-Out Gate 宣言）→ 7-2B（並列発火）の手順で** reviewer を **同じ REVIEWER_SET で** 並列で再起動（`REVIEW_INDEX` をインクリメント、最新の `{RUN_DIR}/implementation-{最新}.md` のパスを渡す。PASS を返した観点も再レビューする = 修正による新たな退行を検知するため。観点集合は初回選定を維持し途中で追加・削除しない。**再レビュー時も Fan-Out Gate を省略しないこと**）
  5. 全体 PASS になるまで繰り返す（上限到達時は 2. の hard stop に従う）

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する（複数回ループで `REVIEW_INDEX` が増えた場合は最初の 1 回のみマーク、ループ詳細は「中断・再開ログ」に追記）。

---

## ステップ 7.5: リファクタ提案（refactor-advisor 起動 → ゲート → 任意適用）

`REVIEWER_SET` の every reviewer が PASS を返し、未解決の Critical / High が
ない全体 VERDICT PASS の場合のみ実行する。reviewer の retry-cap hard stop は
このステップへ入らず、refactor-advisor、tester、成功完了のいずれにも進まない。

詳細プロトコル: `${PROJECT_ROOT}/.codex/skills/pir2/references/refactor-advisor-gate.md` を参照（refactor-advisor 起動仕様 / 提案存在確認 / ユーザー提示フォーマット / ユーザー選択の処理 / リファクタ適用の worker 再起動 / 退行検知の再 reviewer ループ）。

要点:
- refactor-advisor は **1 体だけ起動**（reviewer 並列とは別系統、直列）
- 提案がある場合のみユーザーゲートを開く（`all` / 番号指定 / `none` / `custom`）
- 適用後は **7-2A（Fan-Out Gate 宣言）→ 7-2B（並列発火）** で reviewer 再起動し退行検知
- 再 reviewer FAIL なら 7-4 の差し戻しループに合流（`INNER_LOOP_COUNT` 継続）
- refactor-advisor は同一 run 内 **1 回のみ**（無限リファクタループ防止）

### 完了後

ステップ 5.6-2 に従い、refactor-advisor ゲートを実行して通常の後続条件を満たした場合だけ
`{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。reviewer の retry-cap
hard stop では checkbox を完了扱いにせず、overall FAIL と未解決事項を「中断・再開ログ」に記録する。

---

## ステップ 8: テストループ（tester、最大3回）

### 8-1: tester 起動

tester は、`REVIEWER_SET` の every reviewer が PASS を返し、未解決の Critical / High がない
reviewer gate PASS の後にだけ起動できる。reviewer の non-PASS または retry-cap hard stop
からテストへ進むことは禁止する。テストは read/log-heavy なので、subagent が利用可能なら
`spawn_agent(agent_type="tester")` で `tester` role を起動する。モデル引数は指定せず、
`.codex/agents/tester.toml` の role 定義に委ねる。利用できない場合は Sol orchestrator が同じ仕様で
実行する。起動仕様（プロンプトに含めるパラメータ一覧）は
`${PROJECT_ROOT}/.codex/skills/pir2/references/tester-prompt.md` を参照。`TEST_INDEX` は初回 `01`、
再テスト時はインクリメント。

### 8-2: 判定

- `VERDICT: PASS` → ステップ 9 へ
- `VERDICT: FAIL` →
  1. `OUTER_LOOP_COUNT += 1`
  2. `OUTER_LOOP_COUNT >= 3` の場合は **続行可能ゲート（8-2-G）** へ。上限到達は overall FAIL の hard stop として記録し、ユーザー判断を待つ（tester PASS なしに成功完了へ移行しない）。ユーザーが追加修正を明示承認した場合だけ 3. の correction cycle を1回追加できる
  3. `INNER_LOOP_COUNT = 0` にリセット
  4. 実装修正を行う（`IMPL_INDEX` をインクリメントし、`PRE_IMPL_INDEX` と suffix を更新して固有の `WORKER_RAW_OUTPUT` / `IMPLEMENTATION_REPORT_PATH` を作成し、`{RUN_DIR}/test-{最新}.md` のパスを tester 指摘事項として読む）。Sol orchestrator が tester の指摘から修正用 `task.md` / `requirements.md` を具体化し、まず Luna Max の worker-delegation job を起動して acceptance を実測する。runner の `--output-file` は raw pathだけにし、完了後は raw → Sol normalization → deterministic gate → acceptance → reviewer → tester の順に進める。分離可能な shard の扱いは `${PROJECT_ROOT}/.codex/skills/pir2/references/implementation-delegation.md` の再実装ルールに従う。Terra High/Max、Sol High/Max への昇格はそれぞれ capability/local-reasoning evidence がある場合だけとする
  5. **ステップ 7 に戻る**（レビューループを再実行、`REVIEW_INDEX` は継続インクリメント。以前に PASS だった role を含む `REVIEWER_SET` の every reviewer を再実行する）
  6. tester を再起動（`TEST_INDEX` をインクリメント）
  7. PASS になるまで繰り返す

各 tester の判定も Sol が report と実行 provenance を確認した直後に独立 ledger
へ append します。これは reviewer / worker acceptance とは別の verdict であり、
`sol-acceptance-v1.tsv` の判定を上書きしません。

```sh
"$OBS_HELPER" verdict \
  --run-dir "$RUN_DIR" --job-id "$JOB_ID" --target-attempt-index "$REPORT_SUFFIX" --cycle "$TEST_INDEX" \
  --role tester --verdict "$TEST_VERDICT" \
  --report-ref "$TEST_REPORT_PATH" \
  --model "$TEST_ACTUAL_MODEL" --effort "$TEST_ACTUAL_EFFORT" --evidence-ref "$TEST_EVIDENCE_REF" \
  --sol-acceptance-ref "$ACCEPTANCE_REF"
```

### 8-2-G: 続行可能ゲート（OUTER_LOOP_COUNT 上限到達時のみ）

詳細プロトコル: `${PROJECT_ROOT}/.codex/skills/pir2/references/continuation-gate.md` を参照（4 条件の判定基準 / ユーザー確認フォーマット / 運用ルール）。1 条件でも欠ける場合、またはユーザーが停止を選んだ場合は overall FAIL を報告して hard stop とする。ユーザーが追加修正を明示承認した場合だけ、worker correction → deterministic gate → acceptance → 全 reviewer → tester の一周を追加する。追加周回でも tester が PASS しなければ成功完了へ進めない。**Auto mode でも本ゲートはユーザー応答を待つ**（仕様変更判断ゲートのため Auto mode 例外）。1 サイクル中に通過できるのは最大 1 回のみ。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する（複数回ループで `TEST_INDEX` が増えた場合も同様、最初の 1 回のみマーク）。

---

## ステップ 9: ウォークスルー生成（Sol orchestrator の read-only 確認）

変更されたファイルを Read して最終的な実装内容を確認し、ウォークスルーを作成する。フル版（内部記録）とサマリー版（最終サマリーに転記）の 2 形式を作成し、フル版は実装記録ドキュメント（ステップ 5 で作成）の「実装ログ」セクションに埋める。

詳細テンプレート（フル版・サマリー版・サマリー版の原則）: `${PROJECT_ROOT}/.codex/skills/pir2/references/walkthrough-templates.md` を参照。

最重要原則: **推測でコードを書かない。実際に Read したコードのみ引用する**。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。

---

## ステップ 10: メモリへの記録

`PROJECT_MEMORY_DIR` 配下にタスクの振り返り材料を追記します:

- まず `mkdir -p {PROJECT_MEMORY_DIR}` でディレクトリを作成
- パス: `{PROJECT_MEMORY_DIR}/pir_skill_log.md`
- フォーマット: `## [タスク名] — [気づき・課題・パターン]`
- **モデル/実行形態スイープ計装**（後日「どのフェーズを安価モデルに下げられるか」「subagent を使う価値があるか」を判断する素材。機械集計しやすいよう固定プレフィックスで必ず1行記録する）:
  `- 使用モデル: explorer=<model×体数>, planner=<model>, worker=<actor:model:effort>, reviewer=<model×体数>, tester=<model>, retrospector=<model> / REPLAN=<N> / INNER_LOOP=<N> / OUTER_LOOP=<N>`
  今回 run で各フェーズを**実際に実行した形態**を埋める。worker は `luna:gpt-5.6-luna:max`、`terra:gpt-5.6-terra:high|max`、`sol:gpt-5.6-sol:high|max` の実測値を記録し、Sol worker を使わない場合は `none` とする。スイープ実験本体は計装でデータが溜まってから別途行う。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。

---

## ステップ 11: 振り返り（retrospector、常に実行）

振り返りは Sol orchestrator が実行してよい（run artifact とログの read/write のみ）。subagent が利用可能で、今回 run が大きくログ分析を分離した方がよい場合のみ `retrospector` を起動する。起動仕様（model 切替条件 / プロンプトに含めるパラメータ一覧 / 起動後の処理）は `${PROJECT_ROOT}/.codex/skills/pir2/references/retrospector-prompt.md` を参照。`/pir2` では `ワークフロー種別: pir2` を明示し、`PLAN_STRATEGY_CHANGED` の現在値も渡すこと（true なら今回 run でユーザー方針切替が発生し planner v1→v2 再策定が走った）。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。

---

## ステップ 11.5: handoff.md 完了判定と後処理

詳細プロトコル: `${PROJECT_ROOT}/.codex/skills/pir2/references/handoff-cleanup.md` を参照。要点: `$HANDOFF_PATH` が存在する場合、全 `[x]` なら削除、残項目ありなら `最終更新` 行を更新する。最終サマリーに結果を記載すること。`$HANDOFF_PATH` が存在しない場合はスキップ。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。全 checkbox が `[x]` になった場合は最終サマリー（ステップ 12）に「next-steps.md: 全項目完了」と記載する。

---

## ステップ 12: 最終サマリーの提示

詳細テンプレートは `${PROJECT_ROOT}/.codex/skills/pir2/references/final-summary-template.md` を参照。実装記録、変更ファイル、レビュー結果、refactor-advisor 結果、テスト結果、再探索回数、RUN_DIR、振り返り、メタ改善推奨を含める。

---

## ステップ 13: ウォークスルーの提示

ステップ9で作成したサマリー版ウォークスルーをユーザーに提示してください。フル版は内部記録として保持し、ユーザーから「詳細を見せて」等の要求があれば提示します。

末尾に `詳細なウォークスルーが必要な場合はお知らせください。` と添えてください。
