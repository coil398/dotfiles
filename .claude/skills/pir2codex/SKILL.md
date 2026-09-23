---
name: pir2codex
description: PIR²の実装phaseだけをCodex CLIへ委譲する実験workflow。Claudeによる計画・review・test・retrospectを保ち、通常のpir2と実装品質を比較するときに使う。
argument-hint: "[タスクの説明]"
---

# PIR² Codex — Implement だけ Codex 版 Plan → Implement → Review → Retrospect

PIR² の **Codex 実装実験版**です。explorer / planner / reviewer / tester / retrospector の各担当は通常 /pir2 と同じく Claude（`Agent` ツール）で動かし、**Implement フェーズのみ Codex（codex CLI、codex-runner 担当経由）に差し替え**ます。狙いは「Codex に実装させたときの品質」を通常 /pir2 と統制比較すること。このスキル本体（= メイン Claude）がオーケストレーターとなり、制御フロー（起動・ループ管理・VERDICT 集約・ユーザー確認ゲート）をスキル本体に集約します。担当からのネスト起動は read-only の探索（explorer 担当）に限ります。

以下の手順を**順番に**実行してください。通常 /pir2 と同一の考え方の箇所は `~/.claude/skills/pir2/SKILL.md`（共有原本）の対応する節、および `~/.claude/skills/pir2/references/*` を SSOT として参照します（DRY・二重管理回避）。**差分の本体はステップ 6（Codex 実装）**です。

**タスク**: $ARGUMENTS

---

## 担当の起動

各担当は `Agent({ subagent_type: "general-purpose", model: "<下表の model>", prompt: ... })` で起動する。prompt の先頭に「次の手順ファイルを先にReadし、その範囲だけ行う: <下表の手順path>」を置き、続けて各ステップが指定する入力（`RUN_DIR` / `*_INDEX` / 出力path 等）を渡す。権限が読み取り専用の担当には、prompt に「対象コード・設定・git・記憶を変更しない。出力pathが指定された場合だけそのpathへ書く」を含める。

| 担当 | model | 手順path | 権限 |
|---|---|---|---|
| explorer | haiku / sonnet / opus（調査の難度で選ぶ） | `~/.agents/skills/research/references/explorer.md` | 読み取り専用（出力path: `{RUN_DIR}/exploration-{NN}.md`） |
| planner | opus | `~/.claude/skills/pir2codex/references/planner.md` | 読み取り専用（出力path: `{RUN_DIR}/plan.md` と `{PROJECT_MEMORY_DIR}/pir_planner_log.md` への追記） |
| codex-runner | sonnet | `~/.claude/skills/codex/references/runner.md` | 読み書き（Codex CLI 実行と `WORK_DIR` 配下の証跡）。`run_in_background: true` で起動する |
| reviewer | sonnet | `~/.agents/skills/code-review-guidance/SKILL.md`、`~/.agents/skills/code-review-guidance/references/result-contract.md`、`~/.agents/skills/code-review-guidance/references/<REVIEWER_ROLE>.md` | 読み取り専用（出力path: `{RUN_DIR}/review-{NN}-{ROLE}.md`） |
| refactor-advisor | sonnet | `~/.agents/skills/refactor-advisor/references/refactor-guidance.md` | 読み取り専用 |
| tester | sonnet | `~/.agents/skills/tester/references/test-procedure.md`、`~/.agents/skills/code-review-guidance/references/result-contract.md` | 読み書き（テスト出力と一時 fixture のみ。実装は変更しない） |
| retrospector | opus | `~/.agents/skills/retro/references/retrospector.md` | 読み取り専用（出力path: スキル本体が指定したレポートpath） |

---

## ステップ 1: プロジェクトメモリパスと RUN_DIR の確定

以下の Bash コマンドで `PROJECT_ROOT` / `PROJECT_MEMORY_DIR` / `RUN_DIR` / `HANDOFF_PATH` を確定し、以降のすべてのステップで使用してください:

