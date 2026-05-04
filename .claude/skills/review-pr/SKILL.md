---
name: review-pr
description: PR・リモートブランチ単位でコードレビューする。PR番号・PRのURL・リモートブランチ名を渡されたとき、「PR確認して」「PRレビュー」「review this PR」「gh pr の差分を見て」といった要望に使う。ローカルの未コミット差分・ファイル指定のレビューは /reviewer を使うこと。ユーザーが /review-pr と入力したら必ずこのスキルを使う。
argument-hint: [PR番号, ブランチ名, またはファイルパス]
---

# Review PR — コードレビュー

変更差分をレビューします。このスキル本体（= メイン Claude）がオーケストレーターとなり、`reviewer` を `Agent` ツールで **ハイブリッド並列起動**（correctness / consistency / quality / security / architecture の 5 観点から必要なものを選択して 1〜5 体）します。サブエージェント内からの Agent 呼び出しは Claude Code の設計上不可能なため、起動責任はスキル本体に集約されます。

**対象**: $ARGUMENTS（PR番号、ブランチ名、またはファイルパス。省略時は現在のステージング差分）

---

## ステップ 0: プロジェクトメモリパスと RUN_DIR の確認

以下の Bash コマンドで PROJECT_MEMORY_DIR と RUN_DIR を取得し、以降のすべてのステップで使用してください:

```bash
sh ~/.claude/lib/pir-preflight.sh "$ARGUMENTS"
```

出力フォーマット（5 行の `KEY=VALUE`）:
- `PROJECT_MEMORY_DIR=...`
- `PROJECT_ROOT=...`
- `RUN_DIR=...`
- `HANDOFF_PATH=...`（/review-pr では使用しない）
- `RESUME_MODE=...`（/review-pr では使用しない）

`/review-pr` は handoff 連携を行わないため、`HANDOFF_PATH` と `RESUME_MODE` は無視してください。

---

## ステップ 1: 差分の取得

まず `$ARGUMENTS` から `--reviewers=<roles>` と `--all-reviewers` フラグを**抽出して除去**し、残りを対象指定として扱う。次に残り部分に応じて差分を取得する:

- **PR番号が指定された場合**: `gh pr diff <番号>` で差分を取得する
- **ブランチ名が指定された場合**: `git diff <ブランチ名>...HEAD` で差分を取得する
- **ファイルパスが指定された場合**: 該当ファイルを Read する
- **引数なし**: `git diff HEAD` でステージング済み＋未ステージの差分を取得する

いずれもユーザーが対象（PR/ブランチ/ファイル）を明示した上での差分・ピンポイント取得であり、`~/.claude/CLAUDE.md`「コードベース探索の委譲」の例外（VCS 軽量確認 / ユーザー提示ファイルのピンポイント Read）に該当します。メイン Claude が自発的に広域探索（Grep/Glob 等）を開始する場合はこの例外に該当しないため、explorer に委譲してください。

取得した差分を `{RUN_DIR}/diff.patch` に Write で保存してください（起動する reviewer 全員に同じ差分を参照させるため、インライン展開ではなくファイル経由で渡す）。変更ファイル一覧は差分からパースして取得する。

---

## ステップ 2: レビュー (Sonnet ハイブリッド並列)

### 2-1: REVIEWER_SET 決定（非 planner 系：自動選定がデフォルト）

`REVIEWER_SET` を決定する:

1. **ユーザーフラグ**: ステップ 1 で抽出した `--reviewers=<roles>` があればカンマ区切りを観点集合として採用（未知 role は無視）。`--all-reviewers` があれば全 5 観点。両方指定時は `--reviewers=` を優先
2. **フラグ未指定時の自動選定**（以下を上から評価）:
   1. `correctness` は常に含める
   2. 変更ファイル一覧にコード拡張子が含まれる（ドキュメント・設定のみでない） → `consistency` を追加
   3. `{RUN_DIR}/diff.patch` の内容または PR タイトル/本文に**セキュリティ関連語句**（認証 / 認可 / auth / token / secret / password / credential / SQL / XSS / CSRF / シリアライズ / 外部API / ユーザー入力 / validate / sanitize / 権限 / 暗号 / crypto / 脆弱性）が含まれる → `security` を追加
   4. 差分に**新規ファイル追加**（`diff --git a/dev/null` or `new file mode`）、または変更ファイルが 2 つ以上の異なるトップレベルディレクトリにまたがる → `architecture` を追加
   5. 差分に**新規関数・メソッド・クラスの追加**、または**差分行数 > 20 行** → `quality` を追加
   6. **判断に迷う**（diff が取得できない・対象が曖昧・上記ルールで 1 体しか選ばれないが自信なし） → **全 5 観点にフォールバック**
