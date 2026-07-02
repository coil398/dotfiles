---
name: pir2codex
description: PIR² の Codex 実装版。Plan→Review→Retrospect は Claude のまま、Implement フェーズだけ Codex（mcp__codex__codex）に差し替えた実験的ワークフロー。Codex 実装の品質を通常 /pir2 と比較するために使う。大きく結合した実装は IMPLEMENTATION_UNITS による直列 fresh セッション化に対応。ユーザーが /pir2codex と入力したら必ずこのスキルを使う。
argument-hint: [タスクの説明]
---

# PIR² Codex — Implement だけ Codex 版 Plan → Implement → Review → Retrospect

PIR² の **Codex 実装実験版**です。explorer / planner / reviewer / tester / retrospector は通常 /pir2 と同じく Claude（`Agent` ツール）で動かし、**Implement フェーズのみ Codex セッション（`mcp__codex__codex`）に差し替え**ます。狙いは「Codex に実装させたときの品質」を通常 /pir2 と統制比較すること。このスキル本体（= メイン Claude）がオーケストレーターとなり、制御フロー（起動・ループ管理・VERDICT 集約・ユーザー確認ゲート）をスキル本体に集約します。サブからのネスト起動は read-only の探索（explorer）に限ります。

以下の手順を**順番に**実行してください。通常 /pir2 と同一のステップは `~/.claude/skills/pir2/SKILL.md` の同番号ステップおよび `~/.claude/skills/pir2/references/*` を SSOT として参照します（DRY・二重管理回避）。**差分の本体はステップ 6（Codex 実装）**です。

**タスク**: $ARGUMENTS

---

## ステップ 1: プロジェクトメモリパスと RUN_DIR の確定

以下の Bash コマンドで `PROJECT_ROOT` / `PROJECT_MEMORY_DIR` / `RUN_DIR` / `HANDOFF_PATH` を確定し、以降のすべてのステップで使用してください:

```bash
PROJECT_ROOT="$(pwd)"
# sanitized-cwd 計算（PROJECT_MEMORY_DIR 専用）は ~/.claude/skills/pir2/references/sanitized-cwd.md を SSOT とする
# 成果物置き場（RUN_DIR/HANDOFF_PATH）の基底パスの SSOT は run-dir-base.md。PROJECT_ROOT 基底になったため
# RUN_DIR/HANDOFF_PATH 側の sanitize は不要（run_feature の sanitize のみ下記に別途残る）
sanitized_cwd="$(pwd | sed 's|[^a-zA-Z0-9]|-|g')"
PROJECT_MEMORY_DIR="${HOME}/.claude/projects/${sanitized_cwd}/memory"
run_ts="$(date +%Y%m%d-%H%M%S)"
run_feature="$(printf '%s' "$ARGUMENTS" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
[ -z "$run_feature" ] && run_feature="task"
RUN_DIR="${PROJECT_ROOT}/.ai-pir-runs/${run_ts}-${run_feature}"
mkdir -p "$RUN_DIR"
# 中間ファイルを git 追跡から外す（git リポジトリのときのみ）
if git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  grep -qxF '/.ai-pir-runs/' "${PROJECT_ROOT}/.gitignore" 2>/dev/null || echo '/.ai-pir-runs/' >> "${PROJECT_ROOT}/.gitignore"
fi
HANDOFF_PATH="${PROJECT_ROOT}/.ai-pir-runs/handoff.md"
echo "PROJECT_ROOT=$PROJECT_ROOT"
echo "PROJECT_MEMORY_DIR=$PROJECT_MEMORY_DIR"
echo "RUN_DIR=$RUN_DIR"
echo "HANDOFF_PATH=$HANDOFF_PATH"
```

`RESUME_MODE` の判定（resume / passive-notice / new）と RESUME_MODE 別の挙動は **/pir2 のステップ 1 と同一**（詳細プロトコル: `~/.claude/pir-handoff.md`）。`PLAN_STRATEGY_CHANGED=false` を初期化する。以降の各サブエージェント／Codex wrapper へのプロンプトには必ず `PROJECT_MEMORY_DIR` / `RUN_DIR` / `PROJECT_ROOT` を含めてください。

---

## ステップ 2: ブレインストーミング（状況に応じて実施）

**/pir2 のステップ 2 と同一**。要件が曖昧・アーキ選択が必要・対話で設計を固めたい場合のみ `brainstorm` スキルを実行し、結果をステップ4の planner に渡す。brainstorm 完了後は単独ターンで止まらず自動でステップ3へ進む。

---

## ステップ 3: 探索フェーズ（explorer）

