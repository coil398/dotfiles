---
name: deepthink
description: Cursorで判断に迷う重要な論点を独立した熟考担当に検討させ、結論と未解決点を整理する。選択肢の比較や設計判断に確信を持てない場合に使う。要件をユーザーと決める場合は brainstorm、計画作成は deepplan。
argument-hint: "[深く考えたい状況・論点] [--panel | --opus-panel]"
---

<!-- Cursor native overlay: 共通deepthinkのCursor実行方式。 -->

# Deepthink — Cursor

**状況・論点**: `$ARGUMENTS`

このnative入口の実体ディレクトリを基準に、共有原本 [../../../.agents/skills/deepthink/SKILL.md](../../../.agents/skills/deepthink/SKILL.md) を最初にReadし、その手順に従います。続けて [../../../.agents/skills/deepthink/references/model.md](../../../.agents/skills/deepthink/references/model.md) をReadし、モデル指定を確定します。別配置で起動されて相対pathを解決できない場合は、親が実在確認して渡した共有Skillの絶対pathを使います。

## Cursorでの実行

- 熟考・統合・十分性確認の担当は標準Task（`subagent_type: "generalPurpose"`）で起動します。`model` は native Rule（`skill-procedure.mdc`）に従い、ユーザーがモデルを名前で指定した場合だけ model.md の Cursor 行の識別子を渡します。effort はモデル識別子に含まれ、`[effort=…]` では渡しません。panel では全担当に同じモデルを使い、同時に起動します。
- 役割referenceは共有 `deepthink/references/{deliberator,synthesizer,gate}.md` の実在を確認した絶対pathを `SKILL_PATH` として渡し、担当自身にReadさせます。
- 必要なローカル調査は `explorer` Task へ渡し、共有 `research/references/explorer.md` の絶対pathと、対象版、問い、確定事実、編集禁止、チャット返却を明示します。
- 指定が受理されない、Taskが途中終了する、Skillや入力を読めない場合は `INCOMPLETE` と理由を返し、inheritや別モデルへ黙ってフォールバックしません。
