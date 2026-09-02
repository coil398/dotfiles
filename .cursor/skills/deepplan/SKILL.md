---
name: "deepplan"
description: planner の代わりに deepthink 型ループで実装プランを深く策定する。探索 → 熟考 → 統合 → ゲートで `{RUN_DIR}/plan.md`（planner 互換）を出す。「深いプラン」「deepplan」「しっかり計画してから実装」「設計判断が重い計画」に使う。ユーザーが /deepplan と入力したら必ずこのスキルを使う。/pir2 --deepplan 等からは PLAN_MODE=deepplan として呼ばれる。
argument-hint: [計画したいタスク]
---

<!-- Cursor native overlay: seeded from .agents/skills; edit here for Cursor mechanics -->

> **Cursor 実行時の注意**
> - 子エージェントは `Task` ツール（`subagent_type`）で起動する。Task / subagent の語彙だけを使う
> - メインエージェントがオーケストレーター。VERDICT ループ・ユーザー確認ゲート・ループカウンタはメインが保持する
> - 別ランタイム専用機能（`TeamCreate` / 専用チーム / `~/.claude/hooks`）は Cursor では非対応のためスキップする（必要なら通常の直列 Task 起動へ縮退）
> - Task の `model` は省略するか `inherit` のみ（親 Auto に従う）。ベンダー名はハードコードしない
> - Cursor agent の `model` は `inherit` か公式モデル ID。仕事の分類は `role: coding|reasoning`
> - **本スキル例外**: deliberator / synthesizer / gate だけは `claude-fable-5-1[effort=medium]` を Task `model` に渡す（短名 `fable` 禁止。SSOT: `.agents/skills/deepthink/references/fable-model.md`）。explorer は `inherit`。失敗時は inherit + panel にフォールバック

# Deepplan — 深い実装プラン策定（planner 代替）

共有手順の全文は `.agents/skills/deepplan/SKILL.md` を **最初に Read** し、その手順に従う。以下は Cursor 固有の読み替えのみ。

**タスク**: $ARGUMENTS

## Cursor 読み替え

| 共有側の語彙 | Cursor |
|---|---|
| 子エージェント起動 / `Agent` | `Task`（`subagent_type`） |
| `model: sonnet`（explorer） | `inherit` |
| `model: claude-fable-5-1` | Task `model: claude-fable-5-1[effort=medium]`（`--effort=low|medium|high|max` で上書き。既定 medium） |
| `deliberator` / `synthesizer` / `gate` / `explorer` | 同名の Cursor subagent overlay（無ければ `generalPurpose` + 役割プロンプト） |

手順・rubric・plan.md 契約・禁止事項は共有 SKILL が SSOT。重複して薄めない。