**/pir2 のステップ 3 と同一**。コードベース探索はメイン Claude が直接行わず、必ず `explorer` を `Agent` ツールで起動（最低1体、独立領域なら最大3体並列、haiku/sonnet/opus 使い分け）。プロンプトに含めるパラメータ・調査観点・git 操作禁止の明示・既存 agent 流用時のロール境界再注入は /pir2 ステップ3に従う。

---

## ステップ 4: プラン策定（planner）

**/pir2 のステップ 4 と同一**。`planner` を `Agent` ツールで起動（model: opus）。プロンプトには `PROJECT_MEMORY_DIR` / `RUN_DIR` / `PLAN_STRATEGY_CHANGED` / タスク内容 / `{RUN_DIR}/exploration-*.md` のパス一覧を渡す。加えて:

- 「完全に独立した実装 shard がある場合のみ `IMPLEMENTATION_SHARDS` を提案してください（試験実装）」
- 「大きいが結合していて並列分割できない実装は `IMPLEMENTATION_UNITS`（順序付きの直列 unit）を提案してください（試験実装。`IMPLEMENTATION_SHARDS` と排他）」
- 「プランレポート本体は `{RUN_DIR}/plan.md` に書き出し、チャットには要約＋EXPLORATION_NEEDED の有無のみ返してください」

> ℹ️ planner は Claude のまま（実装役だけ Codex に差し替える統制比較のため）。planner の分割戦略観点（規模見積もり→ shards / units / 単一）は `~/.claude/agents/planner.md` 5.3 が SSOT。

既存パターン逸脱の事前申告が含まれていたら、実装着手前にユーザー確認（**/pir2 ステップ4と同一**）。

---

## ステップ 4.5: 能動的再探索ループ（最大5回）

**/pir2 のステップ 4.5 と同一**。詳細プロトコル: `~/.claude/skills/pir2/references/exploration-loop.md`。

## ステップ 4.6: プラン選択肢のユーザー確認（該当時のみ・Auto mode でも例外なし）

**/pir2 のステップ 4.6 と同一**。詳細プロトコル: `~/.claude/skills/pir2/references/plan-choice-gate.md`。別案 or 方針切替時は `PLAN_STRATEGY_CHANGED=true` をセットして planner 再起動。

---

## ステップ 5: プラン保存

**/pir2 のステップ 5 と同一**。`docs/plans/YYYY-MM-DD-<feature>.md` に保存しユーザーに提示。

## ステップ 5.5: handoff.md 初期版生成（`RESUME_MODE=new` の場合のみ）

**/pir2 のステップ 5.5 と同一**（詳細: `~/.claude/pir-handoff.md`）。

## ステップ 5.6: 次ステップキュー初期版生成

**/pir2 のステップ 5.6 と同一**。詳細プロトコル: `~/.claude/skills/pir2/references/next-steps-queue.md`。ユーザー会話中断後は次の判断前に必ず `{RUN_DIR}/next-steps.md` を Read。各ステップ完了直後に checkbox を `[x]` 更新。

## ステップ 5.7: 破壊的変更チェックリスト + 動作変更チェック

**/pir2 のステップ 5.7 と同一**。詳細プロトコル: `~/.claude/skills/pir2/references/destructive-change-check.md`。

## ステップ 5.8: 直前追加 feedback の自己照合ゲート

**/pir2 のステップ 5.8 と同一**。詳細プロトコル: `~/.claude/skills/pir2/references/feedback-conflict-gate.md`。ただし照合対象は「Codex に渡す実装プロンプト案」の除外指示・スコープ縮小とする。

---

## ステップ 6: 実装（Codex）★ pir2codex の差分本体

`INNER_LOOP_COUNT = 0`、`OUTER_LOOP_COUNT = 0` から開始してください。

ここが通常 /pir2 との唯一の実質差分です。implementer サブエージェント（Claude）の代わりに **Codex セッション（`mcp__codex__codex`）が実装**します。

### 6-0: 実装 actor の決定（Codex 版マッピング）

通常 /pir2 と同じ判定ロジック（`~/.claude/skills/pir2/references/implementation-delegation.md`）で actor を決めるが、**実装主体は Claude implementer ではなく Codex セッション**になる。マッピング:

| /pir2 の actor | pir2codex での実体 |
|---|---|
| `implementer-subagent` | **codex-single**: Codex 1 セッションが plan 全体を実装（デフォルト） |
| `implementer-shards` | **codex-shards**: 独立 shard ごとに Codex セッションを並列起動（最大3） |
| `implementer-sequential` | **codex-sequential**: unit ごとに新しい Codex セッション（新 threadId）を `UNIT_ID` 昇順に直列起動。unit ごとにコンテキストまっさら |
| `main` | **codex-single に倒す**（実装を Claude に戻さない＝実験変数を保つ。pir2codex に Claude 直接実装の経路はない） |

