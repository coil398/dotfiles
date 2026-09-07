---
name: tester
description: Cursorで実装済みコードを検証するnative入口。共有testerとtest-procedureを読み、親が検証範囲と結果を確定する。
argument-hint: "[検証対象の説明]"
---

<!-- Cursor native overlay: runtime entry; shared testing rules live in .agents -->

# Tester — Cursor native entry

Cursorの親は、次の共有原本をこのSkillの実体から相対して解決する。

~~~text
SHARED_SKILL_PATH=../../../.agents/skills/tester/SKILL.md
PROCEDURE_PATH=../../../.agents/skills/tester/references/test-procedure.md
RESULT_PATH=../../../.agents/skills/code-review-guidance/references/result-contract.md
~~~

親はSHARED_SKILL_PATHとRESULT_PATHの実在を確認してReadし、共有testerの進行と結果契約を適用する。PROCEDURE_PATHは実在を確認して検証Taskへ絶対pathで渡し、親が直接実行する場合だけ親自身がPROCEDURE_PATHをReadする。TEST_SCOPE、受入条件、実行・静的代替・IaC・データ取扱いを共有手順に従って扱う。親が明示的に許可したlocal/ephemeralのtest outputとlocal fixtureだけを生成でき、対象実装・既存データ・既存fixtureを変更せず、report保存は親が行う。対象repoのcwd、~/.cursor/projects、固定Agent定義からmemoryやpathを推測しない。

CursorのTask起動、model、effort、role、容量は公開schemaと既存runtime方針に従い、TEST_SCOPE・受入条件・許可範囲を欠落なく検証Taskへ渡す。この親入口は必要な検証Taskを起動できる。起動された検証Taskは別の司令塔や親Skillを再委任しない。固定model、固定人数、report保存、記憶追記、実装、commit、pushをこの入口で追加しない。CodexのAgent語彙や固定モデル名を使わない。実行結果・未確認事項・副作用を親へ返す。
