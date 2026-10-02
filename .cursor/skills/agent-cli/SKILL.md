---
name: "agent-cli"
description: >-
  ある AI エージェントから別の AI CLI（devin / codex / claude / cursor-agent /
  opencode / gemini / grok）を非対話で呼び出すときの実行規則。print モードの
  選び方、認証・権限・cwd の罠、出力フォーマット、ACP 起動の注意をまとめる。
  「codex に投げて」「devin を CLI から呼んで」「別エージェントに委譲」
  といった依頼で使う。ユーザーが /agent-cli と入力したら使う。
---

<!-- Cursor thin entry; the shared skill remains the source of truth. -->
SHARED_SKILL_PATH=../../../.agents/skills/agent-cli/SKILL.md

Read the shared skill at `SHARED_SKILL_PATH` relative to this entry file, then follow its instructions.
If relative resolution is unavailable, read the checked-out source at `/home/coil398/dotfiles/.agents/skills/agent-cli/SKILL.md`.
The shared skill's references/, scripts/, and other assets remain at that source path and are not copied here.