判定は planner の `{RUN_DIR}/plan.md`（`IMPLEMENTATION_SHARDS` / `IMPLEMENTATION_UNITS`）と delegation.md の許可条件に従う。曖昧なら **codex-single**。

> **試験実装の注記**: `codex-shards` / `codex-sequential` は `~/.claude/skills/pir2/references/experimental.md` の `pir2-implementer-sequential-units`（直列）/ `pir2-implementer-shards-and-review-fix-shards`（並列）を SSOT に retrospector が観測する。判定が曖昧なら codex-single に倒す。

### 6-1: Codex wrapper Agent の起動（共通プロトコル）

Codex は `mcp__codex__codex` で呼ぶが、MCP ツールをメイン Claude が直接呼ぶとブロックする（`~/.claude/skills/codex/SKILL.md` SSOT）。そのため **wrapper Agent（`subagent_type=general-purpose`）経由**で起動する。wrapper はこのフェーズの実行主体なので **foreground**（/pir2 が implementer を await するのと同じ。`/codex` の background は“横の相談”用なのでここでは前面待ち）。

**入出力は Claude（スキル本体 + wrapper）が肩代わりする**。Codex は `workspace-write` sandbox で書き込みが `cwd`（リポジトリ）配下に限定される。`RUN_DIR`（`${PROJECT_ROOT}/.ai-pir-runs/<run>/`）は Codex に直接読み書きさせず、スキル本体が仲介するため:

1. スキル本体が `{RUN_DIR}/plan.md`（および該当時 review/test 指摘・先行 unit レポート）を **Read して全文を wrapper プロンプトに verbatim 埋め込む**（要約しない＝telephone-game 回避）
2. Codex は **リポジトリ内のコードだけを書く**
3. wrapper が受け取った Codex の報告（変更ファイル一覧＋概要）を返し、**スキル本体が implementation レポートを `{RUN_DIR}` に Write**（肩代わり）

#### wrapper Agent への指示テンプレート

wrapper Agent に渡すプロンプトに必ず含める:

- 「まず `ToolSearch query="select:mcp__codex__codex,mcp__codex__codex-reply"` でツールをロードせよ」
- 「次に `mcp__codex__codex` を **1回だけ**呼べ（リトライ禁止）。引数:」
  - `prompt`: 下記「Codex 実装プロンプト」
  - `cwd`: `$PROJECT_ROOT`
  - `sandbox`: `"workspace-write"`
  - `approval-policy`: `"never"`
  - `model`: `"gpt-5.5"`
  - `config`: `{ "model_reasoning_effort": "high" }`（難所の根本原因究明・複雑設計を伴う実装は `"xhigh"`）
- 「Codex の応答が返ったら、**threadId・変更ファイル一覧・実装概要・注意点・エラー（あれば全文）** をそのまま報告して終了せよ。wrapper 自身はファイル検証しない（呼び出し元が git diff で検証する）。結果を捏造しない」

#### Codex 実装プロンプト（wrapper が Codex に渡す本文）

```
あなたは実装担当エンジニアです。以下の実装プランに忠実に、リポジトリ内のコードを実際に編集して実装してください。

厳守事項:
- テキストで説明するだけでなく、必ず実際にファイルを編集（apply_patch 等）すること
- プランに記載されていない変更はしない
- テストスイートの実行（go test / pytest / npm test 等）はしない。lint・型チェック・ビルド・コード生成・diff 確認までに留める
- 既存コードの命名・パターンに合わせる
- 完了したら「変更ファイル一覧」「実装概要」「注意点・未解決事項」を簡潔に報告する

--- 実装プラン ---
{plan.md の全文}
（codex-shards 時: --- 許可ファイル / 禁止ファイル --- を明記）
（再実装時: --- レビュー指摘 / テスト指摘 --- {review-*.md / test-*.md の全文}）
（codex-sequential 時: --- 担当 UNIT --- {UNIT_ID と spec} / --- 先行 unit の成果 --- {先行 unit の git diff と概要}）
```

#### wrapper 返り後のスキル本体の処理（共通）

