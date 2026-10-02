---
name: "wsl-windows"
description: >-
  WSL から Windows のファイル・プロセス・Git・Unity CLI を扱うときの実行規則。
  `/mnt/c` 上の Linux git、WindowsApps の 0-byte スタブ、Editor と CLI の取り違え、
  NTFS 越しのハングを防ぐ。Editor の状態（DEAD / STARTING / READY）ごとの対処、
  unity open / status / command を含む。ユーザーが /wsl-windows と入力したら使う。
---

<!-- Cursor thin entry; the shared skill remains the source of truth. -->
SHARED_SKILL_PATH=../../../.agents/skills/wsl-windows/SKILL.md

Read the shared skill at `SHARED_SKILL_PATH` relative to this entry file, then follow its instructions.
If relative resolution is unavailable, read the checked-out source at `/home/coil398/dotfiles/.agents/skills/wsl-windows/SKILL.md`.
The shared skill's references/, scripts/, and other assets remain at that source path and are not copied here.
