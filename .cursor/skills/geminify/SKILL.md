---
name: geminify
description: "読みにくい日本語を Gemini 4 Hydrogen（agy 経由）で読みやすくし、書き直しが原文を誤解していないか照合する。/geminify、geminify、日本語が読みにくい、で使う。"
argument-hint: "[読みにくい日本語。空なら直前の出力]"
disable-model-invocation: true
---

<!-- Cursor native overlay: Cursor の入口と共有手順への接続だけを定義する。 -->

# Geminify：Cursor native entry

Cursor でロードされたら、まず共有原本 [../../../.agents/skills/geminify/SKILL.md](../../../.agents/skills/geminify/SKILL.md) を Read する。別配置で相対 path を解決できない場合は、親が実在確認して渡した共有 Skill の絶対 path を使う。対象の決め方、秘密情報の扱い、書き直し・照合・直しの手順は共有 package を原本とし、この入口へ複製しない。

対象文は `$ARGUMENTS` が本文ならそれを使う。空、または「直前を直して」だけの指定なら、直前のアシスタント出力を使う。同じターンに質問がある場合は、答えの草稿を内部で作り、その草稿を対象文にする。会話全体は送らない。モデルへの問い合わせは共有スクリプトが agy 経由で行う。スクリプトの標準出力を、前置きなしでそのまま返す。