```bash
PROJECT_ROOT="$(pwd)"
# sanitized-cwd 計算（PROJECT_MEMORY_DIR 専用）は ~/.claude/skills/pir2/references/sanitized-cwd.md を SSOT とする
# RUN_DIR/HANDOFF_PATH は PROJECT_ROOT 基底（sanitize 不要）。sanitized_cwd は PROJECT_MEMORY_DIR 専用
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

`RESUME_MODE` の判定（resume / passive-notice / new）と RESUME_MODE 別の挙動は **pir2 共有原本の対応する考え方と同一**（詳細プロトコル: `~/.claude/pir-handoff.md`）。`PLAN_STRATEGY_CHANGED=false` を初期化する。以降の各担当へのプロンプト／Codex 実装プロンプトには必ず `PROJECT_MEMORY_DIR` / `RUN_DIR` / `PROJECT_ROOT` を含めてください。

---

## ステップ 2: ブレインストーミング（状況に応じて実施）

**pir2 共有原本の対応する考え方と同一**。要件が曖昧・アーキ選択が必要・対話で設計を固めたい場合のみ `brainstorm` スキルを実行し、結果をステップ4の planner に渡す。brainstorm 完了後は単独ターンで止まらず自動でステップ3へ進む。

---

## ステップ 3: 探索フェーズ（explorer）

**pir2 共有原本の対応する考え方と同一**。コードベース探索はメイン Claude が直接行わず、必ず explorer 担当を「担当の起動」の形式で起動（最低1体、独立領域なら最大3体並列、haiku/sonnet/opus 使い分け）。プロンプトには `RUN_DIR=[パス]` / `EXPLORATION_INDEX=NN`（初回=`01`、並列時は `01`/`02`/`03`）/「探索レポート本体は `{RUN_DIR}/exploration-{NN}.md` に書き出し、チャットには要約のみ返してください」/「実装・`git add`/`git commit` 等のリポジトリ状態変更は行わないでください」を必ず含める。稼働中の担当を探索フェーズに流用する場合のロール境界再注入は `~/.claude/skills/pir2async/SKILL.md`「稼働中の担当を探索フェーズに流用する場合のロール境界再注入」節と同じ手順に従う。

---

## ステップ 4: プラン策定（planner）

**pir2 共有原本の対応する考え方と同一**。planner 担当を「担当の起動」の形式で起動（model: opus）。プロンプトには `PROJECT_MEMORY_DIR` / `RUN_DIR` / `PLAN_STRATEGY_CHANGED` / タスク内容 / `{RUN_DIR}/exploration-*.md` のパス一覧を渡す。加えて:

- 「完全に独立した実装 shard がある場合のみ `IMPLEMENTATION_SHARDS` を提案してください（試験実装）」
- 「大きいが結合していて並列分割できない実装は `IMPLEMENTATION_UNITS`（順序付きの直列 unit）を提案してください（試験実装。`IMPLEMENTATION_SHARDS` と排他）」
- 「プランレポート本体は `{RUN_DIR}/plan.md` に書き出し、チャットには要約＋EXPLORATION_NEEDED の有無のみ返してください」

> ℹ️ planner は Claude のまま（実装役だけ Codex に差し替える統制比較のため）。planner の分割戦略観点（規模見積もり→ shards / units / 単一）は `~/.claude/skills/pir2codex/references/planner.md` 5.3 が SSOT。

既存パターン逸脱の事前申告が含まれていたら、実装着手前にユーザー確認する（結果を実質的に変える判断のみ確認し、確定済み事項は再質問しない）。

---

## ステップ 4.5: 能動的再探索ループ（最大5回）

**pir2 共有原本の対応する考え方と同一**。詳細プロトコル: `~/.claude/skills/pir2/references/exploration-loop.md`。

## ステップ 4.6: プラン選択肢のユーザー確認（該当時のみ・Auto mode でも例外なし）

**pir2 共有原本の対応する考え方と同一**。詳細プロトコル: `~/.claude/skills/pir2/references/plan-choice-gate.md`。別案 or 方針切替時は `PLAN_STRATEGY_CHANGED=true` をセットして planner 再起動。

---

## ステップ 5: プラン保存

**pir2 共有原本の対応する考え方と同一**。`docs/plans/YYYY-MM-DD-<feature>.md` に保存しユーザーに提示。

## ステップ 5.5: handoff.md 初期版生成（`RESUME_MODE=new` の場合のみ）

**pir2 共有原本の対応する考え方と同一**（詳細: `~/.claude/pir-handoff.md`）。

## ステップ 5.6: 次ステップキュー初期版生成

**pir2 共有原本の対応する考え方と同一**。詳細プロトコル: `~/.claude/skills/pir2/references/next-steps-queue.md`。ユーザー会話中断後は次の判断前に必ず `{RUN_DIR}/next-steps.md` を Read。各ステップ完了直後に checkbox を `[x]` 更新。

## ステップ 5.7: 破壊的変更チェックリスト + 動作変更チェック

**pir2 共有原本の対応する考え方と同一**。詳細プロトコル: `~/.claude/skills/pir2/references/destructive-change-check.md`。

## ステップ 5.8: 直前追加 feedback の自己照合ゲート

**pir2 共有原本の対応する考え方と同一**。詳細プロトコル: `~/.claude/skills/pir2/references/feedback-conflict-gate.md`。ただし照合対象は「Codex に渡す実装プロンプト案」の除外指示・スコープ縮小とする。

---

## ステップ 6: 実装（Codex）★ pir2codex の差分本体

`INNER_LOOP_COUNT = 0`、`OUTER_LOOP_COUNT = 0`、`VERIFY_RETRY_COUNT = 0` から開始してください。

ここが通常 /pir2 との唯一の実質差分です。implementer 担当（Claude）の代わりに **Codex（codex CLI、codex-runner 担当経由）が実装**します。`~/.claude/skills/codex/SKILL.md` が codex 実行の SSOT。

### 6-0: 実装 actor の決定（Codex 版マッピング）

通常 /pir2 と同じ判定ロジック（`~/.claude/skills/pir2/references/implementation-delegation.md`）で actor を決めるが、**実装主体は Claude implementer ではなく Codex セッション**になる。マッピング:

| /pir2 の actor | pir2codex での実体 |
|---|---|
| `implementer-subagent` | **codex-single**: Codex 1 セッションが plan 全体を実装（デフォルト） |
| `implementer-shards` | **codex-shards**: 独立 shard ごとに Codex セッションを並列実行（最大3） |
| `implementer-sequential` | **codex-sequential**: unit ごとに新しい Codex セッション（新 threadId）を `UNIT_ID` 昇順に直列実行。unit ごとにコンテキストまっさら |
| `main` | **codex-single に倒す**（実装を Claude に戻さない＝実験変数を保つ。pir2codex に Claude 直接実装の経路はない） |

判定は planner の `{RUN_DIR}/plan.md`（`IMPLEMENTATION_SHARDS` / `IMPLEMENTATION_UNITS`）と delegation.md の許可条件に従う。曖昧なら **codex-single**。

> **試験実装の注記**: `codex-shards` / `codex-sequential` は `~/.claude/skills/pir2/references/experimental.md` の `pir2-implementer-sequential-units`（直列）/ `pir2-implementer-shards-and-review-fix-shards`（並列）を SSOT に retrospector が観測する。判定が曖昧なら codex-single に倒す。

### 6-1: Codex セッションの実行（共通プロトコル）

Codex は codex CLI（`codex exec` / `codex exec resume`）で呼ぶ。**CLI 実行と完走管理は codex-runner 担当が担う**（`~/.claude/skills/codex/SKILL.md` が SSOT。MCP は使わない）。

スキル本体は codex-runner 担当を「担当の起動」の形式で **`run_in_background: true` で起動し、自分のターンを終える**。codex-runner が codex を最後まで走り切らせ、完了時にスキル本体が通知で起こされる。

> ⚠️ **スキル本体が foreground で待ってはならない。** Codex 実装は Bash ツールの timeout より長くかかる場合があり、メイン Claude の foreground ポーリングは進行を止める。待機は codex-runner の中に隔離する。

> ℹ️ 実装完了はステップ7 reviewer の前提なので、**codex-runner の完了通知を受け取るまでステップ7へ進まない**。「background だから待たない」ではなく「ターンを終えて通知で起こされる」。通知前に reviewer を走らせると空の diff をレビューすることになる。

**入出力はスキル本体が肩代わりする**。Codex は `workspace-write` sandbox で書き込みが `cwd`（リポジトリ）配下に限定される。`RUN_DIR`（`${PROJECT_ROOT}/.ai-pir-runs/<run>/`）は Codex に直接読み書きさせず、スキル本体が仲介するため:

1. スキル本体が `{RUN_DIR}/plan.md`（および該当時 review/test 指摘・先行 unit レポート）を **Read して全文を Codex 実装プロンプトに verbatim 埋め込む**（要約しない＝telephone-game 回避）
2. Codex は **リポジトリ内のコードだけを書く**
3. codex-runner が返した Codex の報告（変更ファイル一覧＋概要）をもとに、**スキル本体が implementation レポートを `{RUN_DIR}` に Write**（肩代わり）

#### codex-runner 起動前の基準取得（実受入確認の前提・必須）

codex-runner（6-1a/6-1b/6-1c いずれか）を起動する **前** に、`git -C "$PROJECT_ROOT" status --short` の出力を `{RUN_DIR}/verify-{IMPL_INDEX}-pre.txt` に保存する（codex-shards の並列起動時・codex-sequential の直列起動時も、この1回＝初回起動の直前のみ記録する）。Codex 完了後に同じコマンドを撮り直し、差分と Codex の自己申告を照合する（下記「codex-runner 返り後のスキル本体の処理」手順2）。

#### codex-runner への指示テンプレート

`SUFFIX` は codex-single では空、codex-shards では `-{SHARD_ID}`、codex-sequential では `-unit-{UNIT_ID}`。

`Agent({ subagent_type: "general-purpose", model: "sonnet", run_in_background: true, ... })` で起動し、プロンプト先頭に「次の手順ファイルを先にReadし、その範囲だけ行う: `~/.claude/skills/codex/references/runner.md`」を置いたうえで必ず含める:

| 名前 | 値 |
|---|---|
| `PROMPT` | 下記「Codex 実装プロンプト」の全文 |
| `CWD` | `$PROJECT_ROOT` |
| `SANDBOX` | `workspace-write`（実装フェーズなので書き込み可。相談用の `read-only` ではない） |
| `MODEL` | `gpt-5.6-sol` |
| `EFFORT` | `high`（難所の根本原因究明・複雑設計を伴う実装は `xhigh`）。ルブリックは `~/.claude/skills/codex/SKILL.md` が SSOT |
| `WORK_DIR` | `{RUN_DIR}` |
| `RUN_ID` | `impl-{IMPL_INDEX}{SUFFIX}` — **shard/unit ごとに必ず別の値**（衝突すると他人の完了を自分の完了と誤認する） |
| `SESSION_FILE` | `{RUN_DIR}/codex-impl{SUFFIX}.session`（inner-loop の再実装で同一 thread を resume するため） |

codex-runner は `EXIT` / `thread_id` / Codex の応答本文（変更ファイル一覧・実装概要・注意点）/ エラー / ポーリング総ラウンド数を返す。**結果を待たずにステップ7へ進まないこと。**

#### Codex 実装プロンプト（codex-runner に `PROMPT` として渡す本文）

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

#### codex-runner 返り後のスキル本体の処理（共通・順序厳守）

1. **implementation レポートを Write**: `{RUN_DIR}/implementation-{IMPL_INDEX}.md`（shard 時 `-{SHARD_ID}`、unit 時 `-unit-{UNIT_ID}`）に、Codex の変更ファイル一覧＋実装概要＋注意点を `~/.claude/skills/pir2codex/references/implementer.md`「実装完了レポートのフォーマット」に合わせて書き出す。Codex が「編集不要」と報告した場合は `### 注意点・未解決事項` に `NO_OP_JUSTIFIED: <理由>` を明記する。
2. **実受入確認（必須）**: `git -C "$PROJECT_ROOT" status --short` / `git -C "$PROJECT_ROOT" diff --stat` を撮り、手順1の pre 基準と比較して Codex の申告した変更ファイルが実際の diff に現れているかをスキル本体が実測照合する。Codex の自己申告だけを成功とみなさない（CLAUDE.md「ツール結果の捏造の絶対禁止」と同根。Codex も自己申告しうる）。申告と実差分が食い違う場合は原因を確認し、1 回だけ codex-runner を再実行する（`SESSION_FILE` があれば resume）。再実行後も食い違うならユーザーに実差分と申告の相違点を提示して判断を仰ぐ。プラン外への波及（プラン範囲逸脱）の意味的判断はこの実測照合の対象外で、後段 reviewer（ステップ7）が拾う。
3. **thread_id を保持**（`{RUN_DIR}/codex-impl{SUFFIX}.session` に永続化済み。inner-loop の resume 継続用）

