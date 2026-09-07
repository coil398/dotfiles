---
name: "retro"
description: "実際の作業結果からパターンを汎化し、次回に役立つ改善を提案する。振り返り・ふりかえり・retrospective・改善サイクル・エージェント定義の見直し・パターン分析に使う。`--meta` と `--dream` はユーザーが明示した場合だけ使う。ユーザーが /retro と入力したら使う。"
argument-hint: "[--meta] [--dream] [対象プロジェクトのパス]"
---

<!-- Cursor native overlay: Cursor の Task 起動方式と共有 reference の解決だけを定義する。 -->

# retro — Cursor native entry

Cursor でロードされたら、まず共有原本 [../../../.agents/skills/retro/SKILL.md](../../../.agents/skills/retro/SKILL.md) を Read する。通常は `references/retrospector.md`、`--meta` / `--dream` は `references/meta-retrospector.md` を、共有 package の実体から解決する。相対 path を解決できない場合は、親が実在確認して渡した絶対 path を使い、この入口へ reference を複製しない。

親は対象、モード、入力、保存・承認・統合を持つ。独立分析に利益がある場合だけ Cursor の標準 Task を一体起動し、親が確認した reference の物理 path、対象版、変更禁止、返却形式を渡して担当自身に Read させる。子は結果だけを返し、親の振り返り工程を再起動せず、report・memory・registryを保存しない。Task の model/effort は AGENTS の runtime 方針に従い、この入口で固定しない。
