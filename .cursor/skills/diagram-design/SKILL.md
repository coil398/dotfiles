---
name: diagram-design
description: "技術図・概念図・比較図・データ図を設計・生成し、掲載サイズの画像で批判的にレビューして修正する。図解の作成、可読性改善、既存図のレビューに使う。"
---

# Diagram Design — Cursor entry

共有原本 [../../../.agents/skills/diagram-design/SKILL.md](../../../.agents/skills/diagram-design/SKILL.md) を Read して実行する。相対 path はロード済み Skill の実体位置から解決し、別配置では親が実在確認して渡した共有 Skill の絶対 path を使う。専門手順をこの入口へ複製しない。

親が Plan、担当範囲、掲載条件、指摘の採否、最終判断を持つ。画像レビューを分業する場合は、生成担当とは別の、画像を読める標準 `generalPurpose` Task に対象画像、元の要件、掲載条件、根拠、共有 `references/visual-review.md` の実体 path を渡す。担当自身がその手順と画像を読み、対象を変更せず結果を返す。親の制作ループを子へ再実行させない。

Task の model/effort と待機方法は既存の runtime 方針に従う。画像確認や独立した担当の起動を実行できなければ、共有手順どおり未実行範囲を明記する。
