---
name: deepthink
description: Cursorで複雑な問いを、必要な探索・Fable（またはユーザー指名のOpus 5.5）による独立した熟考・統合・十分性確認へ分けて考える。single/panelの方式を使い、親だけで熟考を完了させない。ユーザーが /deepthink と入力したときに使う。
argument-hint: "[深く考えたい状況・論点] [--panel | --opus-panel]"
---

<!-- Cursor native overlay: 共通deepthinkのCursor実行方式。 -->

# Deepthink — Cursor

**状況・論点**: `$ARGUMENTS`

このnative入口の実体ディレクトリを基準に、共有原本 [../../../.agents/skills/deepthink/SKILL.md](../../../.agents/skills/deepthink/SKILL.md) を最初にReadし、その手順に従います。続けて [../../../.agents/skills/deepthink/references/fable-model.md](../../../.agents/skills/deepthink/references/fable-model.md) をReadし、Cursor 行のモデル指定を確定します。別配置で起動されて相対pathを解決できない場合は、親が実在確認して渡した共有Skillの絶対pathを使います。

## Cursorでの実行

- 熟考・統合・十分性確認の担当は標準Task（`subagent_type: "generalPurpose"`）で起動し、`model` に fable-model.md の Cursor 行の識別子を渡します。effort はモデル識別子に含まれ、`[effort=…]` では渡しません。panel では全担当に同じ識別子を使い、同時に起動します。
- 役割referenceは共有 `deepthink/references/{deliberator,synthesizer,gate}.md` の実在を確認した絶対pathを `SKILL_PATH` として渡し、担当自身にReadさせます。
- 必要なローカル調査は `explorer` Task へ渡し、共有 `research/references/explorer.md` の絶対pathと、対象版、問い、確定事実、編集禁止、チャット返却を明示します。
- 指定が受理されない、Taskが途中終了する、Skillや入力を読めない場合は `INCOMPLETE` と理由を返し、inheritや別モデルへ黙ってフォールバックしません。
