---
name: deepplan
description: planner の代わりに deepthink 型ループで実装プランを深く策定する。探索 → Fable 熟考 → 統合 → ゲートで `{RUN_DIR}/plan.md`（planner 互換）を出す。「深いプラン」「deepplan」「しっかり計画してから実装」「設計判断が重い計画」に使う。ユーザーが /deepplan と入力したら必ずこのスキルを使う。/pir2 --deepplan 等からは PLAN_MODE=deepplan として呼ばれる。
argument-hint: [計画したいタスク]
---

# Deepplan — 深い実装プラン策定（planner 代替）

実装プランを **deepthink 型ループ**で策定する。通常の `planner` 1体起動の代わりに、探索 → 熟考（Fable 1体）→ 統合 → ゲートを回し、**implementer が迷わず実行できる `{RUN_DIR}/plan.md`**（planner レポートフォーマット互換）を出す。

**タスク**: $ARGUMENTS

モデル / effort / 体数の SSOT: `.agents/skills/deepthink/references/fable-model.md`（`claude-fable-5-1`、effort 既定 `high`、deliberator は **1体**）。

| フェーズ | 担当 | モデル |
|---------|------|--------|
| 探索 | explorer（最大4体） | `sonnet` |
| 集約 + rubric | オーケストレーター | メインセッション |
| 熟考 | deliberator（1体） | `claude-fable-5-1` |
| 統合 | synthesizer | `claude-fable-5-1` |
| ゲート | gate | `claude-fable-5-1` |
| plan.md 確定 | オーケストレーター（または synthesizer 最終出力） | — |

フラグ（`$ARGUMENTS` から検出してタスク文言から除外）:

- `--effort=max` → effort max
- `--opus-panel` → deliberator を opus 複数体（通常は使わない）
- 呼び出し元が既に `RUN_DIR` / `PROJECT_MEMORY_DIR` / 探索パスを渡している場合は **ステップ0を再利用**し、新規 RUN_DIR を切らない

---

## ステップ 0: パス確定（standalone 時）

呼び出し元（`/pir2 --deepplan` 等）が既に渡している場合はその値を使う。無いときだけ:

```bash
PROJECT_ROOT="$(pwd)"
sanitized_cwd="$(pwd | sed 's|[^a-zA-Z0-9]|-|g')"
PROJECT_MEMORY_DIR="${HOME}/.claude/projects/${sanitized_cwd}/memory"
run_ts="$(date +%Y%m%d-%H%M%S)"
run_feature="$(printf '%s' "$ARGUMENTS" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
[ -z "$run_feature" ] && run_feature="deepplan"
RUN_DIR="${PROJECT_ROOT}/.ai-pir-runs/${run_ts}-${run_feature}"
mkdir -p "$RUN_DIR"
if git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  grep -qxF '/.ai-pir-runs/' "${PROJECT_ROOT}/.gitignore" 2>/dev/null || echo '/.ai-pir-runs/' >> "${PROJECT_ROOT}/.gitignore"
fi
echo "RUN_DIR=$RUN_DIR"
echo "PROJECT_MEMORY_DIR=$PROJECT_MEMORY_DIR"
```

渡されうる追加入力: `PLAN_STRATEGY_CHANGED` / `HANDOFF_PATH` / `{RUN_DIR}/exploration-*.md` パス一覧 / ブレインストーミング結果。

---

## ステップ 1: プラン用 rubric ドラフト

`{RUN_DIR}/rubric.md` に **実装プランの十分性**基準を書く（gate が客観照合できる形）:

必須観点の例:

1. 字義スコープが明示され、指示外拡張が無い
2. 既存パターン（同レイヤー 3+）との関係が根拠つき
3. 実装ステップがファイル・関数単位で具体的
4. 検証が implementer 自己検証と tester 専任に分離されている
5. 主要リスク・反証・前提が崩れる条件がある
6. `EXPLORATION_NEEDED` / `USER_DECISION_REQUIRED` の要否が判定されている

---

## ステップ 2: 探索

既存の `{RUN_DIR}/exploration-*.md` が十分なら追加探索を省略してよい。不足なら `explorer`（`sonnet`）を最大4体並列。観点:

