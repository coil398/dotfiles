# retrospector 実行プロンプト

PIR² 系スキル共通の retrospector 実行仕様。

subagent が利用可能でログ分析を分離したい場合は `spawn_agent` に `agent_type="retrospector"` を渡して `retrospector` role を起動する。モデル引数は指定せず、`${PROJECT_ROOT}/.codex/agents/retrospector.toml` の role 定義に委ねる。利用できない、または小規模 run の場合はメイン Codex が同じ項目で振り返りを実行する:

- **モデル指定**: `INNER_LOOP_COUNT` / `OUTER_LOOP_COUNT` の値にかかわらず、呼び出し側では指定しない。`.codex/agents/retrospector.toml` の role 定義に委ねる
- **プロンプト**: 以下の情報をすべて渡す
  - `PROJECT_MEMORY_DIR`
  - `PROJECT_ROOT`
  - `RUN_DIR`
  - `META_MODE=false`（PIR² 系スキルは常に通常モードで起動する。メタモードは `/retro --meta` で明示起動する）
  - `INNER_LOOP_COUNT`
  - `OUTER_LOOP_COUNT`
  - `REPLAN_COUNT`
  - `PLAN_STRATEGY_CHANGED`（true なら今回 run でユーザー方針切替が発生し planner v1→v2 再策定が走った。`/pir2` で使用。`/pir2async` 等で該当機構を持たない場合は `false` 固定でよい）
  - `EXPERIMENTAL_PATH=${PROJECT_ROOT}/.codex/skills/pir2/references/experimental.md`（存在する場合。retrospector は毎回 Read し、該当 run の観測があれば追記・更新する）
  - `WORKER_OBSERVABILITY_SCHEMA_PATH=${PROJECT_ROOT}/.codex/skills/pir2/references/worker-observability.md`（共通 actor 観測の schema/enum/集計方法の SSOT。毎回 Read する）
  - `OBSERVATION_LOG_PATH=~/.codex/memory/experimental_observations.md`（観測ログの記録先・git 管理外。実 run の観測データはここに記録し、`experimental.md` の Observation Log は触らない）
  - `{RUN_DIR}/worker-observations-v1.tsv`（actor attempt の SSOT。存在する場合は全行を Read する）
  - `{RUN_DIR}/sol-acceptance-v1.tsv`（requirement 別の Sol 実測。worker report/exit code と混同しない）
  - `{RUN_DIR}/independent-verdicts-v1.tsv`（reviewer/tester の独立 verdict。Sol acceptance と別集計する）
  - `{RUN_DIR}/review-*.md` のパス一覧（retrospector が必要に応じて Read する）
  - `{RUN_DIR}/test-*.md` のパス一覧
  - 最終的な VERDICT
  - **ワークフロー種別**: 呼び出し元のスキル名（`pir2` / `pir2async` / `debug` 等。retrospector がレポートで比較・統計できるように記録する）

worker observability の扱い:

- actor attempt 数、actor、実モデル、時間、result、昇格、mismatch は `worker-observations-v1.tsv` から集計する。worker の完了報告や runner exit code を acceptance PASS として推論しない。
- `sol-acceptance-v1.tsv` の各 `Rn` の `verdict` と `evidence_*` を Sol acceptance の観測結果として扱う。`independent-verdicts-v1.tsv` の reviewer/tester verdict は別フィールド・別集計で扱う。
- TSV は append-only の run 記録なので、retrospector は schema、actor 行、acceptance 行、independent verdict を編集・再作成しない。必要な experiment-level 集計だけを `OBSERVATION_LOG_PATH` と `experimental.md` の既存責務に従って追記する。

## 起動後の処理

retrospector のレポートに「メタ改善推奨」項目が含まれていた場合、その旨を最終サマリーに必ず転記してユーザーに通知すること（自動でメタモードは起動せず、ユーザーが `/retro --meta` を実行するかどうかを判断できるようにする）。
