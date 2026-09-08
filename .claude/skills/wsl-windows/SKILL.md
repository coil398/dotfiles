---
name: wsl-windows
description: >-
  WSL から Windows のファイル・プロセス・Git・Unity CLI を扱うときの実行規則。
  `/mnt/c` 上の Linux git、WindowsApps の 0-byte スタブ、Editor と CLI の取り違え、
  NTFS 越しのハングを防ぐ。Editor の状態（DEAD / STARTING / READY）ごとの対処、
  unity open / status / command を含む。ユーザーが /wsl-windows と入力したら使う。
---

# wsl-windows — Claude entry

同じdotfiles checkoutの共有原本 `.agents/skills/wsl-windows/SKILL.md` を読み、そのホスト層の禁則と Unity CLI の手順（状態ごとの対処を含む）を実行する。ロード済み入口の実体からcheckoutを確定し、別配置では親が実在確認した共有原本の絶対pathを使う。

手順の複製はしない。Git の同期工程（保全・競合・push）は `git-sync`、dotfiles 本体の同期は `dotfiles-autosync`。