### 6-1a: codex-single（デフォルト）

codex-runner を **1 体** background 起動（`SUFFIX` なし、`RUN_ID=impl-{IMPL_INDEX}`） → スキル本体はターンを終える → 完了通知で起こされる → implementation-{IMPL_INDEX}.md を Write → 実受入確認 → thread_id 保持。

### 6-1b: codex-shards（plan に `IMPLEMENTATION_SHARDS`・独立ゲート通過時）

delegation.md「shard 許可条件」を全て満たした各 shard を、**別々の codex-runner として同一メッセージ内に並列 background 起動**（`SUFFIX=-{SHARD_ID}`、`RUN_ID=impl-{IMPL_INDEX}-{SHARD_ID}`。shard ごとに独立した Codex セッション）。各 Codex プロンプトに当該 shard の許可/禁止ファイルを明記し「許可集合の外を編集するな」と指示。**全 codex-runner の完了通知が揃うまで次に進まない**（1 つでも未着なら待つ）。揃ったら「codex-runner 返り後のスキル本体の処理」手順1に従って shard ごとに `implementation-{IMPL_INDEX}-{SHARD_ID}.md` を Write する。その後スキル本体が delegation.md「shard 統合確認」（全 `implementation-{IMPL_INDEX}-*.md` を Read + git diff で競合・命名不整合・未接続を確認）を実施し、その**後**に手順2の実受入確認を全 shard の申告和集合に対して 1 回だけ実施する。問題があれば codex-single に戻して統合修正。

