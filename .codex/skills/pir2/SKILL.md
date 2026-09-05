---
name: "pir2"
description: "コーディングタスクを Plan → Implement → Review → Retrospect の4フェーズで実行する。複雑なタスク・設計が必要なタスク・品質保証が重要なタスク、大きな機能追加・リファクタリング・アーキテクチャ変更に使う。「ちゃんと作りたい」「しっかり実装して」「品質重視で」といった要望にも対応する。`--deepplan` でプラン策定を deepplan に切り替えられる。ユーザーが /pir2 と入力したら必ずこのスキルを使う。"
argument-hint: "[タスクの説明] [--deepplan]"
---

# PIR² — Plan → Implement → Review → Retrospect

PIR² は Plan → Implement → Review → Test → Retrospect を Astra parent が進める。Astra は要件・計画・所有境界・統合・受入を持ち、小さく密結合した変更は直接実装できる。独立して明確な変更は worker-delegation の native collaboration worker（Luna Max）へ、原因・状態・競合・性能などの難所は expert（Sol high/max）へ委譲する。並列化は所有範囲が重ならない独立単位に限り、共有ファイルは直列化する。

**タスク**: $ARGUMENTS

最初に `PLAN_MODE=standard` とする。引数に独立したフラグ `--deepplan` が明示された場合だけ `PLAN_MODE=deepplan` にしてそのフラグをタスク文言から除く。通常実行では deepplan を起動しない。

---

## ステップ 1: プロジェクトメモリパスと RUN_DIR の確定

読込済みの本 `SKILL.md` の実体パスから親の親を `CODEX_SKILLS_DIR` として確定する。対象プロジェクトの場所とは分離し、対象 repo 内の `.codex/skills` の存在を仮定しない。

実行前に `${CODEX_SKILLS_DIR}/worker-delegation/SKILL.md` と、必要な場合だけ `${CODEX_SKILLS_DIR}/pir2/references/worker-observability.md` を Read する。runner-owned artifact を使う job だけ observability の init を行い、native collaboration または Astra 直接実装には台帳を作りません。続けて `${CODEX_SKILLS_DIR}/pir2/references/sanitized-cwd.md` を Read し、その正規表現で `sanitized_cwd` を計算する。親 epic から起動された場合は prompt に明示された `PIR2_RUN_DIR` と `PIR2_PARENT_EPIC_RUN_DIR` の組だけを信頼し、ambient な同名環境変数で別 path を推測しない。以下のコード例の `PIR2_RUN_DIR` / `PIR2_PARENT_EPIC_RUN_DIR` は、親 prompt に明示された組で設定し、指定がなければ空にしてから実行する。以下の条件を満たさない path は採用しない。

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
handoff_parent="$(dirname "$HANDOFF_PATH")"
if [ -e "$handoff_parent" ] || [ -L "$handoff_parent" ]; then
  [ -d "$handoff_parent" ] && [ ! -L "$handoff_parent" ] || exit 1
else
  (umask 077; mkdir "$handoff_parent") || exit 1
