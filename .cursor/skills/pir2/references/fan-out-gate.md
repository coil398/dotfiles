# Fan-Out Gate（reviewer 並列レビュー）

PIR² 系スキル（/pir2 等）の reviewer 並列レビュー仕様。subagent が利用可能な場合は同一ターンで reviewer を並列起動し、利用できない場合はメインエージェント が同一レビューサイクル内で全観点を実行する。SKILL.md 側で 7-2A 宣言テンプレートを発火させた後の実行本体・違反検知・リカバリ・起動パラメータをここに集約する。

## 観点マッピング（reviewer.toml の SSOT に従う）

`REVIEWER_ROLE` ごとの担当観点。詳細は `~/.cursor/agents/reviewer.toml` の `developer_instructions` に含まれる「呼び出し元（スキル本体）への運用ガイド」を参照する:

- `correctness`: バグ・正確性 / パフォーマンス / リグレッション
- `consistency`: 命名規則・構造一貫性 / 同一ロジック全適用網羅性 / 類似ファイル群波及網羅性
- `quality`: 保守性（局所スコープ）/ テストの質 / データアクセス重複 / スコープ逸脱
- `security`: セキュリティ（OWASP）/ 認可・認証 / シークレット漏洩 / 依存脆弱性
- `architecture`: レイヤリング / 循環依存 / 責務逸脱 / 抽象粒度

## 違反パターンと検出

次のいずれかが発生したら違反として検出し、Fan-Out Gate 宣言（SKILL.md の 7-2A）からやり直す:

- subagent 起動が 2 ターン以上に分かれる
- subagent 利用時に起動数が宣言した N より少ない
- subagent 非利用時に review ファイル数が宣言した N より少ない
- 観点を独自判断で減らした
- 直前ターンの宣言テンプレートが省略された

## 違反検出時のリカバリ

1. 不完全に起動された subagent があれば完了を待ってから結果を破棄する
2. Fan-Out Gate の宣言テンプレートを正しく書き直す
3. 並列レビューをやり直す（`REVIEW_INDEX` は据え置き、起動またはレビュー実行のみ再送）

## reviewer 実行パラメータ（共通）

- **model**: `role=coding`
- **プロンプト**:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `REVIEW_INDEX=NN`（初回 `01`、再レビュー時はインクリメント。起動する全体で同じ番号を共有する）
  - `REVIEWER_ROLE=[correctness|consistency|quality|security|architecture]`（体ごとに変える。REVIEWER_SET に含まれる観点のみ）
  - `{RUN_DIR}/plan.md` のパス
  - `{RUN_DIR}/implementation-{最新 IMPL_INDEX}.md` のパス
  - 「レビューレポート本体は `{RUN_DIR}/review-{REVIEW_INDEX}-{REVIEWER_ROLE}.md` に書き出し、チャットには VERDICT + 要約のみ返してください」

## refactor-advisor との関係

refactor-advisor は Fan-Out Gate の対象外。差し戻しループ中に走らせてもバグ修正でコードが変わる前提なので提案の意味が薄い。reviewer 全員 PASS 後の独立ステップ（pir2 のステップ 7.5）で 1 回だけ実行する。詳細は `~/.agents/skills/pir2/references/refactor-advisor-gate.md` を参照。
