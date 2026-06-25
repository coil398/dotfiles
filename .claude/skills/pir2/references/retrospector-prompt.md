# retrospector 起動プロンプト

PIR² 系スキル共通の retrospector 起動仕様。

`retrospector` エージェントを `Agent` ツールで起動する:

- **model**: `INNER_LOOP_COUNT が 0 かつ OUTER_LOOP_COUNT が 0 の場合は sonnet`、いずれかが 1 以上の場合は `opus`
- **プロンプト**: 以下の情報をすべて渡す
  - `PROJECT_MEMORY_DIR`
  - `PROJECT_ROOT`
  - `RUN_DIR`
  - `META_MODE=false`（PIR² 系スキルは常に通常モードで起動する。メタモードは `/retro --meta` で明示起動する）
  - `INNER_LOOP_COUNT`
  - `OUTER_LOOP_COUNT`
  - `REPLAN_COUNT`
  - `PLAN_STRATEGY_CHANGED`（true なら今回 run でユーザー方針切替が発生し planner v1→v2 再策定が走った。`/pir2` で使用。`/pir2async` 等で該当機構を持たない場合は `false` 固定でよい）
  - `EXPERIMENTAL_PATH=~/.claude/skills/pir2/references/experimental.md`（存在する場合。retrospector は毎回 Read し、該当 run の観測があれば追記・更新する）
  - `OBSERVATION_LOG_PATH=~/.claude/memory/experimental_observations.md`（観測ログの記録先・git 管理外。実 run の観測データはここに記録し、`experimental.md` の Observation Log は触らない）
  - `{RUN_DIR}/review-*.md` のパス一覧（retrospector が必要に応じて Read する）
  - `{RUN_DIR}/test-*.md` のパス一覧
  - 最終的な VERDICT
  - **ワークフロー種別**: 呼び出し元のスキル名（`pir2` / `pir2async` / `debug` 等。retrospector がレポートで比較・統計できるように記録する）

## 起動後の処理

retrospector のレポートに「メタ改善推奨」項目が含まれていた場合、その旨を最終サマリーに必ず転記してユーザーに通知すること（自動でメタモードは起動せず、ユーザーが `/retro --meta` を実行するかどうかを判断できるようにする）。
