---
name: "pir2"
description: "複雑な実装・設計変更をPlan → Implement → Review → Test → Retrospectで進める。影響範囲や設計判断が重い作業に使う。"
argument-hint: "[タスクの説明] [--deepplan]"
---

# PIR² — Cursor native entry

ロード済みの本Skillの実体から共有原本 [../../../.agents/skills/pir2/SKILL.md](../../../.agents/skills/pir2/SKILL.md) を解決してReadし、その計画・実装・review/test・振り返り・完了条件を使う。別配置では親が実在確認した共有Skillの絶対pathを使う。親Cursor agentが探索統合、計画、scope、所有、ユーザー判断、受入、最終判断を保持する。

## Cursorでの実行

- `CURSOR_SKILLS_DIR`はロード済みの本Skillの親の親、共有資料はそこから解決した `.agents/skills` の実体を使う。対象repoや未確認のHOMEからSkill pathを推測しない。
- Taskのmodelは省略または`inherit`とする。`--deepplan`が明示された場合だけnative deepplanを使い、独立した熟考・統合・十分性確認TaskにはdeepthinkのFableモデル正本を適用する。
- 小さく密結合した確認・変更は親が直接行える。独立した探索は`explorer` Taskへ、排他的所有を持つ実装と必要なreview/testだけ標準Taskへ渡し、子へ親用PIR²工程や別の制御Taskを起動させない。
- 委譲時は対象版、目的、確認済み事実、排他的所有、禁止範囲、依存、完了条件、focused checkと、実行者が読む共有Skill/referenceの実体pathを渡す。共有契約・schema・lockfile・生成物・同一ファイルを複数writerへ同時に渡さない。

後続担当または再開に記録が必要な場合だけ [sanitized-cwd.md](references/sanitized-cwd.md) をReadして専有run directoryを予約する。bucket名は `sanitized_cwd="$(printf '%s' "$PROJECT_ROOT" | sed 's|[^a-zA-Z0-9]|-|g')"` とし、親から検証済みpathを受け取った場合は再計算しない。短いrunにplan、handoff、report、台帳を要求しない。

実装を委譲する場合は共有原本と同じpackageの [implementation-delegation.md](../../../.agents/skills/pir2/references/implementation-delegation.md) をReadし、実装Taskは標準Task `Task(subagent_type="generalPurpose")` で `model` を省略して起動する。破壊的影響、ユーザー判断、review/test、振り返りは共有原本の条件と実体pathに従い、この入口へ工程を複製しない。親はstatus、diff、実在する成果物と確認結果から受入を決め、未生成report、未起動Task、自己申告を成功条件にしない。
