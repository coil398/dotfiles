---
name: deepplan
description: Cursorで設計判断の重い依頼を、必要な探索・独立検討・統合から実装可能な計画へ整理する。親が計画と受入を所有し、固定人数・ラウンド・成果物を完了条件にしない。ユーザーが /deepplan と入力したときに使う。
argument-hint: "[計画したいタスク]"
---

<!-- Cursor native overlay: 共通deepplanのCursor実行方式。 -->

# Deepplan — Cursor

このnative入口の実体ディレクトリを基準に、共有原本 [../../../.agents/skills/deepplan/SKILL.md](../../../.agents/skills/deepplan/SKILL.md) を最初にReadします。別配置で起動されて相対pathを解決できない場合は、親が実在確認して渡した共有Skillの絶対pathを使います。親Cursor agentが目的、非目的、対象、所有、依存、受入、保存を保持し、未指定のRUN_DIR・report pathを作りません。

## Cursorでの実行

- 必要なローカル調査だけを Cursor の標準 Task または標準 read-only child へ渡します。対象版、問い、確定事実、編集禁止、チャット返却と、必要な実行者用 Skill / reference の実体 path を明示し、子自身に必要な資料を Read させ、readerに保存や記憶追記をさせません。
- 独立検討を分ける場合、Cursor deepthinkの実体位置を基準に、今回使う [deliberator](../deepthink/references/deliberator.md)、[synthesizer](../deepthink/references/synthesizer.md)、[gate](../deepthink/references/gate.md) の実体存在だけを確認します。親は内容を先読みせず、各絶対pathを `SKILL_PATH` として対応するTaskへ渡し、担当自身にReadさせます。独立した熟考・統合・十分性確認Taskを起動するときは [fable-model.md](../deepthink/references/fable-model.md) を親がReadしてFableの起動指定を確定します。親が直接計画を作る場合は共有 `writing-plan/references/planner.md` の必要な部分を、親が直接統合・十分性確認する場合は対応するreferenceをReadします。
- Fableの指定が受理されない、Taskが途中終了する、Skillや入力を読めない場合は `INCOMPLETE` と理由を返し、inheritや別モデルへ黙ってフォールバックしません。本文でモデル識別子、effort、方式、担当数、fallbackを再定義せず、子へ親用 `/deepplan` の進行手順を渡して同じ計画工程を再起動させません。

## 計画と返却

計画結果の照合、保存、実装への受け渡しは親が行い、この入口からcommitやpushへ自動進行しません。
