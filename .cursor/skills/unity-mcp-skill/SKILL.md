---
name: "unity-mcp-skill"
description: "Orchestrate the Unity Editor through MCP (Model Context Protocol) tools and resources for Unity projects: create or modify GameObjects, edit scripts, manage scenes, run tests, and automate the Unity Editor. Natural-language trigger examples: 1) “Create or modify GameObjects”; 2) “Edit a Unity script”; 3) “Manage a Unity scene”; 4) “Run Unity tests”; 5) “Automate the Unity Editor”. Use this skill implicitly whenever the request matches these Unity-MCP tasks, even without naming the skill. If the user enters /unity-mcp-skill, always use it. Provides best practices, tool schemas, and workflow patterns for effective Unity-MCP integration."
---

<!-- Cursor native overlay: Cursor の入口と共有 Unity 専門資料への接続だけを定義する。 -->

# unity-mcp-skill — Cursor native entry

Cursor でロードされたら、まず共有原本 [../../../.agents/skills/unity-mcp-skill/SKILL.md](../../../.agents/skills/unity-mcp-skill/SKILL.md) を Read する。別配置で相対 path を解決できない場合は、親が実在確認して渡した共有 Skill の絶対 path を使う。`references/tools-reference.md`、`references/workflows.md` と指定 project の資料は共有/対象 project を原本とし、この入口へ複製しない。

親は Cursor で実際に利用できる Unity MCP resource/tool、対象 instance、操作、承認、受入を確定する。委任時は親が確認した専門 reference の物理 path、project evidence、対象、所有範囲、変更禁止または明示 writer 範囲、返却形式を渡し、担当自身に Read させる。read-only 担当は観測だけを返し、親の Unity 操作工程を再起動しない。Task の model/effort は AGENTS の runtime 方針に従い、この入口で固定しない。
