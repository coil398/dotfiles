---
name: reviewer
description: Cursorでレビュー親を実行するnative入口。共有reviewer Skillを読み、対象・担当配分・結果集約を親が行う。
---

<!-- Cursor native overlay: runtime entry; shared review rules live in .agents -->

# Reviewer — Cursor native entry

Cursorの親は、このSkillの実体ディレクトリから次の共有原本を相対して解決する。

~~~text
SHARED_SKILL_PATH=../../../.agents/skills/reviewer/SKILL.md
GUIDANCE_PATH=../../../.agents/skills/code-review-guidance/SKILL.md
RESULT_PATH=../../../.agents/skills/code-review-guidance/references/result-contract.md
~~~

親はSHARED_SKILL_PATHとRESULT_PATHの実在を確認してReadし、共有reviewer手順と結果契約を適用する。GUIDANCE_PATHは実在を確認して評価Taskへ絶対pathで渡し、親が直接評価する場合だけ親自身がGUIDANCE_PATHと対応referenceをReadする。対象repoのcwd、~/.cursor/projects、固定Agent定義からSkillや資料を推測しない。評価者へは親が確認したGUIDANCE_PATH、RESULT_PATHの絶対pathと担当roleを渡す。

CursorのTask起動、model、effort、role、容量は公開schemaと既存runtime方針に従い、必要な評価Taskへ親の入力を欠落なく渡す。この親入口は必要な評価Taskを起動できる。起動された評価Taskは別の司令塔や親Skillを再委任しない。固定model、固定人数、report保存、記憶追記、実装、commit、pushをこの入口で追加しない。CodexのAgent語彙や固定モデル名を使わない。
