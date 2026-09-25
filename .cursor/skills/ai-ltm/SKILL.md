---
name: "ai-ltm"
description: "セッション開始・再開や過去の失敗・類似問題で長期記憶を自動recallし、確定した学び・意思決定・中断点をrecordする。"
---

<!-- Cursor native overlay: 共有記憶手順と Cursor の非同期入口を接続する。 -->

# ai-ltm — Cursor native entry

Cursor でロードされたら、まず共有原本 [../../../.agents/skills/ai-ltm/SKILL.md](../../../.agents/skills/ai-ltm/SKILL.md) を Read する。別配置で相対 path を解決できない場合は、親が実在確認して渡した共有 Skill の絶対 path を使う。`session_recall.py`、`vector_search.py`、`sync_memory.py`、`init.sql`、`references/setup.md` は共有 package を原本とし、この入口へ複製しない。

## Cursor 固有の実行差分

共有原本の責任、記憶の範囲、writer の権限、結果統合、保存境界をそのまま使う。Cursor が非同期 Task と結果転送を提供するときだけ、親は共有原本の `session_recall.py` を使う bounded recall worker を本命作業と並行して一体起動できる。起動時には共有原本の実体から解決した script/reference path、対象、返却形式、変更禁止を渡し、worker の結果を await して本命を止めない。Task が利用できない場合は recall を起動せず、本命を継続する。

worker は stage event と terminal record を親へ返すだけで、親の workflow を再委任・再起動せず、記憶の保存・embed・同期も行わない。親は terminal record と実際の反映を確認してから、共有原本の writer 境界に従って必要な保存を行う。Task の model/effort は AGENTS の runtime 方針に従い、この入口で固定しない。