fi
[ ! -L "$HANDOFF_PATH" ] || exit 1
[ ! -e "$HANDOFF_PATH" ] || [ -f "$HANDOFF_PATH" ] || exit 1
echo "PROJECT_ROOT=$PROJECT_ROOT" "PROJECT_MEMORY_DIR=$PROJECT_MEMORY_DIR" "ARTIFACT_ROOT=$ARTIFACT_ROOT" "RUN_DIR=$RUN_DIR" "HANDOFF_PATH=$HANDOFF_PATH"
```

`RUN_DIR` はこの workflow の必要な artifact root とし、利用する report の path は各実行前に確定します。native collaboration または Astra 直接実装では runner 用の `implementation-*`、3台帳などを再導出しません。以降の prompt に `PROJECT_MEMORY_DIR` と `RUN_DIR` を含めます。

次に `RESUME_MODE` を判定する。引継ぎ語が引数にあれば `resume`（Astra が handoff の未チェック項目だけを読み、既存 plan を上書きしない）、語がなく handoff が存在すれば `passive-notice`（通知して通常フロー）、それ以外は `new`（Astra が plan を確定した後に初期 handoff を Write）とする。retrospector 後は `${CODEX_SKILLS_DIR}/pir2/references/handoff-cleanup.md` の手順で handoff を処理する。`INNER_LOOP_COUNT=0`、`OUTER_LOOP_COUNT=0`、`PLAN_STRATEGY_CHANGED=false` も初期化し、ユーザーの方針切替でのみ `true` にする。

---

## ステップ 2: ブレインストーミング（状況に応じて実施）

要件が曖昧、未決定の設計判断が結果を大きく変える、または対話で設計を固める方が手戻りを減らせる場合だけ `brainstorm` を実行し、結果を Astra の計画判断に反映する。既存設計がある、タスクが明確、または関連する `docs/brainstorm/` がある場合はスキップする。完了後は自動でステップ3へ進む。ユーザー確認は、既存パターンからの逸脱、ユーザーが留保した設計選択、権限・不可逆な外部操作など実質的な判断が必要な場合だけ行う。

---

## ステップ 3: 探索フェーズ（explorer）

実装前に対象と既存パターンを確認する。小さく密結合した調査は Astra が直接行い、切り出せる独立領域は各領域1体の `explorer` に並列で渡す。アクティブ設定の `max_concurrent_threads_per_session` と実行時に利用可能な空き枠の低い方を超えない範囲で実行し、設定値を埋めることは要求しない。完了済みを空き枠と推測せず、利用可能な既存 thread は `followup_task` で再利用する。モデルは role 定義に任せる。委譲した結果は `{RUN_DIR}/exploration-{NN}.md` に保存し、直接調査は plan の根拠へ記録する。推測と確認済み事実を分ける。

- prompt には `PROJECT_MEMORY_DIR`、`RUN_DIR`、`EXPLORATION_INDEX`、レポート path、タスク、実装・git変更禁止を含める。
- 既存パターン、再利用可能な helper、分岐ごとのフィールド、framework の自動処理、必要なら公式 docs の裏取りを調査する。
- 不明点は既存 explorer の `followup_task`（不可なら同じ role の追加起動）で調べ、追加 index は既存最大値+1。新規ライブラリ選定だけは `tech-validator` role を使う。

---

## ステップ 4: Astra によるプラン策定

Astra parent が全 exploration report、brainstorm 結果（実施時）、handoff（resume 時）、対象コードを read-only で照合し、`{RUN_DIR}/plan.md` を直接作成・更新する。Astra は目標、根拠、対象ファイル、scope、依存 DAG、実装手順、検証手順、禁止範囲、`R1` から始まる requirements、必要な `IMPLEMENTATION_SHARDS`（各 shard の所有範囲・依存・成果物）を確定する。plan の内容をそのまま信頼せず、対象コードと探索結果を Read して事実を確認する。

既存の plan がある場合は未完了項目と変更対象を保持し、影響するセクションだけを増分更新する。Astra は計画・DAG・scope・requirements・implementation shards の作成と最終判断を所有する。

### PLAN_MODE=deepplan

`PLAN_MODE=deepplan` の場合だけ `${CODEX_SKILLS_DIR}/deepplan/SKILL.md` を Read して実行。同一 `RUN_DIR`。完了条件は `{RUN_DIR}/plan.md`。EXPLORATION_NEEDED 残時の再実行も deepplan。standard ならこの節をスキップする。

既存構造から逸脱するプランは、実装前に既存 N 件中 M 件、採用構成、理由、代替案をユーザーへ提示して承認を得る。

### ステップ 4.5: 能動的再探索ループ（最大5回）

実行前に `${CODEX_SKILLS_DIR}/pir2/references/exploration-loop.md` を必要に応じて Read する。`EXPLORATION_ROUND=0` から開始し、`plan.md` の `EXPLORATION_NEEDED` に `- topic` が残る間だけ、Astra が定義した topic の追加探索と plan.md の増分更新を最大5回行う。cap到達時は未解決 topic と実害を確認する。正しさ・安全性に必要な不明点は未確認のまま実装せず、根拠のある次の調査か必要なユーザー判断へ進む。非致命的な改善だけを backlog と最終サマリーへ記録する。計画の全破棄・再生成・計画担当の再起動は行わない。

### ステップ 4.6: プラン選択肢のユーザー確認（該当時のみ）

実行前に `${CODEX_SKILLS_DIR}/pir2/references/plan-choice-gate.md` を必ず Read する。キーワードや案の数だけで停止しない。ユーザーが留保した判断、依頼範囲の変更、未承認の権限・不可逆操作など、親が指示と実測から安全に決められない場合だけ推奨案を示して確認を待つ。別案・方針切替なら `PLAN_STRATEGY_CHANGED=true` とし、ユーザーの選択を `plan.md` の影響する方針・scope・DAG・requirements へ増分反映する。既存計画全体を破棄・再策定せず、Auto mode でもこの確認を省略しない。

---

## ステップ 5: プラン保存

`docs/plans/` がなければ作成し、`docs/plans/YYYY-MM-DD-<feature>.md` にタスク、目標、実装チェックリスト、`{RUN_DIR}/plan.md` の設計詳細、実装ログ（変更ファイルと内容は完了後に記録）、作成日と進行中ステータスを保存する。保存 path をユーザーに提示する。確認後に削除できる記録であることを明記する。

---

## ステップ 5.5: handoff.md 初期版生成（`RESUME_MODE=new` の場合のみ）

`resume` / `passive-notice` は既存 handoff を温存してスキップする。`new` の場合は `{RUN_DIR}/plan.md` を Read し、`~/.codex/pir-handoff.md` を実行前に必ず Read して、そのフォーマットに従い `$HANDOFF_PATH` へ `最終更新`、タスク、背景・決定事項、残 TODO（`- [ ]`）、既知の問題/要確認、関連 artifact を Write する。path を提示し、passive-notice なら resume 方法も通知する。

## ステップ 5.6: 次ステップキュー初期版生成

実行前に `${CODEX_SKILLS_DIR}/pir2/references/next-steps-queue.md` を必ず Read する。`{RUN_DIR}/next-steps.md` に以降の subagent 起動予定を checkbox で Write し、各ステップ完了直後に `[x]` と `<!-- done: ISO8601 -->` を付ける。ユーザー会話で中断した後は、次の判断前に必ずこのファイルを Read する。resume 時は handoff の未完了項目を統合する。

## ステップ 5.7: 破壊的変更チェックリスト + 動作変更チェック

実行前に `${CODEX_SKILLS_DIR}/pir2/references/destructive-change-check.md` を必ず Read する。plan・実差分・利用側から公開挙動、データ、権限、生成物への影響を確認し、想定する具体的な実害に対応した review/test を選ぶ。必要な根拠は plan に記録する。固定フラグやファイル数だけで全観点・全スイートを追加せず、プロジェクト必須検証と実害防止に必要な確認は維持する。

## ステップ 5.8: 直前追加 feedback の自己照合ゲート

実行前に `${CODEX_SKILLS_DIR}/pir2/references/feedback-conflict-gate.md` を必ず Read する。最新依頼・適用指示・関連する既知の feedback を意味で照合する。明確な最新指示はそのまま反映し、未決定の矛盾や権限外の変更だけ確認する。必要な記憶を参照し、件数・期間・記録ファイルを一律に要求しない。

---

## ステップ 6: 実装経路

実行前に `${CODEX_SKILLS_DIR}/worker-delegation/SKILL.md` と、この skill の
`${CODEX_SKILLS_DIR}/pir2/references/implementation-delegation.md` を Read します。
計画から次の経路を選びます。

- 小さく、全体文脈と分離できない変更は Astra が直接実装し、対象 diff と焦点を絞った確認を行う。
- 所有ファイルと終了条件が明確な独立変更は native collaboration の `worker`（Luna Max）へ渡す。
- 原因・状態所有権・競合・性能・厳しい互換性などの難所は `expert` / `expert_max`（Sol high/max）へ最初から渡す。Terra は標準経路外で、実測根拠がある例外に限る。

委譲時は目的、所有/禁止範囲、変更してよい契約、`R1...Rn` の終了条件、焦点を絞った確認を短い task/requirements にします。native collaboration では runner、canonical report、固定 8 fields、deterministic gate、ledger を複製せず、worker-delegation の返却契約だけを使います。明示的な artifact/provenance が必要な CLI runner job の場合だけ、同契約が定める runner 用証拠を適用します。

PIR² 固有の shard は、plan に `IMPLEMENTATION_SHARDS` があり、各 shard の所有/禁止ファイル、依存、成果物が明示され、共有型/API/schema/migration/lockfile/生成物/golden/config/helper に競合せず、統合後の確認方法がある場合だけ、アクティブ設定の `max_concurrent_threads_per_session` と実行時空き枠の低い方の範囲で並列化します。条件不成立なら単一の worker または Astra 直接経路に戻します。並列 writer を一律禁止せず、同一ファイルや共有契約を複数担当に割り当てないことを安全条件とします。

完了後は Astra が `git status -sb`、対象 diff、実在する変更ファイル、各 `Rn` の確認結果を測定して acceptance を決めます。worker の自己申告・終了コードだけで PASS にせず、reviewer/tester は必要な場合だけ別系統で使います。

### 6.1: runner job の証拠

artifact identity、実行モデル、effort、変更集合の厳密な証拠が必要な runner job に限り、worker-delegation の deterministic-completion SSOT と verifier を使います。`PHANTOM_CLAIM` はその runner job の hard fail、`UNDECLARED_CHANGE` は実差分を再確認する warning とします。native collaboration と Astra の直接実装には 8 fixture、canonical report、ledger を要求しません。

---

## ステップ 6.5: worker の未解決事項ユーザー確認（該当時のみ）

`{RUN_DIR}/implementation-{最新}.md` または worker の返却に未解決事項があれば、まず Astra が対象コード、依頼、既存仕様から解消できるか確認します。仕様・権限・不可逆な外部操作など安全に決められない事項だけをユーザーへ提示し、単なる「あり」の一言で処理を停止しません。解消できる場合は影響する plan/requirements だけを更新し、必要な経路（直接実装、worker、expert）へ戻します。

---

## ステップ 7: レビューループ

### 7-1: 観点セット

`--reviewers=<roles>` があれば未知 role は警告して除外し、有効な観点が残らなければ下記の自動選定を適用します。`--all-reviewers` は全5観点、両方なら `--reviewers=` を優先します。未指定時は変更のリスクと範囲から必要な観点だけを選び、security / architecture は該当する変更に限って追加します。フラグを除いた文字列をタスク説明として扱い、集合を最終サマリーに記録します。

### 7-2: reviewer の起動

`REVIEWER_SET` に選んだ観点だけを起動します。独立した観点が複数ある場合は同じ collaboration wave に並べ、1 観点だけなら単独起動で構いません。起動時は対象 diff、plan、受入条件、固有 report path を渡し、モデルは role 定義に任せます。Fan-Out の宣言・固定人数・ledger は必要な場合だけ使い、native collaboration の通常経路へ runner 用手順を持ち込みません。

### 7-3: verdict と inner loop

独立レビューが不要と判断した場合は、親の差分照合結果を記録して次へ進み、reviewer の VERDICT を作りません。必要な観点の欠落を空集合として扱いません。起動した reviewer が PASS を返し、確認対象に未解決 Critical/High がなければ reviewer gate PASS。欠落、判定不能、non-PASS、未解決 Critical/High は FAIL とします。

FAIL 時は `INNER_LOOP_COUNT += 1`。失敗原因を根拠に、修正範囲が小さく密結合なら Astra が直接修正し、独立した変更なら worker、難所なら expert / expert_max に渡します。再レビューは失敗原因に関係する reviewer だけを起動し、変更範囲が広がった場合だけ観点を追加します。同一ツール呼出し・コマンドが2回連続で失敗したら、原因未特定の3回目を実行しません。原因と修正根拠が確認できた場合だけ再試行し、解消できない場合は必要な判断と根拠を提示します。入力不足・環境・権限の問題は能力不足と混同せず、Astra が解消できるかを先に確認します。

---

## ステップ 7.5: リファクタ提案（refactor-advisor → ゲート → 任意適用）

実行前に `${CODEX_SKILLS_DIR}/pir2/references/refactor-advisor-gate.md` を必要に応じて Read する。レビューで品質上の改善余地が残り、refactor-advisor の分離価値がある場合だけ一体・一回起動し、提案の適用はユーザーが選択した候補に限ります。適用後は影響した観点だけを再レビューし、refactor-advisor 自体を無条件に再実行しません。

---

## ステップ 8: テスト（必要な場合）

### 8-1: tester 起動

runtime、データ整合性、生成物、またはユーザーが明示した確認がある場合だけ、reviewer とは別系統の `tester` を起動します。文書・設定であっても実行指示、権限、生成、公開挙動を変える場合はその影響を検証します。挙動に影響しない文書変更や no-op は、Astra または worker が行う適切な静的・構文・設定チェックで足りる場合があり、無条件に tester を起動しません。必要なら `${CODEX_SKILLS_DIR}/pir2/references/tester-prompt.md` を Read して TEST_SCOPE を組み立て、モデルは role 定義に任せます。

### 8-2: verdict と outer loop

tester を使った場合は `VERDICT: PASS`、または tester が不要な場合は対象確認が完了すればステップ9へ進みます。FAIL 時は report の再現可能な原因を修正経路へ戻します。

1. `OUTER_LOOP_COUNT += 1`。
2. 再現した原因と修正根拠が確認できた場合、test report に基づく最小の修正を直接実施または worker/expert に委譲し、必要な reviewer と tester だけを再実行します。runner を使った job の場合だけ worker-delegation の証拠手順へ戻します。
3. 同一ツール呼出し・コマンドが2回連続で失敗したら、原因未特定の3回目を実行しません。修正根拠がない、権限が不足する、または未承認の不可逆な影響を伴う場合は、未解決の根拠と必要な判断をユーザーへ示します。全 reviewer や 8 fixture の無条件再実行は行いません。

### 8-2-G: 続行可能ゲート（必要な場合）

繰り返し修正が安全性・仕様・外部状態に影響する場合だけ `${CODEX_SKILLS_DIR}/pir2/references/continuation-gate.md` を Read します。上記の停止条件に該当したら、影響範囲・再現した原因・残る選択肢をまとめ、追加実装にはユーザー承認が必要かを判断します。単なるテスト回数や未解決事項の存在だけで全 workflow を hard stop にしません。

---

## ステップ 9: ウォークスルー生成（read-only）

実行前に `${CODEX_SKILLS_DIR}/pir2/references/walkthrough-templates.md` を必ず Read する。変更ファイルを実際に Read し、フル版を実装記録の実装ログへ、サマリー版を最終サマリーへ作る。引用は Read 済みコードだけにする。完了後は next-steps を更新する。

## ステップ 10: メモリへの記録

`mkdir -p "$PROJECT_MEMORY_DIR"` の後、`$PROJECT_MEMORY_DIR/pir_skill_log.md` に `## [タスク名] — [気づき・課題・パターン]` を追記する。必要な場合だけ、実測した explorer/worker/reviewer/tester/retrospector の model・体数、`EXPLORATION_ROUND`、`INNER_LOOP`、`OUTER_LOOP` を記録し、worker は actor:model:effort として残す。native collaboration の実行に runner 台帳を作らず、未使用 actor の架空行も作らない。

