---
name: "ir"
description: "明確で小さい変更をImplement → Reviewで進める。別の計画artifactや振り返りが不要な修正・小機能・設定・文書変更に使う。"
argument-hint: "[タスクの説明]"
---

# IR — Cursor native entry

ロード済みの本Skillの親の親を`CURSOR_SKILLS_DIR`とし、共有原本 [../../../.agents/skills/ir/SKILL.md](../../../.agents/skills/ir/SKILL.md) を実体から解決してReadする。その実装・受入・review/test手順を使い、別配置では親が実在確認した共有Skillの絶対pathを使う。

親Cursor agentがscope、所有、受入、結果統合を持つ。小さく密結合した変更は直接実装でき、分離価値がある場合だけ実装担当の標準Taskへ、目的、確認済み事実、排他的所有、禁止範囲、完了条件、focused checkを渡す。Taskのmodelは省略または`inherit`とし、子へ親用IR工程や別Taskを再起動させない。

記録が後続作業に必要な場合だけ、ロード済みSkillから解決した `${CURSOR_SKILLS_DIR}/pir2/references/sanitized-cwd.md` をReadする。bucket名は `sanitized_cwd="$(printf '%s' "$PROJECT_ROOT" | sed 's|[^a-zA-Z0-9]|-|g')"` とし、検証済みpathを受け取った場合は再計算しない。通常はplan、handoff、run directoryを作らない。

reviewer/testerが必要なら同じ親が共有原本から実体pathを解決して手順を実行し、評価・検証担当へ必要な専門referenceだけを渡す。未生成report、未起動Task、実装担当の自己申告を受入根拠にしない。
