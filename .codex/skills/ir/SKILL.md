---
name: "ir"
description: "軽量な Implement → Review の2フェーズワークフロー。タスクが明確で小さい場合に使う。バグ修正・小機能追加・設定変更・ファイル修正など、計画不要で「サクッとやって」「これ直して」「簡単な変更」といった要望に対応する。ユーザーが /ir と入力したら必ずこのスキルを使う。"
argument-hint: "[タスクの説明]"
---

# IR — Implement → Review

軽量ワークフローを実行します。プランニング・振り返りなしで、小さいタスクに使います。Astra（スキル本体）は実装範囲と要件を具体化し、全体文脈と分離できない小変更は直接実装できます。独立して明確に切り出せる変更は共通の [worker-delegation 契約](../worker-delegation/SKILL.md) に従って native collaboration の worker（Luna Max）へ委譲し、難所は expert（Sol high/max）を最初から選べます。reviewer / tester は worker とは別系統で起動し、品質・動作判定を担当します。

**タスク**: $ARGUMENTS

---

## ステップ 0: プロジェクトメモリパスと RUN_DIR の確定

本 `SKILL.md` の実体パスから親の親を `CODEX_SKILLS_DIR` として確定する。対象 repo 内に Skills があると仮定しない。

以下の Bash コマンドで `PROJECT_ROOT` / `PROJECT_MEMORY_DIR` / `RUN_DIR` を確定し、以降のすべてのステップで使用してください:

```bash
PROJECT_ROOT="$(pwd -P)"
# sanitized-cwd 計算は ${CODEX_SKILLS_DIR}/pir2/references/sanitized-cwd.md を SSOT とする
# （Codex harness の sanitize 仕様変更時はこの SSOT のみを更新し、9 ファイルに横展開）
sanitized_cwd="$(printf '%s' "$PROJECT_ROOT" | sed 's|[^a-zA-Z0-9]|-|g')"
PROJECT_MEMORY_DIR="${HOME:?HOME is required}/.codex/projects/${sanitized_cwd}/memory"
run_ts="$(date +%Y%m%d-%H%M%S)"
run_feature="$(printf '%s' "$ARGUMENTS" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
[ -z "$run_feature" ] && run_feature="task"
RUN_ROOT="${HOME:?HOME is required}/.ai-pir-runs"
for run_parent in "$RUN_ROOT" "$RUN_ROOT/$sanitized_cwd"; do
  if [ -e "$run_parent" ] || [ -L "$run_parent" ]; then
    [ -d "$run_parent" ] && [ ! -L "$run_parent" ] || exit 1
  else
    (umask 077; mkdir "$run_parent") || exit 1
  fi
done
run_prefix="$RUN_ROOT/$sanitized_cwd/$run_ts-$run_feature"
RUN_DIR="$run_prefix"
run_collision=0
while ! (umask 077; mkdir "$RUN_DIR") 2>/dev/null; do
  [ -e "$RUN_DIR" ] || [ -L "$RUN_DIR" ] || exit 1
  run_collision=$((run_collision + 1))
  RUN_DIR="$run_prefix-$run_collision"
done
echo "PROJECT_ROOT=$PROJECT_ROOT"
echo "PROJECT_MEMORY_DIR=$PROJECT_MEMORY_DIR"
echo "RUN_DIR=$RUN_DIR"
```

`/ir` は handoff 連携を行わないため、`HANDOFF_PATH` / `RESUME_MODE` は不要です。

### 共通 observability

native collaboration または Astra の直接実装では、この補助台帳を初期化しません。明示的な CLI runner が artifact/provenance を必要とする job の場合だけ、`worker-delegation` の runner と observability SSOT に従います。

---

## ステップ 1: 経路選択と実装

IR の軽量性を保つため、Astra は task を読んで次のいずれかを選びます。

- 小さく全体文脈と分離できない変更: Astra が対象ファイルを直接変更し、`git diff` と必要最小限の確認を行う。
- 所有範囲と終了条件が明確な独立変更: native collaboration の `worker`（`gpt-5.6-luna` / `max`）へ委譲する。
- 原因・状態・競合・性能・厳しい互換性など難所が事前に分かる変更: `expert`（`gpt-5.6-sol` / `high`）または `expert_max`（`max`）へ直接委譲する。Luna や Terra を先に試す必要はない。
- Terra は標準経路に含めず、同種 workload の実測で明確な利点がある場合だけ worker-delegation の例外として親が明示する。

委譲する場合だけ `${CODEX_SKILLS_DIR}/worker-delegation/SKILL.md` の短い入力契約（目的、所有範囲、制約、終了条件、焦点を絞った確認、blocker）を使います。runner が必要な artifact/provenance job 以外では CLI runner、canonical report、deterministic gate、台帳を追加しません。runner を選んだ場合の actor、8 項目 report、`PHANTOM_CLAIM` は共通契約へ委譲し、native collaboration に持ち込みません。

どの経路でも Astra が `git status -sb`、対象 diff、実在する変更ファイル、各 `Rn` または直接実行した確認結果を根拠に受入を判定します。worker の自己申告・終了コード・未解決事項の一言だけで成功または停止を決めず、repo と依頼から解消できる不足は先に解消します。ユーザー判断が必要なのは、仕様・権限・不可逆な外部操作など親が安全に決められない場合だけです。

---

## ステップ 2: レビュー (Codex reviewer ハイブリッド並列)

### 2-1: REVIEWER_SET 決定（非 planner 系：自動選定がデフォルト）

`REVIEWER_SET` を決定する:

