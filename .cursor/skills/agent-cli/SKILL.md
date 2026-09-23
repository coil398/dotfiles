---
name: "agent-cli"
description: "ある AI エージェントから別の AI CLI（devin / codex / claude / cursor-agent / opencode / gemini）を非対話で呼び出すときの実行規則。print モード、認証・権限・cwd の罠、出力フォーマット、ACP 起動の注意。"
argument-hint: "[呼び出すCLIや委譲内容]"
---

# agent-cli — Cursor native entry

ロード済みの本Skillの親の親を`CURSOR_SKILLS_DIR`とし、共有原本 [../../../.agents/skills/agent-cli/SKILL.md](../../../.agents/skills/agent-cli/SKILL.md) を実体から解決してReadする。その実行規則に従う。別配置では親が実在確認した共有Skillの絶対pathを使う。

## Cursorでの実行

- 共有原本のCLI別手順をそのまま使う。Cursor自身を別エージェントから呼ぶ場合は `cursor-agent` の節が対象
- 委譲プロンプトは自己完結にする（目的・対象path・完了条件）。子は親の会話文脈を見ない
