---
name: "deepseek-ops"
description: DeepSeek V4.x Flash を複数 provider（OpenCode Go / NVIDIA Build / DeepInfra）経由で動かすときの失敗型・切り分け・運用の正本。DSML tool-call drift の検出と salvage、quota 層の確認、provider 選定に使う。「DeepSeek が応答しない」「tool call が空」「429 が続く」といった症状で使う。ユーザーが /deepseek-ops と入力したら使う。
---

<!-- Cursor thin entry; the shared skill remains the source of truth. -->
SHARED_SKILL_PATH=../../../.agents/skills/deepseek-ops/SKILL.md

Read the shared skill at `SHARED_SKILL_PATH` relative to this entry file, then follow its instructions.
If relative resolution is unavailable, read the checked-out source at `/home/coil398/dotfiles/.agents/skills/deepseek-ops/SKILL.md`.
The shared skill's references/, scripts/, and other assets remain at that source path and are not copied here.
