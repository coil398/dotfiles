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
~~~

上記の実在するファイルをReadし、その手順、references、COVERAGE/VERDICT契約を適用する。対象repoのcwd、~/.cursor/projects、固定Agent定義からSkillや資料を推測しない。評価者へは親が確認したGUIDANCE_PATHの絶対pathと担当roleを渡す。

CursorのTask起動、model、role、容量は既存runtime方針に従う。この親入口は必要な評価Taskを起動できる。Taskのmodelは省略するかinheritとし、起動された評価Taskは別の司令塔や親Skillを再委任しない。固定model、固定人数、report保存、記憶追記、実装、commit、pushをこの入口で追加しない。CodexのAgent語彙や固定モデル名を使わない。未確認をPASSへ変換せず、変更後は影響を受けた観点だけを親が再評価する。
