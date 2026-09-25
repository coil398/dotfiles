---
name: "debug"
description: "ログ・再現・コードの実測から不具合の根本原因を特定して修正する。症状、スタックトレース、エラーログがある調査に使う。"
argument-hint: "[症状やエラーメッセージ] [--deepplan]"
---

# Debug — Cursor native entry

ロード済みの本Skillの親の親を`CURSOR_SKILLS_DIR`とし、共有原本 [../../../.agents/skills/debug/SKILL.md](../../../.agents/skills/debug/SKILL.md) を実体から解決してReadする。その診断・修正・review/test手順を実行し、別配置では親が実在確認した共有Skillの絶対pathを使う。

## Cursorでの実行

- 親Cursor agentが症状、再現、根本原因、scope、受入を所有する。小さく密結合した調査・修正は直接行い、分離価値のある探索は`explorer` Taskへ、実装は標準Taskへ渡す。
- Taskのmodelは省略または`inherit`とする。`--deepplan`が明示された場合のFable担当だけ、deepplanが指定するモデル正本に従う。
- 委譲時は対象版、確認済み原因、排他的所有、禁止範囲、成功条件、focused checkと、実行者が読む共有Skill/referenceの実体pathを渡す。子へ親用debug工程を再起動させない。
- run記録が必要な場合だけ `${CURSOR_SKILLS_DIR}/pir2/references/sanitized-cwd.md` をReadする。bucket名は `sanitized_cwd="$(printf '%s' "$PROJECT_ROOT" | sed 's|[^a-zA-Z0-9]|-|g')"` とし、親から検証済みpathを受け取った場合は再計算しない。

reviewer/testerが必要なら同じ親が共有原本から実体pathを解決して手順を実行し、評価・検証担当へ必要な専門referenceだけを渡す。実装担当の自己申告、未起動Task、未生成reportを原因やPASSの根拠にしない。Cursor固有のTask起動と資料配達以外の診断規則は、この入口へ複製しない。