### 6-1c: codex-sequential（plan に `IMPLEMENTATION_UNITS`・unit ゲート通過時）

delegation.md「unit 許可条件」を満たした unit を `UNIT_ID` 昇順に **1 体ずつ直列**に codex-runner を background 起動（`SUFFIX=-unit-{UNIT_ID}`、`RUN_ID=impl-{IMPL_INDEX}-unit-{UNIT_ID}`。先行 unit の完了通知を受け取ってから次を起動する）。各 unit:

- **新しい Codex セッション（新 threadId・`SESSION_FILE` を渡さない）= コンテキストまっさら**
- スキル本体が**先行 unit の `git diff` と `implementation-{IMPL_INDEX}-unit-*.md` を Read し、当該 unit の `PROMPT` に埋め込む**（Codex 実装プロンプトの「先行 unit の成果」欄）。「先行 unit の命名・抽象・データ形状に従え」を明記
- Codex は当該 unit の範囲のみ実装

全 unit 完了後、スキル本体が delegation.md「unit 統合確認」（全 `implementation-{IMPL_INDEX}-unit-*.md` を Read + git diff で unit 境界の命名不整合・重複抽象・未接続を確認）を実施し、その**後**に手順2の実受入確認を全 unit の申告和集合に対して 1 回だけ実施する。問題があれば codex-single に戻して統合修正。

