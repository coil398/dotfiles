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
~~~

上記の実在するファイルをReadし、PRのbase/head、repo/ref、staged・unstaged・untrackedの境界、観点配分、COVERAGE/VERDICT集約を共有手順に従って行う。対象repoのcwd、~/.cursor/projects、固定Agent定義から資料やpathを推測しない。評価者へは親が確認したGUIDANCE_PATHの絶対pathと対応referenceを渡す。

CursorのTask起動、model、role、容量は既存runtime方針に従う。この親入口は必要な評価Taskを起動できる。Taskのmodelは省略するかinheritとし、起動された評価Taskは別の司令塔や親Skillを再委任しない。固定model、固定人数、report保存、記憶追記、PRへの外部投稿、実装、commit、pushをこの入口で追加しない。未起動担当・未生成report・未確認範囲を成功として補完しない。
