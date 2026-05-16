# Fan-Out Gate（reviewer 並列起動）

PIR² 系スキル（/pir2 等）の reviewer 並列起動仕様。「並列発火を 1 メッセージで完遂する」ためのプロトコル。SKILL.md 側で 7-2A 宣言テンプレートを発火させた後の起動本体・違反検知・リカバリ・起動パラメータをここに集約する。

## 起動宣言テンプレート（Fan-Out Gate 本体）

reviewer 並列起動メッセージを送信する **直前のターン本文中** に、以下のテンプレートを必ず生成すること。このテンプレートが本文に出現していないターンで Agent 起動を発火させた場合は、ステップ完了判定を取り消して宣言からやり直す。

> **Fan-Out Gate（reviewer）**
> - REVIEWER_SET = [<観点をカンマ区切りで全列挙>]
> - 起動体数 = <N>（= len(REVIEWER_SET)、必ず一致）
> - 同一 function_calls ブロックに <N> 個の Agent 起動を並べる
> - 1 体ずつ起動・後追い起動・観点削減はいずれも違反

このブロックは「起動直前の自己コミットメント」であり、自分の手癖（1 体ずつ逐次起動する癖）を止めるためのフェンスとして機能する。再レビュー時にも毎回この宣言を書くこと。

**pir2async の Agent Teams 版**では実装+レビューチーム作成時にも適用する。テンプレートを以下に置換:
> **Fan-Out Gate（impl-review チーム）**
> - REVIEWER_SET = [<観点をカンマ区切りで全列挙>]
> - 起動体数 = <N+1>（implementer 1 体 + reviewer N 体 = 1 + len(REVIEWER_SET)、必ず一致）
> - 同一 function_calls ブロックに <N+1> 個の Agent 起動を並べる
> - implementer だけ先に起動・reviewer を後追い追加・観点削減はいずれも違反

## 観点マッピング（reviewer.md の SSOT に従う）

`REVIEWER_ROLE` ごとの担当観点。詳細は `~/.claude/agents/reviewer.md` の「呼び出し元（スキル本体）への運用ガイド」を参照する:

- `correctness`: バグ・正確性 / パフォーマンス / リグレッション
- `consistency`: 命名規則・構造一貫性 / 同一ロジック全適用網羅性 / 類似ファイル群波及網羅性
- `quality`: 保守性（局所スコープ）/ テストの質 / データアクセス重複 / スコープ逸脱
- `security`: セキュリティ（OWASP）/ 認可・認証 / シークレット漏洩 / 依存脆弱性
- `architecture`: レイヤリング / 循環依存 / 責務逸脱 / 抽象粒度

## 違反パターンと検出

次のいずれかが発生したら違反として検出し、Fan-Out Gate 宣言（SKILL.md の 7-2A）からやり直す:

- function_calls ブロックが 2 ターン以上に分かれる
- 並んだ Agent 起動の数が宣言した N より少ない
- 観点を独自判断で減らした
- 直前ターンの宣言テンプレートが省略された

## 違反検出時のリカバリ

1. 不完全に起動された Agent は完了を待ってから結果を破棄する
2. Fan-Out Gate の宣言テンプレートを正しく書き直す
3. 並列発火をやり直す（`REVIEW_INDEX` は据え置き、起動メッセージのみ再送）

## reviewer 起動パラメータ（共通）

- **model**: `sonnet`
- **プロンプト**:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `REVIEW_INDEX=NN`（初回 `01`、再レビュー時はインクリメント。起動する全体で同じ番号を共有する）
  - `REVIEWER_ROLE=[correctness|consistency|quality|security|architecture]`（体ごとに変える。REVIEWER_SET に含まれる観点のみ）
  - `{RUN_DIR}/plan.md` のパス
  - `{RUN_DIR}/implementation-{最新 IMPL_INDEX}.md` のパス
  - 「レビューレポート本体は `{RUN_DIR}/review-{REVIEW_INDEX}-{REVIEWER_ROLE}.md` に書き出し、チャットには VERDICT + 要約のみ返してください」

## refactor-advisor との関係

refactor-advisor は Fan-Out Gate の対象外。差し戻しループ中に走らせてもバグ修正でコードが変わる前提なので提案の意味が薄い。reviewer 全員 PASS 後の独立ステップ（pir2 のステップ 7.5）で 1 回だけ起動する。詳細は `~/.claude/skills/pir2/references/refactor-advisor-gate.md` を参照。
