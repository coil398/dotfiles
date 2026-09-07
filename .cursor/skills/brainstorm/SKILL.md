---
name: brainstorm
description: Cursorで実装前の要件・設計選択を整理する対話スキル。結果を変える未決定と既存パターンからの逸脱だけを明確にし、明確な小さな依頼には不要な質問をしない。ユーザーが /brainstorm と入力したときに使う。
argument-hint: "[テーマ]"
---

<!-- Cursor native overlay: 共通brainstormのCursor実行方式。 -->

# Brainstorm — Cursor

このnative入口の実体ディレクトリを基準に、共有原本 [../../../.agents/skills/brainstorm/SKILL.md](../../../.agents/skills/brainstorm/SKILL.md) を最初にReadします。別配置で起動されて相対pathを解決できない場合は、親が実在確認して渡した共有Skillの絶対pathを使います。親Cursor agentが要件、scope、質問、設計、承認を所有します。承認済み設計ができるまでコードを変更しません。

## Cursorでの実行

- 広域のコードベース探索が設計に必要な場合だけ、Cursor の標準 Task または標準 read-only child を使います。対象版、問い、確定事実、所有範囲、編集禁止、チャットで返す根拠と、必要な実行者用 Skill / reference の実体 path を渡し、子自身に必要な資料を Read させます。特定の職種名や固定のTask識別子を必須にせず、既知の単一ファイルは親が確認できます。
- Taskの起動値は親のruntime方針に従い、担当数を固定しません。Taskの途中終了・未読・timeoutは未確認として返し、結果を捏造しません。
- 親が直接探索・設計する場合だけ、必要な共有referenceを親自身がReadします。子へファイル保存、記憶追記、コード変更、外部投稿を要求せず、返却を親が既存コードと照合します。子は親用 `/brainstorm` の進行や委任を再起動しません。

## 返却

共通原本の形式で採用案、決定、非目的、受入条件、検証、残るユーザー判断を返します。保存はユーザーまたは後段の実在消費者が指定した場合だけ親が行い、実装・commit・push・外部投稿へ自動拡張しません。
