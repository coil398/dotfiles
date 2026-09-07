---
name: refactor-advisor
description: Cursorで任意のリファクタリング改善案を返すnative入口。共有refactor-advisorとrefactor-guidanceを読み、reviewerのVERDICTから分離する。
argument-hint: "[対象範囲の指定]"
---

<!-- Cursor native overlay: runtime entry; shared review rules live in .agents -->

# Refactor Advisor — Cursor native entry

Cursorの親は、次の共有原本をこのSkillの実体から相対して解決する。

~~~text
SHARED_SKILL_PATH=../../../.agents/skills/refactor-advisor/SKILL.md
GUIDANCE_PATH=../../../.agents/skills/refactor-advisor/references/refactor-guidance.md
~~~

上記の実在するファイルをReadし、対象diff・既存先例・3箇所以上の重複・標準/既存helper・言語イディオム・非阻害の提案境界を共有手順に従って扱う。対象repoのcwd、~/.cursor/projects、固定Agent定義から資料やpathを推測しない。

CursorのTask起動、model、role、容量は既存runtime方針に従う。この親入口は必要な一体のrefactor評価Taskを起動できる。Taskのmodelは省略するかinheritとし、起動された評価Taskは別の司令塔や親Skillを再委任しない。固定model、固定人数、ユーザーゲート、report保存、記憶追記、実装、commit、pushをこの入口で追加しない。CodexのAgent語彙や固定モデル名を使わない。PROPOSALSのみを返し、VERDICTや完了阻害判定を作らない。適用後の影響観点の再確認は親が行う。
