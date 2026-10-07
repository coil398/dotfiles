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

評価TaskはSHARED_SKILL_PATHと、親が指定した担当referenceを自身でReadする。実装前の専門検討ではREFERENCES_DIRの `pre-implementation.md` を読み、その返却手順を使う。最終レビューだけRESULT_PATHをReadし、COVERAGE/VERDICT形式で返す。

対象repoのcwd、~/.cursor/projects、固定Agent定義から資料を推測しない。担当配分、別Task起動、結果集約、report保存、記憶追記、実装、commit、pushを行わない。CursorのTask実行設定は公開schemaとruntime方針に従い、親から渡されたrepo・版・担当観点・暫定案または差分・実体path・要件を欠落なく使う。
