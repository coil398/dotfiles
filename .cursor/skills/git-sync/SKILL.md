---
name: git-sync
description: >-
  「git sync」「同期して」「pullしてpush」で、対象リポジトリの変更保全・差分統合・関連配備更新・pushまで実行する。
  通常の競合や配備不一致は親が解消して継続する。ユーザーが /git-sync と入力したら使う。
argument-hint: "[リポジトリルート。省略時は cwd]"
---

<!-- Cursor native overlay: Cursor の入口と共有同期手順への接続だけを定義する。 -->

# git-sync — Cursor native entry

Cursor でロードされたら、まず共有原本 [../../../.agents/skills/git-sync/SKILL.md](../../../.agents/skills/git-sync/SKILL.md) を Read する。別配置で相対 path を解決できない場合は、親が実在確認して渡した共有 Skill の絶対 path を使う。対象確定、preflight、競合、承認、報告の手順は共有 package を原本とし、この入口へ複製しない。

親は Cursor の構造化された対象 path と利用可能な Git 操作で同期を実行し、対象、upstream、commit/push の実行と結果統合を持つ。read-only 確認を Task に渡す場合は、親が確認した対象版・必要資料の物理 path・変更禁止・返却形式を渡し、担当自身に Read させる。担当は観測だけを返し、commit・push・report 保存・記憶追記を行わず、親の同期工程を再起動しない。Task の model/effort は AGENTS の runtime 方針に従い、この入口で固定しない。

同期依頼には通常のWIP保全・競合統合・関連するホーム配備更新・commit/pushを含む。共有原本の復旧手順を適用し、これらの工程ごとに再承認させない。