- 同一ドメイン・同一レイヤーの既存実装パターン
- 再利用可能な util / 既存 API
- 自動生成境界・AppMode 対称性・テスト seed 影響
- （`PLAN_STRATEGY_CHANGED=true` 時）関連 feedback / CLAUDE.md ルール

プロンプトに「実装・git 変更禁止。結果は `{RUN_DIR}/exploration-{NN}.md`」を含める。

---

## ステップ 3: context + rubric 確定 + ユーザーゲート

- 全 exploration を `{RUN_DIR}/context.md` に集約（コードは逐語。deepthink ステップ3と同じ密度）
- rubric を確定
- standalone 起動時のみ rubric 承認ゲート（A/B/C）。`/pir2` 等の委譲時は呼び出し元が既に探索済みなら **(A) 相当で続行**し `user-decisions.md` に記録

---

## ステップ 4: 熟考ループ（最大4ラウンド）

deepthink と同じ Fan-Out / PASS まで反復。違いは **レンズと最終成果物**:

**Fan-Out Gate（既定 fable-single）**

```
> THINKER_MODE = fable-single
> EFFORT = high
> 起動体数 = 1
> LENS = 全レンズ統合
```

**ROUND 1 レンズ（1体に内包）**:

1. `アーキテクチャ・既存パターン` — どこに何を置くか、既存多数派との整合
2. `リスク・反証・スコープ` — 壊れる点、字義超え、代替案
3. `実装可能性・検証分離` — ステップ粒度、tester/implementer 境界、依存順

ROUND ≥2 は gate の needs-thinking に照準。

deliberator / synthesizer / gate は `model: claude-fable-5-1`。成果物:

- `{RUN_DIR}/deliberation-{ROUND}-01.md`
- `{RUN_DIR}/position-{ROUND}.md` — **この position は「実装方針の論証」**（まだ plan.md フォーマットでなくてよい）
- `{RUN_DIR}/gate-{ROUND}.md`

---

## ステップ 5: plan.md 確定（必須）

gate PASS（またはハードキャップの暫定）後、オーケストレーターが `{RUN_DIR}/position-{最終}.md` と context / exploration を材料に、**planner エージェント定義の「プランレポートフォーマット」完全互換**で `{RUN_DIR}/plan.md` を Write する。

フォーマット SSOT: `~/.claude/agents/planner.md`（または `.claude/agents/planner.md`）の「プランレポートフォーマット」節。最低限含める:

- 概要 / 実装ステップ（ファイル・関数単位）
- 適用される既存ルール
- テスト・検証方法（implementer 自己検証と tester 専任を分離）
- 注意点・リスク
- `EXPLORATION_NEEDED`（無ければ `- なし`）
- 必要なら `USER_DECISION_REQUIRED` / `IMPLEMENTATION_SHARDS` / `IMPLEMENTATION_UNITS`

`PLAN_STRATEGY_CHANGED=true` のときは v1 判断白紙化チェック表も入れる。

チャット返却は要約のみ:

```
PLAN_PATH={RUN_DIR}/plan.md
EXPLORATION_NEEDED: あり/なし
USER_DECISION_REQUIRED: あり/なし
THINKER_MODE / EFFORT / rounds
```

フル plan.md をチャットに貼らない。

---

## 呼び出し元との契約

| 呼び出し | deepplan の責務 | 呼び出し元の責務 |
|---|---|---|
| `/deepplan` standalone | 0〜5 を完遂。任意で `docs/plans/` へ要約コピー可 | — |
| `/pir2 --deepplan` 等 | 同一 `RUN_DIR` で plan.md まで | 既存の 4.5 EXPLORATION_NEEDED ループ / 4.6 ユーザー確認 / implement 以降 |

呼び出し元が EXPLORATION_NEEDED 残を検出したら、通常どおり追加探索 → **deepplan 再実行（同 RUN_DIR）**または planner 再起動ポリシーに従う（既定は deepplan 再実行）。

---

## 禁止

- deliberator を Fable で複数体並列にしない
- 短名 `fable` だけをモデル ID にしない（`claude-fable-5-1` をピン）
- gate PASS 前に plan.md を「完成」扱いしない
- implementer / reviewer / tester を deepplan 内で起動しない