1. **git diff で実体検証（必須）**: `git diff --stat HEAD` / `git diff --name-only HEAD` を実行し、Codex が実際にファイルを変更したかを確認する。Codex の自己申告を信じない（CLAUDE.md「ツール結果の捏造の絶対禁止」と同根。Codex も自己申告しうる）。変更が空・プラン外への波及がある場合は対処（再実行 or ユーザー確認）
2. **threadId を保持**（inner-loop の `codex-reply` 継続用）
3. **implementation レポートを Write**: `{RUN_DIR}/implementation-{IMPL_INDEX}.md`（shard 時 `-{SHARD_ID}`、unit 時 `-unit-{UNIT_ID}`）に、Codex の変更ファイル一覧＋実装概要＋注意点を `~/.claude/agents/implementer.md`「実装完了レポートのフォーマット」に合わせて書き出す（reviewer / tester がこのファイルを Read するため、フォーマットを /pir2 と一致させる）

### 6-1a: codex-single（デフォルト）

wrapper を **1 体**起動 → git diff 検証 → threadId 保持 → implementation-{IMPL_INDEX}.md を Write。

### 6-1b: codex-shards（plan に `IMPLEMENTATION_SHARDS`・独立ゲート通過時）

delegation.md「shard 許可条件」を全て満たした各 shard を、**別々の wrapper Agent として同一メッセージ内に並列起動**（各 wrapper が独立した Codex セッション）。各 Codex プロンプトに当該 shard の許可/禁止ファイルを明記し「許可集合の外を編集するな」と指示。全 shard 完了後、スキル本体が delegation.md「shard 統合確認」（全 `implementation-{IMPL_INDEX}-*.md` を Read + git diff で競合・命名不整合・未接続を確認）を実施。問題があれば codex-single に戻して統合修正。

### 6-1c: codex-sequential（plan に `IMPLEMENTATION_UNITS`・unit ゲート通過時）

delegation.md「unit 許可条件」を満たした unit を `UNIT_ID` 昇順に **1 体ずつ直列**に wrapper 起動（先行 unit の完了を待ってから次を起動）。各 unit:

- **新しい Codex セッション（新 threadId）= コンテキストまっさら**
- スキル本体が**先行 unit の `git diff` と `implementation-{IMPL_INDEX}-unit-*.md` を Read し、当該 unit の wrapper プロンプトに埋め込む**（Codex 実装プロンプトの「先行 unit の成果」欄）。「先行 unit の命名・抽象・データ形状に従え」を明記
- Codex は当該 unit の範囲のみ実装

全 unit 完了後、スキル本体が delegation.md「unit 統合確認」（全 `implementation-{IMPL_INDEX}-unit-*.md` を Read + git diff で unit 境界の命名不整合・重複抽象・未接続を確認）を実施。問題があれば codex-single に戻して統合修正。

> ℹ️ v1 では codex-sequential / codex-shards は**初回実装のみ**。reviewer/tester FAIL 後の再実装は統合済み diff に対し codex-single で行う（6-2）。

### 6-2: inner-loop の再実装（reviewer FAIL 後）

- **codex-single**: `mcp__codex__codex-reply({ threadId, prompt: <FAIL を返した全 review-*.md の全文> })` で**同スレッド継続**（Codex が実装文脈を保ったまま修正）。wrapper Agent 経由で呼び、返り後に git diff 検証 → implementation-{新 IMPL_INDEX}.md を Write
- **codex-shards / codex-sequential の初回後**: 統合済み diff に対し codex-single（新規 Codex セッション or 直近 threadId への reply）で修正する

### 完了後

