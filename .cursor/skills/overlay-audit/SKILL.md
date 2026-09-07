---
name: "overlay-audit"
description: >-
  指定した起動ディレクトリと、親が確定した dotfiles root のスキル配置・エージェント定義を点検する。
  判定の正は etc/audit-skill-agent-layout.py。実効 runtime の native 優先順、Cursor の name、
  agent の model/role、生成物の状態を報告する。「overlay 点検」「スキル配置」
  「エージェント定義は共通か」「layout audit」「/overlay-audit」で使う。
argument-hint: "[起動ディレクトリ]"
---

<!-- Cursor native overlay: Cursor の root 入力と共有判定 engine への接続だけを定義する。 -->

# overlay-audit — Cursor native entry

Cursor でロードされたら、まず共有原本 [../../../.agents/skills/overlay-audit/SKILL.md](../../../.agents/skills/overlay-audit/SKILL.md) を Read する。別配置で相対 path を解決できない場合は、親が実在確認して渡した共有 Skill の絶対 path を使う。判定規則は共有原本と `etc/audit-skill-agent-layout.py` を正とし、この入口へ複製しない。

親は runtime が確定した起動ディレクトリ、実在確認した dotfiles root、engine の実体 path、監査範囲を渡して直接実行する。Task に read-only 確認を委任する場合は同じ入力と返却形式を渡し、担当自身に必要な資料を Read させる。担当は engine の実測結果だけを返し、配置・生成物・report・記憶を変更せず、親の監査工程を再起動しない。Task の model/effort は AGENTS の runtime 方針に従い、この入口で固定しない。
