---
name: "ai-design-system"
description: "プロジェクト内のデザインシステムSSOTを生成・監査・維持する。トークン・命名・カラーパレット・スペーシングの一貫性と、aesthetic direction・Typography・Motion・装飾レイヤーによる個性を管理し、アクセシビリティ (accessibility) にも配慮しながら、Inter / 紫グラデーション / 中央寄せ定型などのgeneric AI aestheticsへの無意図な収束を避ける。自然言語トリガー例: 「デザインシステムを作って」／「デザイントークンを整理して」／「UIの見た目を揃えて」／「アクセシビリティを改善して」。該当する依頼ではスキル名がなくても使い、デザインSSOT、トークン、タイポグラフィ、モーション、装飾に関する作業でも参照する。ユーザーが /ai-design-system と入力したら必ず使う。"
---

<!-- Cursor native overlay: Cursor の入口と共有原本の解決だけを定義する。 -->

# ai-design-system — Cursor native entry

Cursor でロードされたら、まず共有原本 [../../../.agents/skills/ai-design-system/SKILL.md](../../../.agents/skills/ai-design-system/SKILL.md) を Read する。別配置で相対 path を解決できない場合は、親が実在確認して渡した共有 Skill の絶対 path を使う。`BOOTSTRAP.md`、`AUDIT.md`、`IDEAL.md`、`AESTHETIC.md`、stack reference は共有 package を原本とし、この入口へ複製しない。

責任、親が直接読む範囲、委任時に渡す実行者資料、結果の返却・保存境界は共有原本に従う。Cursor の標準 Task や実際に利用できる UI/MCP 操作を使う場合も、親が対象と受入を持ち、担当へ親用の進行を再起動させない。Task の model/effort は AGENTS の runtime 方針に従い、この入口で固定しない。