3. 決定した `REVIEWER_SET` をユーザー提示に含める

### 2-2: reviewer を並列起動

スキル本体（メイン Claude）が `reviewer` サブエージェントを `Agent` ツールで **REVIEWER_SET の観点数ぶん並列起動** してください。1メッセージ内に Agent ツール呼び出しを **観点数ぶん** 並べて同時発火させること（逐次起動は禁止）。各体は `REVIEWER_ROLE` を変えて担当観点を分割する:

> ⚠️ **完了条件チェック（厳守）**: このステップを完了したと判定する前に、以下を満たしているか必ず自己確認すること。1 つでも No なら違反であり、起動メッセージを送信せず構成し直す。
> - [ ] 同一の `<function_calls>` ブロックの中に Agent ツール呼び出しが `len(REVIEWER_SET)` 個ぶん並んでいるか？
> - [ ] 「とりあえず 1 体起動して残りは次のターンで」のような分割発火になっていないか？
> - [ ] 「軽いタスクだから 1 体でいい」「直前のレビューで 1 観点しか問題が出なかったから今回も 1 観点でいい」という独自判断で観点を減らしていないか？

- `REVIEWER_ROLE=correctness`: バグ・正確性 / パフォーマンス / リグレッション
- `REVIEWER_ROLE=consistency`: 命名規則・構造一貫性 / 同一ロジック全適用網羅性 / 類似ファイル群波及網羅性
- `REVIEWER_ROLE=quality`: 保守性（局所スコープ）/ テストの質 / データアクセス重複 / スコープ逸脱
- `REVIEWER_ROLE=security`: セキュリティ（OWASP）/ 認可・認証 / シークレット漏洩 / 依存脆弱性
- `REVIEWER_ROLE=architecture`: レイヤリング / 循環依存 / 責務逸脱 / 抽象粒度

各体の起動パラメータ:

- model: `sonnet`
- プロンプト（共通。`REVIEWER_ROLE` のみ変える）:
  - `PROJECT_MEMORY_DIR=[ステップ0で取得したパス]`
  - `RUN_DIR=[ステップ0で取得したパス]`
  - `REVIEW_INDEX=01`（起動する全体で同じ番号を共有する）
  - `REVIEWER_ROLE=[correctness|consistency|quality|security|architecture]`（体ごとに変える。REVIEWER_SET に含まれる観点のみ）
  - 変更ファイル一覧
  - 差分ファイルのパス: `{RUN_DIR}/diff.patch`
  - 「これはコードレビューです。実装は行わず、レビューのみ行ってください。plan.md / implementation-*.md は存在しません。`{RUN_DIR}/diff.patch` を Read して変更内容を確認し、変更されたファイルの現状も必要に応じて Read してレビューしてください。レビューレポート本体は `{RUN_DIR}/review-{REVIEW_INDEX}-{REVIEWER_ROLE}.md` に書き出し、チャットには VERDICT + 要約のみ返してください」

---

## ステップ 3: 結果の統合・提示

起動した reviewer の VERDICT と書き出したレポートをユーザーに提示する:

### VERDICT 集約

- **全体 VERDICT = PASS**: 起動した全員が `VERDICT: PASS`
- **全体 VERDICT = FAIL**: 1体でも `VERDICT: FAIL`

### ユーザーへの提示フォーマット

```
## PR レビュー完了

### 対象
[PR番号 / ブランチ名 / ファイルパス]

### 全体 VERDICT
[PASS|FAIL]

### REVIEWER_SET
[起動した観点のカンマ区切り、例: correctness,consistency,security]

### 観点別 VERDICT
（REVIEWER_SET に含まれる観点のみ。例）
- correctness: [PASS|FAIL] — {RUN_DIR}/review-01-correctness.md
- consistency: [PASS|FAIL] — {RUN_DIR}/review-01-consistency.md
- security: [PASS|FAIL] — {RUN_DIR}/review-01-security.md

### 主な指摘事項（Critical / High のみ）
- [深刻度] `ファイル:行` — [問題の要約]（出典: [ROLE]）
```

各 reviewer が書き出した `{RUN_DIR}/review-01-{ROLE}.md` を Read して、Critical / High の問題一覧を統合してユーザーに提示する。Medium / Low は件数サマリーのみに留める（詳細はファイル参照）。
