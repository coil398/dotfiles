---
name: "writing-plan"
description: "実装計画を作成し、各ステップの実施結果を追記して実装記録として残す。『計画を立てて』『段階的に実装して』『実装記録を残したい』や /writing-plan で使う。"
argument-hint: "[タスクの説明]"
---

# ライティングプラン — 計画 → 実装 → 記録

**タスク**: $ARGUMENTS

Astra parent（`gpt-6-astra` / `high`）が探索、計画、scope、依存関係、所有範囲、受入条件、統合、最終判断を所有します。小さく全体文脈と分離できない変更は Astra が直接実装できます。独立した通常作業は [worker-delegation](../worker-delegation/SKILL.md) に従って worker（Luna Max）へ委譲し、原因・状態・競合・性能など推論中心の難所は expert / expert_max（Sol High/Max）を最初から選べます。Terra は同種 workload の実測で優位性がある場合だけの例外です。

計画書は実装中に更新し、最終的に実装記録として残します。

参照先は対象リポジトリではなく、読込済みの本 `SKILL.md` の実体から解決します。親はその絶対パスを `THIS_SKILL_PATH` として確定し、`CODEX_SKILLS_DIR="$(cd "$(dirname "$THIS_SKILL_PATH")/.." && pwd -P)"` を使います。

## 0. RUN_DIR の確定

```bash
PROJECT_ROOT="$(pwd -P)"
sanitized_cwd="$(printf '%s' "$PROJECT_ROOT" | sed 's|[^a-zA-Z0-9]|-|g')"
PROJECT_MEMORY_DIR="${HOME:?HOME is required}/.codex/projects/${sanitized_cwd}/memory"
run_ts="$(date +%Y%m%d-%H%M%S)"
run_feature="$(printf '%s' "$ARGUMENTS" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
[ -z "$run_feature" ] && run_feature="task"
RUN_ROOT="${HOME:?HOME is required}/.ai-pir-runs"
[ -d "$HOME" ] || { echo "HOME must be a directory" >&2; exit 1; }
for run_parent in "$RUN_ROOT" "$RUN_ROOT/$sanitized_cwd"; do
  if [ -e "$run_parent" ] || [ -L "$run_parent" ]; then
    [ -d "$run_parent" ] && [ ! -L "$run_parent" ] || exit 1
  else
    (umask 077; mkdir "$run_parent") || exit 1
  fi
done
RUN_PREFIX="${RUN_ROOT}/${sanitized_cwd}/${run_ts}-${run_feature}"
RUN_DIR="$RUN_PREFIX"
run_collision=0
while ! (umask 077; mkdir "$RUN_DIR") 2>/dev/null; do
  [ -e "$RUN_DIR" ] || [ -L "$RUN_DIR" ] || exit 1
  run_collision=$((run_collision + 1))
  RUN_DIR="${RUN_PREFIX}-${run_collision}"
done
echo "PROJECT_ROOT=$PROJECT_ROOT"
echo "PROJECT_MEMORY_DIR=$PROJECT_MEMORY_DIR"
echo "RUN_DIR=$RUN_DIR"
```

sanitized-cwd の規則は `${CODEX_SKILLS_DIR}/pir2/references/sanitized-cwd.md` を SSOT とします。`/writing-plan` は handoff 連携を行わないため、`HANDOFF_PATH` / `RESUME_MODE` は不要です。

native collaboration または Astra の直接実装では runner 用の台帳、固定 fixture、canonical implementation report を作りません。明示的な CLI runner と artifact/provenance が必要な job だけ worker-delegation の runner 契約を適用し、既存の artifact・ledger schema をその job の実測結果に使います。

## 1. 計画の作成

Astra がリポジトリ、既存仕様、関連する `docs/brainstorm/` と既存 artifact を read-only で探索し、`{RUN_DIR}/plan.md` を作成します。追加探索を委譲した場合は report を読み、Astra が計画へ統合します。

計画には次を記載します。

- 目標、非目標、確認済みの事実
- bite-sized なステップと完了条件
- 各ステップの対象ファイル、排他的所有範囲、変更禁止範囲
- 依存 DAG と独立して並列化できる単位
- `R1` から始まる測定可能な requirements
- 変更が影響する挙動と、それを確認する検証
- reviewer / tester / runner が必要な場合は、その具体的なリスクと目的

既存の `plan.md` やユーザーの方針変更がある場合、決定済み事項と完了項目を保持し、影響する scope、DAG、requirements、ステップだけを増分更新します。計画全体を作り直しません。

`$ARGUMENTS` に `--deepplan` または `deepplan` が明示されている場合だけ `${CODEX_SKILLS_DIR}/deepplan/SKILL.md` を同じ `RUN_DIR` で実行し、Astra が結果を統合します。

## 2. 実装記録の初期化

`docs/plans/` がなければ作成し、`docs/plans/YYYY-MM-DD-<feature>.md` を次の形式で保存します。保存直後に `プラン: <path>` をユーザーへ提示します。