1. **ユーザーフラグのパース**: `$ARGUMENTS` に `--reviewers=<roles>` が含まれていればカンマ区切りを観点集合として採用（未知 role は警告して除外し、有効な観点が残らなければ下記の自動選定を適用）。`--all-reviewers` が含まれていれば全 5 観点を採用。両方指定時は `--reviewers=` を優先。フラグ抽出後の残りをタスク説明として扱う
2. **フラグ未指定時の自動選定**（以下を上から評価し、必要な観点だけを集合に追加）:
   1. 正しさの独立照合が必要なら `correctness` を含める。単純な文書変更・機械的変更で親の差分照合とfocused checkが十分なら空集合でもよい
   2. コード・既存パターンとの整合性に実害がある変更 → `consistency` を追加
   3. タスクまたは実際の diff に認証・入力・秘密情報・権限・外部境界などのリスクがある → `security` を追加
   4. 新規ファイル、複数モジュール/レイヤー、API・DB schema・責務境界に触れる変更 → `architecture` を追加
   5. ロジックや公開挙動を変える、または保守性に実害がある変更 → `quality` を追加
   6. **判断に迷う**場合は全 5 観点へ機械的に広げず、不確実な観点だけを追加し、理由を最終サマリーに記録する
3. 決定した `REVIEWER_SET` を最終サマリー（ステップ 4）に記録

### 2-2: reviewer の起動

`REVIEWER_SET` に選んだ観点だけを起動します。独立した観点が複数ある場合は同じ collaboration wave に並べ、1 観点だけなら単独起動で構いません。Fan-Out の宣言や reviewer 数の固定は品質条件ではなく、runtime の上限と所有範囲に合わせて実行します。

各体の起動パラメータ:

- プロンプト（共通。`REVIEWER_ROLE` のみ変える）:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `REVIEW_INDEX=01`（初回。再レビュー時はインクリメント。起動する全体で同じ番号を共有する）
  - `REVIEWER_ROLE=[correctness|consistency|quality|security|architecture]`（体ごとに変える。REVIEWER_SET に含まれる観点のみ）
  - Astra 直接実装なら実際の対象 diff と必要な周辺ファイル、worker 実装なら worker が返した実装結果または実在する report path（存在しない `implementation-{IMPL_INDEX}.md` を仮定しない）
  - 「これはコードレビューです。実装は行わず、レビューのみ行ってください。対象 diff と変更ファイルの現状を確認し、レビューレポート本体は `{RUN_DIR}/review-{REVIEW_INDEX}-{REVIEWER_ROLE}.md` に書き出し、チャットには VERDICT + 要約のみ返してください」

### VERDICT 集約

`REVIEWER_SET` が空なら、親の差分照合結果を記録してステップ3.5へ進む。未起動reviewerのVERDICTを作らない。必要な独立確認の欠落を空集合として処理しない。

**今回起動した reviewer** の VERDICT を以下のルールで集約する:

- **全体 VERDICT = PASS**: 起動した reviewer が `VERDICT: PASS` で、確認対象に未解決の Critical / High がない
- **全体 VERDICT = FAIL**: 起動した reviewer に non-PASS・判定不能、または未解決の Critical / High がある

---

## ステップ 3: レビューループ

**LOOP_COUNT = 0 から始めてください。**

全体 `VERDICT: FAIL` の場合:

1. `LOOP_COUNT += 1`
2. FAIL の根拠を Read し、修正範囲が小さく密結合なら Astra が直接直し、独立した明確な変更なら `worker`、難所なら `expert` / `expert_max` に渡す。Terra は標準経路にせず、実測根拠がある例外だけにする。
3. 修正後は失敗原因に関係する reviewer だけを再実行する。以前 PASS だった観点を無条件に繰り返さず、変更範囲が広がった場合だけ追加観点を選ぶ。
4. 同一ツール呼出し・コマンドが2回連続で失敗したら、原因未特定の3回目を実行しない。原因と修正根拠が確認できた場合だけ再試行する。原因を解消できない場合は根拠と必要な判断を提示する。単なる失敗回数で全workflowをやり直さず、入力・環境・権限の不足をモデル能力不足と混同しない。

全体 `VERDICT: PASS` になったらステップ3.5へ進んでください。

---

## ステップ 3.5: tester（必要な場合）

実行時の挙動・runtime・データ整合性に影響する変更、またはユーザーが明示した場合だけ、reviewer とは別系統の `tester` を起動します。文書・設定でも実行指示・権限・生成・公開挙動を変える場合はその影響を確認します。挙動に影響しない文書変更や no-op は、適切な静的・構文・設定チェックを Astra または worker が行えば足り、tester を無条件に起動しません。worker report の自己申告は tester verdict として扱いません。

- `VERDICT: PASS`、または対象に tester が不要な場合は最終サマリーへ進む。
- `VERDICT: FAIL` は、report の再現可能な原因を修正経路へ戻す。修正後は必要な reviewer と tester だけを同じ cycle で再実行し、全 reviewer の無条件再実行や 8 fixture gate は要求しない。

---

## ステップ 4: 最終サマリーの提示

```
## IR 完了サマリー

### タスク
[タスクの説明]

### 変更ファイル
[実差分と実在する変更ファイルから記載]

### レビュー結果
- reviewer VERDICT: [PASS/FAIL/NOT_RUN（不要）]
- ループ回数: [LOOP_COUNT]
- REVIEWER_SET: [起動した観点をカンマ区切り、例: correctness,consistency]
- 観点別の VERDICT: [実際に起動した観点のみ。未起動なら「なし」]
- 親の受入確認: [実際の差分照合・focused checkの結果。未確認事項は分けて記載]
- [主な指摘事項があれば記載]
```
