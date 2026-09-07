---
name: deepplan
description: Cursorで設計判断の重い依頼を、必要な探索・独立検討・統合から実装可能な計画へ整理する。親が計画と受入を所有し、固定人数・ラウンド・成果物を完了条件にしない。ユーザーが /deepplan と入力したときに使う。
argument-hint: "[計画したいタスク]"
---

<!-- Cursor native overlay: 共通deepplanのCursor実行方式。 -->

# Deepplan — Cursor

このnative入口の実体ディレクトリを基準に、共有原本 [../../../.agents/skills/deepplan/SKILL.md](../../../.agents/skills/deepplan/SKILL.md) を最初にReadします。別配置で起動されて相対pathを解決できない場合は、親が実在確認して渡した共有Skillの絶対pathを使います。親Cursor agentが目的、非目的、対象、所有、依存、受入、保存を保持し、未指定のRUN_DIR・report pathを作りません。

## Cursorでの実行

- 必要なローカル調査だけを `Task(subagent_type="explorer")` へ渡します。対象版、問い、確定事実、編集禁止、チャット返却を明示し、readerに保存や記憶追記をさせません。
- 独立した反証・トレードオフの検討が必要なら、Taskを必要な数だけ使い、親が結果を対象コードと照合します。Task数・モデル・ラウンドを固定しません。
- 独立検討を `deliberator` / `synthesizer` / `gate` に分ける場合、Cursor deepthinkの実体位置を基準に、今回実際に使う役割の [deliberator](../deepthink/references/deliberator.md)、[synthesizer](../deepthink/references/synthesizer.md)、[gate](../deepthink/references/gate.md) だけをReadします。各referenceの実在を確認し、その絶対pathを `SKILL_PATH` として対応するTaskへ渡します。親が直接計画を検討・統合する場合は、そのreferenceを読みません。
- Fableの名前付きモデル例外を使う場合は、Cursor deepthinkの [fable-model.md](../deepthink/references/fable-model.md) をこのnative入口の実体位置からReadし、そこに記載された起動契約へ従います。本文でモデル識別子、effort、方式、担当数、fallbackを再定義しません。指定が受理されない、Taskが途中終了する、Skillや入力を読めない場合は `INCOMPLETE` と理由を返し、inheritや別モデルへ黙ってフォールバックしません。

## 計画と返却

親は既存計画を保持して増分更新し、実装ステップ、排他的所有、依存、focused check、リスク、未解決の判断を返します。後段が必要な場合だけ、親が実在を確認した親directory配下の今回未使用のファイルpathへ保存します。計画から実装、レビュー、テスト、commit、pushへ自動進行しません。
