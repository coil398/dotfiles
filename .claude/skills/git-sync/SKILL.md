---
name: git-sync
description: >-
  「git sync」「同期して」「pullしてpush」で、対象リポジトリの変更保全・差分統合・関連配備更新・pushまで実行する。
  通常の競合や配備不一致は親が解消して継続する。ユーザーが /git-sync と入力したら使う。
argument-hint: "[リポジトリルート。省略時は cwd]"
---

# git-sync — Claude entry

同じdotfiles checkoutの共有原本 `.agents/skills/git-sync/SKILL.md` を読み、その同期・復旧・完了手順を実行する。ロード済み入口の実体からcheckoutを確定し、別配置では親が実在確認した共有原本の絶対pathを使う。

同期依頼には通常のWIP保全、競合統合、関連生成物・ホーム配備更新、検証、commit・pushを含む。親が復旧と統合を持ち、これらを工程ごとに再承認させない。実アクセス制御と変更保全は共有原本の手順に従う。
