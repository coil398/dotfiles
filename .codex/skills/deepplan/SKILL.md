---
name: "deepplan"
description: "planner の代わりに deepthink 型ループで実装プランを深く策定する。探索 → 熟考 → 統合 → ゲートで `{RUN_DIR}/plan.md`（planner 互換）を出す。「深いプラン」「deepplan」「しっかり計画してから実装」「設計判断が重い計画」に使う。ユーザーが /deepplan と入力したら必ずこのスキルを使う。/pir2 --deepplan 等からは PLAN_MODE=deepplan として呼ばれる。"
argument-hint: "[計画したいタスク]"
---

<!-- Codex native overlay: seeded from .agents/skills; edit here for Codex mechanics -->

# Deepplan — 深い実装プラン策定（planner 代替）

共有手順の全文は、発見済み共有skillの実体（通常 `${HOME}/.agents/skills/deepplan/SKILL.md`）を **最初に Read** する。対象アプリrepo内の `.agents/skills` を仮定しない。以下の Codex 固有の読み替えを適用し、計画・要件・最終受入は親Astraが所有する。

**タスク**: $ARGUMENTS

## Codex 読み替え

| 共有 SKILL 語彙 | Codex |
|---|---|
| `Agent` / Claude model ピン | Codex collaboration / role（`explorer` / `deliberator` / `synthesizer` / `gate`） |
| `claude-fable-5-1` + effort `medium` | Codexの当該role定義を使う。独立した難所をexpertへ渡す判断はworker-delegationに従い、初手Solも選べる。Claudeモデル名をCodexへ渡さない |
| deliberator 1体（fable-single） | deliberator role を **1体**（`--opus-panel` 時のみ複数） |
| `{RUN_DIR}/plan.md` | 同一契約。planner レポートフォーマット互換 |

手順・rubric・plan.md 契約・禁止事項は共有 SKILL が SSOT。重複して薄めない。
