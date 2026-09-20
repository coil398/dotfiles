---
name: "pir2async"
description: "Cursorで`/pir2async`を通常のPIR² Taskワークフローへ接続する互換入口。専用team APIがない場合の実行差だけを扱う。"
argument-hint: "[タスクの説明] [--deepplan]"
---

# PIR² Async — Cursor

ロード済みの本Skillから `../pir2/SKILL.md` の実体を解決して全文Readし、同じ引数で実行する。PIR²がrun記録を選んだ場合のbucket名は `sanitized_cwd="$(printf '%s' "$PROJECT_ROOT" | sed 's|[^a-zA-Z0-9]|-|g')"` とし、親から検証済みpathを受け取った場合は再計算しない。Cursorに専用team lifecycleがない場合は、PIR²が選んだ独立単位を通常のTaskで並列化し、依存単位を直列化する。

親Cursor agentが計画、所有、起動、ユーザー判断、review/test、統合、受入を保持する。Taskのmodelは省略または`inherit`とし、`--deepplan`のFable担当だけPIR²から接続したモデル正本に従う。専用teamの状態、通信、成果物を捏造せず、縮退を理由に安全・権限・検証境界を弱めない。
