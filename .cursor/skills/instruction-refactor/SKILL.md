---
name: "instruction-refactor"
description: "既存の CLAUDE.md / agents / skills の肥大化を Anthropic 公式基準（SKILL.md ≤ 500 行、bloat warning）と構造的悪さ（責務越境 / SSOT 逸脱 / DRY 違反 / 二重説明）の観点で検出し、Progressive Disclosure / 共通骨格の references 外出し / SSOT 参照への置換などで実際に整理する（検出だけで終わらない）。「instruction file 整理」「肥大化リファクタ」「skill の長さ大丈夫？」「定期メンテ」「棚卸し」「audit」「instruction bloat」「.codex/ 整理」「CLAUDE.md 削って」といった要望や、agents / skills を編集して肥大化・重複・SSOT 逸脱が気になったときの整合性確認にも使う。コードのリファクタ提案を出す refactor-advisor とは対象が違う（こちらは instruction file 専用、向こうはソースコード専用）。ユーザーがこれらに該当することを明示的に名指ししなくても積極的に使う。ユーザーが /instruction-refactor と入力したら必ずこのスキルを使う。"
argument-hint: "[--scope=user|project|all] [--no-implement] [path]"
---

<!-- Cursor native overlay: Cursor の入口と共有評価資料への接続だけを定義する。 -->

# instruction-refactor — Cursor native entry

Cursor でロードされたら、まず共有原本 [../../../.agents/skills/instruction-refactor/SKILL.md](../../../.agents/skills/instruction-refactor/SKILL.md) を Read する。別配置で相対 path を解決できない場合は、親が実在確認して渡した共有 Skill の絶対 path を使う。`references/official-criteria.md`、`checklist.md`、`strategies.md` は共有 package を原本とし、この入口へ複製しない。

親は scope、対象、改善承認、所有、受入、最終判断を持つ。委任する場合は、親が共有原本から解決し実在確認した必要な reference の物理 path、対象版、変更禁止、返却形式を担当へ渡し、担当自身に Read させる。親が直接確認する場合も同じ reference を Read する。担当は測定・判定を返すだけで対象・report・記憶を変更せず、親の探索・判定・改善工程を再起動しない。Task の model/effort は AGENTS の runtime 方針に従い、この入口で固定しない。
