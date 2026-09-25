---
name: "ai-diary"
description: "会話を振り返ったAI視点の日記を作成・保存する。日記や感想の依頼に使う。作業改善の振り返りは /retro、知見の記録や要約は /ai-ltm。"
---

<!-- Cursor native overlay: Cursor の入口と共有原本の解決だけを定義する。 -->

# ai-diary — Cursor native entry

Cursor でロードされたら、まず共有原本 [../../../.agents/skills/ai-diary/SKILL.md](../../../.agents/skills/ai-diary/SKILL.md) を Read する。別配置で相対 path を解決できない場合は、親が実在確認して渡した共有 Skill の絶対 path を使う。保存先、本文形式、トラブルシュートを含む専門手順は共有 package を原本とし、この入口へ複製しない。

責任、直接実行、結果の返却・保存境界は共有原本に従う。日記の執筆は短い親の直接作業として扱い、Cursor の Task に親用の進行や保存を委任しない。Git 同期を行う場合も、親が明示した既存の同期手段と対象範囲を使う。Task の model/effort は AGENTS の runtime 方針に従い、この入口で固定しない。
