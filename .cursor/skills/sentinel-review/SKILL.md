---
name: sentinel-review
description: CursorでIaCをread-only検査するnative入口。共有sentinel-reviewとFinding schema/redactionを読み、結果を親が正規化する。
---

<!-- Cursor native overlay: runtime entry; shared review rules live in .agents -->

# Sentinel review — Cursor native entry

Cursorの親は、次の共有原本をこのSkillの実体から相対して解決する。

~~~text
SHARED_SKILL_PATH=../../../.agents/skills/sentinel-review/SKILL.md
SCHEMA_PATH=../../../.agents/skills/sentinel-review/references/findings-schema.md
REDACTION_PATH=../../../.agents/skills/sentinel-review/references/redaction.md
RESULT_PATH=../../../.agents/skills/code-review-guidance/references/result-contract.md
~~~

親はSHARED_SKILL_PATHとRESULT_PATHをReadし、共有手順が指定する入出力・集約用の資料も読む。SCHEMA_PATHとREDACTION_PATHは実在を確認して評価Taskへ絶対pathで渡し、検出の専門本文は実際の評価者が読む。親が直接評価する場合は親自身が評価資料を読む。対象repoのcwdや固定Agent定義から契約資料を推測しない。

CursorのTask起動、model、effort、role、容量は公開schemaと既存runtime方針に従い、対象IaCの相対path一覧とschema/redaction pathを欠落なくsentinel-iac Taskへ渡す。この親入口は必要なsentinel-iac検査Taskを起動できる。起動された検査Taskは別の司令塔や親Skillを再委任しない。この入口と検査者は書き込みを実行せず、apply、deploy、外部ネットワーク、workflow実行、修正、commit、push、report保存を行わない。壊れた応答は共有手順の未確認として扱う。