> ⚠️ codex-shards の並列起動では **`RUN_ID` を shard ごとに必ず別の値にする**。codex-runner は `WORK_DIR`/`RUN_ID` から導いた完了マーカーファイルの出現でポーリングを抜けるため、`RUN_ID` が衝突すると他 shard の完了を自分の完了と誤認し、未完成の状態で返る。

codex-sequential / codex-shards は**初回実装のみ**。reviewer/tester FAIL 後の再実装は統合済み diff に対し codex-single で行う（6-2）。

### 6-2: inner-loop の再実装（reviewer FAIL 後）

- **codex-single**: 新しい codex-runner を background 起動し、**同じ `SESSION_FILE`（`{RUN_DIR}/codex-impl.session`）を渡して同一 thread を resume**（Codex が実装文脈を保ったまま修正）。`PROMPT` には <FAIL を返した全 review-*.md の全文> を含める。`RUN_ID` は `impl-{新 IMPL_INDEX}` として前回と別の値にする。完了通知後に implementation-{新 IMPL_INDEX}.md を Write → `git diff` による軽量自己チェック（6-1 の実受入確認と同じ考え方を簡略適用する。初回実装点ほど厳密な pre/post 比較は必須ではない）
- **codex-shards / codex-sequential の初回後**: 統合済み diff に対し codex-single（新規 Codex セッション or 直近 threadId への reply）で修正する