```markdown
# [タスク名] 実装記録

_作成: YYYY-MM-DD | ステータス: 進行中_

## 目標

[タスクの概要]

## 実装計画

- [ ] ステップ 1: [ステップ名]
- [ ] ステップ 2: [ステップ名]

## 設計詳細

[`{RUN_DIR}/plan.md` の対象、変更理由、依存関係、受入条件、検証]

## 実装ログ
```

ブレインストーム設計がある場合は参照先を記録します。

## 3. 実装・確認・追記

各ステップについて次を行います。

1. Astra が変更の密結合度、難度、所有境界から直接実装、worker、expert / expert_max のいずれかを選ぶ。
2. 委譲時は目的、確認済み事実、所有範囲、制約、変更禁止範囲、終了条件、焦点を絞った確認、返却事項を渡す。独立した単位だけを並列化し、同じファイルを複数担当へ同時に割り当てない。
3. Astra が `git status`、対象 diff、実在する変更ファイル、requirements と検証出力を確認する。worker の自己申告や終了コードだけを acceptance とみなさない。
4. 受入後、チェックボックスを `[x]` にし、変更ファイル、実装内容、確認結果、未確認事項を実装ログへ追記する。

入力不足、要件未決定、権限、環境、CLI failure は actor の能力不足として扱いません。まず Astra が入力と scope を直し、実測した capability / local-reasoning 不足がある場合だけ expert へ切り替えます。自動 fallback は行いません。

明示的な runner job では、その job に必要な raw report、canonical report、pre/post/CLAIMED、provenance、ledger だけを worker-delegation の SSOT に従って生成します。通常の native/direct job に未生成 index や artifact を要求しません。runner の安全境界、権限検査、fail-closed を弱めず、artifact の虚偽申告は受入前に修正します。

## 4. リスクに応じたレビューとテスト

Astra は各ステップの実差分から、失敗時の具体的な実害を挙げて必要な確認を選びます。

- correctness: 挙動、データ、制御フロー、要件充足に影響する変更
- security: 認証、認可、秘密情報、入力境界、権限、依存・実行設定に影響する変更
- architecture / consistency: 公開契約、SSOT、複数モジュール、生成元と生成物にまたがる変更
- quality: 可読性・保守性の問題が correctness や将来の安全な変更へ具体的に影響する場合
- ui-ux: UI、操作、状態表示、アクセシビリティに影響する変更

複数の独立した観点が必要なら reviewer を並列起動します。全5観点の固定、起動前宣言、観点数不一致による完了取消は行いません。小さな文書変更や機械的変更は Astra の diff 確認だけで受け入れてよく、高リスクまたは広範な変更は必要な reviewer を追加します。reviewer を使った場合だけ実在する diff、plan、必要なら runner artifact を渡し、report と判定を記録します。

テストは変更が影響する挙動を検証します。既存の焦点を絞ったテスト、静的・構文・設定検証、必要な回帰テストを選び、無関係な全テストを一律に繰り返しません。OS / security / 権限境界、データ損失、生成物、公開契約へ影響する場合は対応する安全チェックを省略しません。tester の独立判定が実害の検出に有効な変更では tester を使います。

FAIL 時は根本原因を特定し、plan と requirements の影響箇所だけを更新して修正します。修正後は影響を受けた reviewer 観点と挙動だけを再確認し、変更と無関係な PASS 済み確認を機械的に全再実行しません。同じ blocker が続き安全に進めない場合は、実測結果と不足する判断をユーザーへ返します。

任意の refactor-advisor 提案は本タスクの完了条件に混ぜず、適用前にユーザー承認を得ます。外部送信、本番変更、破壊的操作、OS / security / 権限境界の変更は、計画に書かれていても必要な明示承認を別途得ます。

## 5. 最終化

全ステップの requirements と必要な確認を満たしたら、ヘッダーを次へ更新します。

```markdown
_作成: YYYY-MM-DD | ステータス: **完了** YYYY-MM-DD_
```

末尾に総括を追加します。

```markdown
## 総括

- 完了ステップ数: N/N
- 実行したレビュー: [観点と対象。不要なら「なし」]
- 実行したテスト: [変更挙動と結果]
- 未確認事項: [なければ「なし」]

> このドキュメントは内容を確認後に削除してください。
```

今回のセッションで完了しない場合は完了扱いにせず、次を記録して残します。

```markdown
## 次セッションへの引き継ぎ

### 完了したもの
- [変更・追加したファイル]

### 未完了と次の作業
- [作業] — 前提 / blocker: [...]

### スコープ外
- [項目] — 理由: [...]

### 設計から変更した点
- [変更点] — 理由: [...]
```

設計書は不変の全体像、実装記録はセッション単位の進捗として扱います。最後にタスク、実装記録パス、完了ステップ、実施したレビュー・テスト、未確認事項を簡潔にユーザーへ提示します。
