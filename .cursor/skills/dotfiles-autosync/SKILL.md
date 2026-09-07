---
name: "dotfiles-autosync"
description: "dotfiles本体を、ユーザーの明示依頼に限って中央 engine で保全commit、no-rebase merge、adapter再生成、submodule整合、pushまで同期する。自然言語トリガー例: 「dotfilesを同期して」／「dotfilesの変更を保全して」／「adapterを再生成して同期して」／「dotfilesをpushして」。スキル・プラグインの更新確認は別の check-updates の責務であり、このスキルはdotfiles本体だけを扱う。ユーザーが /dotfiles-autosync と入力したら使う。"
argument-hint: "[dotfiles の Git top-level]"
---

<!-- Cursor native overlay: Cursor の入口から共有 engine へ接続する。 -->

# dotfiles-autosync — Cursor native entry

Cursor でロードされたら、まず共有原本 [../../../.agents/skills/dotfiles-autosync/SKILL.md](../../../.agents/skills/dotfiles-autosync/SKILL.md) を Read する。別配置で相対 path を解決できない場合は、親が実在確認して渡した共有 Skill の絶対 path を使う。`etc/dotfiles-autosync.sh` は共有原本がロードされた checkout から解決し、この入口へ同期手順を複製しない。

Cursor の親が対象 root、既存 upstream、commit/merge/generator/push の承認、結果統合を持つ。engine を起動する場合は共有原本の実体から解決した engine path と明示 root を使い、Task の model/effort は AGENTS の runtime 方針に従ってこの入口では固定しない。read-only 担当を使う場合も、親が確認した path と返却形式を渡し、子に親の同期工程を再起動させない。
