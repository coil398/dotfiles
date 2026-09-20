---
name: field-notes
description: "進行中の方針変更やキャンペーン再開で、短期の判断・仮説を自動capture / recall / triageする。長期記憶や日記には使わない。"
---

<!-- Cursor native overlay: Cursor の入口と共有判断キャッシュへの接続だけを定義する。 -->

# field-notes — Cursor native entry

Cursor でロードされたら、まず共有原本 [../../../.agents/skills/field-notes/SKILL.md](../../../.agents/skills/field-notes/SKILL.md) を Read する。別配置で相対 path を解決できない場合は、親が実在確認して渡した共有 Skill の絶対 path を使う。capture / recall / triage の境界と note の形式は共有 package を原本とし、この入口へ複製しない。

親は campaign、scope、操作、保存先、次の判断への統合を持つ。Cursor の Task に recall を委任する場合だけ、親が選択し実在確認した INDEX/note の物理 path、変更禁止、返却形式を渡し、担当自身に Read させる。担当は根拠を親へ返すだけで保存・promote・triageを行わず、親の工程を再起動しない。Task の model/effort は AGENTS の runtime 方針に従い、この入口で固定しない。