### 完了後

`{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する（`~/.claude/skills/pir2/references/next-steps-queue.md` の4手順に従う。ループ複数回は最初の1回のみマーク）。

---

## ステップ 6.5: 実装者の未解決事項ユーザー確認（該当時のみ）

**pir2 共有原本の対応する考え方と同一**。`{RUN_DIR}/implementation-{最新}.md` の「注意点・未解決事項」が「あり」なら、(A) スコープ縮小承認 / (B) 再プラン / (C) 追加指示で再実装 をユーザーに確認し `{RUN_DIR}/user-decisions.md` に記録。仕様変更判断をスキル本体が独断しない。

---

## ステップ 7: レビューループ（reviewer ハイブリッド並列、最大3回）

**pir2 共有原本の対応する考え方と同一**（reviewer は Claude のまま＝Codex 実装を Claude が異種レビュー）。観点ごとの reviewer 担当は「担当の起動」の形式で起動し（model: sonnet）、`REVIEWER_ROLE` に対応する `references/<REVIEWER_ROLE>.md` を手順pathに含める。`REVIEWER_SET` 決定（デフォルト全5観点）→ **7-2A Fan-Out Gate 宣言 → 7-2B 並列発火**（詳細: `~/.claude/skills/pir2/references/fan-out-gate.md`）→ 7-3 VERDICT 集約 → 7-4 判定。

7-4 で FAIL かつ `INNER_LOOP_COUNT < 3` の場合の再実装は **ステップ 6-2（`codex exec resume` / codex-single）** で行う（implementer 担当の代わりに Codex）。FAIL を返した全 `{RUN_DIR}/review-{最新}-{ROLE}.md` の全文を Codex プロンプトに埋め込む。再レビューは同 REVIEWER_SET の reviewer 担当を 7-2A→7-2B により並列再起動（PASS 観点も退行検知のため再レビュー）。`INNER_LOOP_COUNT >= 3` でステップ7.5へ強制移行。

---

## ステップ 7.5: リファクタ提案（refactor-advisor 起動 → ゲート → 任意適用）

**pir2 共有原本の対応する考え方と同一**。詳細プロトコル: `~/.claude/skills/pir2/references/refactor-advisor-gate.md`。refactor-advisor 担当を「担当の起動」の形式で1体起動（model: sonnet）。提案適用（implementer 再起動の箇所）は **Codex（6-2 と同じ codex 経由）** で行い、適用後は 7-2A→7-2B で reviewer 担当を再起動して退行検知。同一 run 内1回のみ。

---

## ステップ 8: テストループ（tester、最大3回）

**pir2 共有原本の対応する考え方と同一**（tester は Claude）。tester 担当を「担当の起動」の形式で起動する（model: sonnet）。依頼内容の詳細: `~/.claude/skills/pir2/references/tester-prompt.md`。FAIL 時は `OUTER_LOOP_COUNT += 1` → 上限到達なら続行可能ゲート（`~/.claude/skills/pir2/references/continuation-gate.md`、Auto mode でも応答待ち）→ `INNER_LOOP_COUNT=0` リセット → **再実装は Codex（6-2、`{RUN_DIR}/test-{最新}.md` 全文を埋め込む）** → ステップ7へ戻る → tester 担当を再起動。

---

## ステップ 9: ウォークスルー生成（メイン Claude が直接）

**pir2 共有原本の対応する考え方と同一**。詳細テンプレート: `~/.claude/skills/pir2/references/walkthrough-templates.md`。最重要原則: 推測でコードを書かず、実際に Read したコードのみ引用する。

## ステップ 10: メモリへの記録

**pir2 共有原本の対応する考え方と同一**。`{PROJECT_MEMORY_DIR}/pir_skill_log.md` に追記。モデルスイープ計装の1行は implementer の箇所を `implementer=codex(gpt-5.6-sol,effort=<…>)×<セッション数>` として記録する（Codex 実装版であることを明示）。

## ステップ 11: 振り返り（retrospector、常に実行）

**pir2 共有原本の対応する考え方と同一**。retrospector 担当を「担当の起動」の形式で起動する（model: opus）。入力の詳細: `~/.claude/skills/pir2/references/retrospector-prompt.md`。`ワークフロー種別: pir2codex` を明示（通常 pir2 / pir2async との比較用）。`PLAN_STRATEGY_CHANGED` の現在値を渡す。experimental.md の `pir2-implementer-sequential-units` に該当 run の観測を促す。

## ステップ 11.5: handoff.md 完了判定と後処理

**pir2 共有原本の対応する考え方と同一**。詳細: `~/.claude/skills/pir2/references/handoff-cleanup.md`。

---

## ステップ 12: 最終サマリーの提示

以下をユーザーに提示してください:

```
## PIR² Codex 完了サマリー

### タスク
[タスクの説明]

### ワークフロー
pir2codex (Implement だけ Codex 版 — 実装主体 = Codex gpt-5.6-sol)

### 実装 actor / Codex セッション
- IMPLEMENTATION_ACTOR: [codex-single / codex-shards / codex-sequential]
- Codex セッション数: [N]（codex-sequential 時は unit 数 / codex-shards 時は shard 数）
- effort: [high / xhigh]

### 実装記録
docs/plans/YYYY-MM-DD-<feature>.md

### 変更ファイル
[implementation レポートから抜粋。実体検証の詳細は下記「実受入確認」ブロックを参照]

### レビュー結果
- 最終 VERDICT: [PASS/FAIL]
- 内側ループ回数: [INNER_LOOP_COUNT]
- [主な指摘事項]

### 実受入確認（ステップ6・codex-runner 返り後）
- Codex の申告と `git status --short` / `git diff --stat` の実差分: [一致 / 不一致→再実行1回で解消 / 不一致→再実行後もユーザーエスカレーション]
- VERIFY_RETRY_COUNT: [回数]

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

**pir2 共有原本の対応する考え方と同一**。ステップ9のサマリー版を提示し、末尾に `詳細なウォークスルーが必要な場合はお知らせください。` を添える。
