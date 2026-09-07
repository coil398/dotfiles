---
name: agent-skill-migrate
description: 明示されたCodex・CursorのSkill運用移行を、指定設計と既存点検に基づき適用する。通常の実装依頼では起動しない。
disable-model-invocation: true
---

# Agent / Skill Migrate — Cursor

親用の入口。[共有手順](../../../.agents/skills/agent-skill-migrate/SKILL.md)を、ロード済みの本Skillの実体から解決して読む。別配置では親が実在確認した共有Skillの絶対pathを用い、対象repoやHOMEから推測しない。

共有手順に従って`mode`・`runtime`・`scope`・対象・既存点検を解釈する。起動・model選択は共有`AGENTS.md`のCursor方針と実際のTask schemaに従う。Codexの起動引数をTaskへ移植しない。
