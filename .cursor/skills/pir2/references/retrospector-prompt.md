# retrospector 実行プロンプト

PIR² 系スキル共通の retrospector 実行仕様。

subagent が利用可能でログ分析を分離したい場合は `retrospector` を起動する。利用できない、または小規模 run の場合はメインエージェント が同じ項目で振り返りを実行する:

- **Cursor Task `model`**: 省略または `inherit` とし、親の Auto と実行中 agent 定義の role に従う。ループ回数で Task slug やモデルを切り替えない。別 runtime 用のモデル名・effort は渡さない
- **Skill root**: `${CURSOR_SKILLS_DIR}` は読み込み済みの本 `SKILL.md` の実体パスから解決する。対象アプリケーション側の固定配置を参照先として仮定しない
- **プロンプト**: 今回実際に使用・記録した値だけ渡す。未使用のカウンタや未生成 artifact は省略し、`0` や架空の path で補わない
  - 実在する `PROJECT_MEMORY_DIR` と `PROJECT_ROOT`
  - `RUN_DIR` は今回の run で作成した実在する directory がある場合だけ
  - `META_MODE=false`（PIR² 系スキルは通常モードで起動する。メタモードは `/retro --meta` で明示起動する）
  - 記録済みの場合だけ `INNER_LOOP_COUNT`
  - 記録済みの場合だけ `OUTER_LOOP_COUNT`
  - 記録済みの場合だけ `EXPLORATION_ROUND`
  - `RUN_DIR` がある場合、計画の方針変更・追加探索の履歴を実在する `{RUN_DIR}/plan.md` から確認する（存在しない path は作業開始条件にしない）
  - `EXPERIMENTAL_PATH=${CURSOR_SKILLS_DIR}/pir2/references/experimental.md`（実在する場合。retrospector は毎回 Read し、該当 run の観測があれば追記・更新する）
  - `OBSERVATION_LOG_PATH`（呼び出し元が指定した観測ログの実在パス・git 管理外。未指定時は新規作成せず、チャットまたは実在するレポートへ要約する。実 run の観測データを記録する場合も `experimental.md` の Observation Log は触らない）
  - `RUN_DIR` 配下に保存された実在する review report のパス一覧があれば渡す（retrospector が必要に応じて Read する）
  - `RUN_DIR` 配下に保存された実在する test report のパス一覧があれば渡す
  - 最終的な VERDICT
  - **ワークフロー種別**: 呼び出し元のスキル名（`pir2` / `pir2async` / `debug` 等。retrospector がレポートで比較・統計できるように記録する）

## 起動後の処理

retrospector のレポートに「メタ改善推奨」項目が含まれていた場合、その旨を最終サマリーに必ず転記してユーザーに通知すること（自動でメタモードは起動せず、ユーザーが `/retro --meta` を実行するかどうかを判断できるようにする）。
