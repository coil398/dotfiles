# retrospector 実行プロンプト

PIR² 系スキル共通の retrospector 実行仕様。

subagent が利用可能でログ分析を分離したい場合は `retrospector` を起動する。利用できない、または小規模 run の場合はメインエージェント が同じ項目で振り返りを実行する:

- **Task `model`**: 省略または `inherit`。agent overlay は `role=coding`（ループ回数で Task slug を切り替えない）
- **プロンプト**: 以下の情報をすべて渡す
  - `PROJECT_MEMORY_DIR`
  - `PROJECT_ROOT`
  - `RUN_DIR`
  - `META_MODE=false`（PIR² 系スキルは常に通常モードで起動する。メタモードは `/retro --meta` で明示起動する）
  - `INNER_LOOP_COUNT`
  - `OUTER_LOOP_COUNT`
  - `EXPLORATION_ROUND`
  - 計画の方針変更・追加探索の履歴は `{RUN_DIR}/plan.md` の更新履歴から確認する
  - `EXPERIMENTAL_PATH=.cursor/skills/pir2/references/experimental.md`（存在する場合。retrospector は毎回 Read し、該当 run の観測があれば追記・更新する）
  - `OBSERVATION_LOG_PATH=~/.claude/memory/experimental_observations.md`（観測ログの記録先・git 管理外。実 run の観測データはここに記録し、`experimental.md` の Observation Log は触らない）
  - `{RUN_DIR}/review-*.md` のパス一覧（retrospector が必要に応じて Read する）
  - `{RUN_DIR}/test-*.md` のパス一覧
  - 最終的な VERDICT
  - **ワークフロー種別**: 呼び出し元のスキル名（`pir2` / `pir2async` / `debug` 等。retrospector がレポートで比較・統計できるように記録する）

## 起動後の処理

retrospector のレポートに「メタ改善推奨」項目が含まれていた場合、その旨を最終サマリーに必ず転記してユーザーに通知すること（自動でメタモードは起動せず、ユーザーが `/retro --meta` を実行するかどうかを判断できるようにする）。
