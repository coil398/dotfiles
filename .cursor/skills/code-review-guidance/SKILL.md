---
name: code-review-guidance
description: Cursorで指定観点を評価するnative入口。共有code-review-guidanceと担当referenceを読み、結果を親へ返す。
---

<!-- Cursor native overlay: runtime entry; shared review rules live in .agents -->

# Code Review Guidance — Cursor native entry

次の共有原本を、このSkillの実体ディレクトリから相対して解決する。

~~~text
SHARED_SKILL_PATH=../../../.agents/skills/code-review-guidance/SKILL.md
RESULT_PATH=../../../.agents/skills/code-review-guidance/references/result-contract.md
REFERENCES_DIR=../../../.agents/skills/code-review-guidance/references
~~~

評価TaskはSHARED_SKILL_PATHとRESULT_PATHをReadし、親が指定した担当referenceを自身でReadする。対象repoのcwd、~/.cursor/projects、固定Agent定義から資料を推測しない。担当配分、別Task起動、結果集約、report保存、記憶追記、実装、commit、pushを行わない。CursorのTask実行設定は公開schemaとruntime方針に従い、親から渡されたrepo・版・差分・REVIEWER_ROLE・実体path・受入条件を欠落なく使い、共有result-contractのCOVERAGE/VERDICT形式で返す。
