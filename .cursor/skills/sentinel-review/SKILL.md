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
~~~

上記の実在するファイルをReadし、IaC対象の確定、sentinel-iac Taskへのschema path渡し、JSON parse失敗・schema違反・未確認の記録、severity-minとMarkdown集約を共有手順に従って行う。対象repoのcwdや固定Agent定義から契約資料を推測しない。

CursorのTask起動、model、role、容量は既存runtime方針に従う。この親入口は必要なsentinel-iac検査Taskを起動できる。Taskのmodelは省略するかinheritとし、起動された検査Taskは別の司令塔や親Skillを再委任しない。この入口と検査者はread-onlyで、apply、deploy、外部ネットワーク、workflow実行、修正、commit、push、report保存を行わない。壊れた応答をFinding 0件の成功にせず、未確認として返す。
