---
name: "python-toolchain"
description: "Python のスクリプト作成・依存管理・環境構築を行うときに使う。uv 優先の実行方法、PEP 723 インライン依存、uv add / uv run --with の使い分けを定める。"
---

<!-- Cursor native overlay: Cursor の入口と共有原本の解決だけを定義する。 -->

# python-toolchain — Cursor native entry

Cursor でロードされたら、まず共有原本 [../../../.agents/skills/python-toolchain/SKILL.md](../../../.agents/skills/python-toolchain/SKILL.md) を Read する。別配置で相対 path を解決できない場合は、親が実在確認して渡した共有 Skill の絶対 path を使う。ツール選択とコマンド規約は共有 package を原本とし、この入口へ複製しない。

Task の model/effort は AGENTS の runtime 方針に従い、この入口で固定しない。
