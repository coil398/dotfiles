---
name: "dotfiles-autosync"
description: "dotfiles 専用の保全 commit、no-rebase merge、adapter 再生成、submodule 整合、push を中央 engine で実行する。"
argument-hint: "[dotfiles の Git top-level]"
---

# dotfiles-autosync — Claude entry

同じdotfiles checkoutの共有原本 `.agents/skills/dotfiles-autosync/SKILL.md` を読み、その同期・復旧・完了手順を実行する。ロード済み入口の実体からcheckoutを確定し、別配置では親が実在確認した共有原本の絶対pathを使う。

同期依頼には通常のWIP保全、競合統合、関連生成物・ホーム配備更新、検証、commit・pushを含む。親が復旧と統合を持ち、これらを工程ごとに再承認させない。実アクセス制御と変更保全は共有原本の手順に従う。