## ステップ 11: 振り返り

実行前に `${CODEX_SKILLS_DIR}/pir2/references/retrospector-prompt.md` を必要に応じて Read する。小規模または subagent 不可なら Astra が行い、分離価値がある場合だけ `retrospector` role を起動する。runner 台帳を使った場合だけ、その実在する report path と実測値を渡し、未使用の actor/ledger 行を作らない。メタ改善推奨があれば最終サマリーへ転記して `/retro --meta` の判断をユーザーに委ねる。完了後は next-steps を更新する。

## ステップ 11.5: handoff.md 完了判定と後処理

実行前に `${CODEX_SKILLS_DIR}/pir2/references/handoff-cleanup.md` を必ず Read する。`$HANDOFF_PATH` が存在する場合のみ、今回の作業に対応する未完了項目と実結果を照合し、完了時は検証済み RUN_DIR へ回復可能な形で保管する。残項目があれば最終更新行を更新する。結果を最終サマリーに記載する。存在しなければスキップし、完了後は next-steps を更新する。

## ステップ 12: 最終サマリーの提示

実行前に `${CODEX_SKILLS_DIR}/pir2/references/final-summary-template.md` を必ず Read する。結果、実際の変更、実行した検証と未確認事項、実在する記録を簡潔に提示する。未起動の reviewer/tester の verdict や未生成 artifact を補完しない。next-steps 全項目完了ならその旨を記載する。

## ステップ 13: ウォークスルーの提示

ステップ9のサマリー版を提示し、フル版は内部記録として保持する。詳細を求められた場合だけフル版を提示し、末尾に「詳細なウォークスルーが必要な場合はお知らせください。」と添える。
