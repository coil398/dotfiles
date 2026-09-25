---
name: "instruction-refactor"
description: "AGENTS.md・エージェント定義・スキルの肥大化、重複、競合、過剰な発火条件を整理する。指示の監査・改善を求められたとき、または指示編集で具体的な問題を見つけたときに使う。通常のコード整理は対象外。"
argument-hint: "[--scope=user|project|all] [--no-implement] [path]"
---

<!-- Cursor native overlay: Cursor の入口と共有評価資料への接続だけを定義する。 -->

# instruction-refactor — Cursor native entry

Cursor でロードされたら、まず共有原本 [../../../.agents/skills/instruction-refactor/SKILL.md](../../../.agents/skills/instruction-refactor/SKILL.md) を Read する。別配置で相対 path を解決できない場合は、親が実在確認して渡した共有 Skill の絶対 path を使う。`references/official-criteria.md`、`checklist.md`、`strategies.md` は共有 package を原本とし、この入口へ複製しない。

親は scope、対象、改善承認、所有、受入、最終判断を持つ。今回の判断に必要な reference だけを選ぶ。委任する場合は、親が共有原本から解決し実在確認した reference の物理 path、対象版、変更禁止、返却形式を担当へ渡し、担当自身に Read させる。親が直接確認する場合も選んだ reference を Read する。担当は測定・判定を返すだけで対象・report・記憶を変更せず、親の探索・判定・改善工程を再起動しない。Task の model/effort は AGENTS の runtime 方針に従い、この入口で固定しない。
