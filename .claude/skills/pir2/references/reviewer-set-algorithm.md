# REVIEWER_SET 自動選定アルゴリズム

reviewer エージェントを呼ぶスキル（/pir2, /pir2async, /debug, /ir, /reviewer, /review-pr, /writing-plan）が共有する REVIEWER_SET 決定ロジックの SSOT。詳細仕様は `~/.claude/agents/reviewer.md` の「呼び出し元（スキル本体）への運用ガイド」を参照。

## デフォルト挙動

| スキル分類 | デフォルト |
|-----------|-----------|
| planner 系（/pir2, /pir2async, /debug, /writing-plan） | 全 5 観点固定 |
| 非 planner 系（/ir, /reviewer, /review-pr） | 自動選定（1〜5 体） |

## ユーザーフラグ

- `--reviewers=<roles>`: カンマ区切りで明示指定
- `--all-reviewers`: 全 5 観点を強制起動
- 両方指定時は `--reviewers=` を優先

## 自動選定アルゴリズム（非 planner 系で、フラグ未指定時）

以下を上から評価し、該当した観点を集合に追加する:

1. `correctness` は常に含める（動作正否の最低限ゲート）
2. 対象に**コード変更**がある（ドキュメント・設定のみでない） → `consistency` を追加
3. タスク文言または差分テキストに**セキュリティ関連語句**（認証 / 認可 / auth / token / secret / password / credential / SQL / XSS / CSRF / シリアライズ / 外部API / ユーザー入力 / validate / sanitize / 権限 / 暗号 / crypto / 脆弱性）が含まれる → `security` を追加
4. **新規ファイル追加**・**新規ディレクトリ作成**・**複数モジュール/レイヤー跨ぎ**の変更 → `architecture` を追加
5. **新規関数・メソッド・クラスの追加**、または**ロジック変更行数 > 20 行** → `quality` を追加
6. **判断に迷う**（差分が取得できない・タスク文言が曖昧・上記ルールで 1 体しか選ばれないが自信なし） → **全 5 観点にフォールバック**

## スキル別の入力ソース

自動選定が適用される非 planner 系スキルは、「コード変更の有無 / セキュリティ語句の有無 / 新規ファイル追加 / 差分行数」を判断する入力ソースがそれぞれ異なる:
- /ir: implementer 返り値の変更ファイル一覧 / `{RUN_DIR}/implementation-{IMPL_INDEX}.md` の差分テキスト
- /reviewer: `git diff --name-only <range>` / `git diff <range>` の出力
- /review-pr: `gh pr diff <番号>` または `git diff <branch>...HEAD`、PR タイトル/本文

planner 系スキル（/pir2, /pir2async, /debug, /writing-plan）は全 5 観点固定のため自動選定は適用されない。/writing-plan は実装完了レポート（`{RUN_DIR}/implementation-{IMPL_INDEX}.md`）の差分テキストを参照するが、デフォルト 5 観点固定のため自動選定アルゴリズムの判定対象にはならない。

詳細は各スキルの SKILL.md 内「REVIEWER_SET 決定」セクションを参照（このファイルとの一致を保つこと）。