`{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新（/pir2 ステップ5.6-2 と同一。ループ複数回は最初の1回のみマーク）。

---

## ステップ 6.5: 実装者の未解決事項ユーザー確認（該当時のみ）

**/pir2 のステップ 6.5 と同一**。`{RUN_DIR}/implementation-{最新}.md` の「注意点・未解決事項」が「あり」なら、(A) スコープ縮小承認 / (B) 再プラン / (C) 追加指示で再実装 をユーザーに確認し `{RUN_DIR}/user-decisions.md` に記録。仕様変更判断をスキル本体が独断しない。

---

## ステップ 7: レビューループ（reviewer ハイブリッド並列、最大3回）

**/pir2 のステップ 7 と同一**（reviewer は Claude のまま＝Codex 実装を Claude が異種レビュー）。`REVIEWER_SET` 決定（デフォルト全5観点）→ **7-2A Fan-Out Gate 宣言 → 7-2B 並列発火**（詳細: `~/.claude/skills/pir2/references/fan-out-gate.md`）→ 7-3 VERDICT 集約 → 7-4 判定。

7-4 で FAIL かつ `INNER_LOOP_COUNT < 3` の場合の再実装は **ステップ 6-2（Codex codex-reply / codex-single）** で行う（implementer サブエージェントの代わりに Codex）。FAIL を返した全 `{RUN_DIR}/review-{最新}-{ROLE}.md` の全文を Codex プロンプトに埋め込む。再 reviewer は同 REVIEWER_SET で 7-2A→7-2B により並列再起動（PASS 観点も退行検知のため再レビュー）。`INNER_LOOP_COUNT >= 3` でステップ7.5へ強制移行。

---

## ステップ 7.5: リファクタ提案（refactor-advisor 起動 → ゲート → 任意適用）

**/pir2 のステップ 7.5 と同一**。詳細プロトコル: `~/.claude/skills/pir2/references/refactor-advisor-gate.md`。refactor-advisor は Claude で1体起動。提案適用（implementer 再起動の箇所）は **Codex（6-2 と同じ codex 経由）** で行い、適用後は 7-2A→7-2B で reviewer 再起動して退行検知。同一 run 内1回のみ。

---

## ステップ 8: テストループ（tester、最大3回）

**/pir2 のステップ 8 と同一**（tester は Claude）。詳細: `~/.claude/skills/pir2/references/tester-prompt.md`。FAIL 時は `OUTER_LOOP_COUNT += 1` → 上限到達なら続行可能ゲート（`~/.claude/skills/pir2/references/continuation-gate.md`、Auto mode でも応答待ち）→ `INNER_LOOP_COUNT=0` リセット → **再実装は Codex（6-2、`{RUN_DIR}/test-{最新}.md` 全文を埋め込む）** → ステップ7へ戻る → tester 再起動。

---

## ステップ 9: ウォークスルー生成（メイン Claude が直接）

**/pir2 のステップ 9 と同一**。詳細テンプレート: `~/.claude/skills/pir2/references/walkthrough-templates.md`。最重要原則: 推測でコードを書かず、実際に Read したコードのみ引用する。

## ステップ 10: メモリへの記録

**/pir2 のステップ 10 と同一**。`{PROJECT_MEMORY_DIR}/pir_skill_log.md` に追記。モデルスイープ計装の1行は implementer の箇所を `implementer=codex(gpt-5.5,effort=<…>)×<セッション数>` として記録する（Codex 実装版であることを明示）。

## ステップ 11: 振り返り（retrospector、常に実行）

**/pir2 のステップ 11 と同一**。詳細: `~/.claude/skills/pir2/references/retrospector-prompt.md`。`ワークフロー種別: pir2codex` を明示（通常 pir2 / pir2async との比較用）。`PLAN_STRATEGY_CHANGED` の現在値を渡す。experimental.md の `pir2-implementer-sequential-units` に該当 run の観測を促す。

## ステップ 11.5: handoff.md 完了判定と後処理

**/pir2 のステップ 11.5 と同一**。詳細: `~/.claude/skills/pir2/references/handoff-cleanup.md`。

---

## ステップ 12: 最終サマリーの提示

以下をユーザーに提示してください:

```
## PIR² Codex 完了サマリー

### タスク
[タスクの説明]

### ワークフロー
pir2codex (Implement だけ Codex 版 — 実装主体 = Codex gpt-5.5)

### 実装 actor / Codex セッション
- IMPLEMENTATION_ACTOR: [codex-single / codex-shards / codex-sequential]
- Codex セッション数: [N]（codex-sequential 時は unit 数 / codex-shards 時は shard 数）
- effort: [high / xhigh]

### 実装記録
docs/plans/YYYY-MM-DD-<feature>.md

### 変更ファイル
[implementation レポートから抜粋。git diff で実体検証済みであることを明記]

### レビュー結果
- 最終 VERDICT: [PASS/FAIL]
- 内側ループ回数: [INNER_LOOP_COUNT]
- [主な指摘事項]

### リファクタ提案（refactor-advisor）
- 提案件数 / 適用件数

### テスト結果
- テスト VERDICT: [PASS/FAIL]
- 外側ループ回数: [OUTER_LOOP_COUNT]

### 作業ディレクトリ
{RUN_DIR}

### 振り返り
[retrospector の改善内容の要約]

### 通常版 PIR² / Codex 比較ポイント
- Codex 実装の品質（reviewer 指摘の数・質、INNER_LOOP 回数）が Claude implementer と比べてどうだったか
- codex-sequential を使った場合: unit 分割による fresh context 化が後半 unit の品質に効いたか
- Codex 固有の挙動（長尺セッションでの文脈保持、apply_patch の正確性、指摘対応の素直さ）
```

---

## ステップ 13: ウォークスルーの提示

**/pir2 のステップ 13 と同一**。ステップ9のサマリー版を提示し、末尾に `詳細なウォークスルーが必要な場合はお知らせください。` を添える。
