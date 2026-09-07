---
name: review-pr
description: CursorでPR・remote branchをレビューするnative入口。共有review-prとreviewerを読み、repo・base・head・担当・結果を親が確定する。
argument-hint: "[PR番号、ブランチ名、またはファイルパス]"
---

<!-- Cursor native overlay: runtime entry; shared review rules live in .agents -->

# Review PR — Cursor native entry

Cursorの親は、次の共有原本をこのSkillの実体から相対して解決する。

~~~text
SHARED_SKILL_PATH=../../../.agents/skills/review-pr/SKILL.md
REVIEWER_PATH=../../../.agents/skills/reviewer/SKILL.md
GUIDANCE_PATH=../../../.agents/skills/code-review-guidance/SKILL.md
RESULT_PATH=../../../.agents/skills/code-review-guidance/references/result-contract.md
~~~

親はSHARED_SKILL_PATH、REVIEWER_PATH、RESULT_PATHの実在を確認してReadし、共有review-prでPRのbase/head、repo/ref、staged・unstaged・untrackedの境界を確定する。GUIDANCE_PATHは実在を確認して評価Taskへ絶対pathで渡し、親が直接評価する場合だけ親自身がGUIDANCE_PATHと対応referenceをReadする。観点配分とCOVERAGE/VERDICT集約は共有`reviewer`手順に任せる。対象repoのcwd、~/.cursor/projects、固定Agent定義から資料やpathを推測しない。評価者へは親が確認したGUIDANCE_PATH、RESULT_PATHの絶対pathと対応referenceを渡す。

CursorのTask起動、model、effort、role、容量は公開schemaと既存runtime方針に従い、確定したPR入力を`reviewer`へ欠落なく渡す。この親入口は必要なreviewer Taskを起動できる。起動された評価Taskは別の司令塔や親Skillを再委任しない。固定model、固定人数、report保存、記憶追記、PRへの外部投稿、実装、commit、pushをこの入口で追加しない。`reviewer`から返る結果を改変せず引き渡す。
