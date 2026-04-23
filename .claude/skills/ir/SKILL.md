---
name: ir
description: 軽量な Implement → Review の2フェーズワークフロー。タスクが明確で小さい場合に使う。バグ修正・小機能追加・設定変更・ファイル修正など、計画不要で「サクッとやって」「これ直して」「簡単な変更」といった要望に対応する。ユーザーが /ir と入力したら必ずこのスキルを使う。
argument-hint: [タスクの説明]
---

# IR — Implement → Review

軽量ワークフローを実行します。プランニング・振り返りなしで、小さいタスクに使います。このスキル本体（= メイン Claude）がオーケストレーターとなり、`implementer` / `reviewer` を `Agent` ツールで順に起動します。サブエージェント内からの Agent 呼び出しは Claude Code の設計上不可能なため、起動責任はスキル本体に集約されます。

**タスク**: $ARGUMENTS

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
- `HANDOFF_PATH=...`（/ir では使用しない）
- `RESUME_MODE=...`（/ir では使用しない）

`/ir` は handoff 連携を行わないため、`HANDOFF_PATH` と `RESUME_MODE` は無視してください。`PROJECT_MEMORY_DIR` と `RUN_DIR` のみ以降のステップで使用します。

---

## ステップ 1: 実装 (Sonnet)

スキル本体（メイン Claude）が `implementer` サブエージェントを `Agent` ツールで起動してください。

- model: `sonnet`
- プロンプト:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `IMPL_INDEX=01`（初回。再実装時はインクリメント）
  - タスク内容（$ARGUMENTS）
  - 「プランなしで直接実装してください。plan.md は存在しません。実装完了レポート本体は `{RUN_DIR}/implementation-{IMPL_INDEX}.md` に書き出し、チャットには要約のみ返してください」

実装要約を受け取ったら次のステップへ進んでください。

---

## ステップ 2: レビュー (Sonnet ハイブリッド並列)

### 2-1: REVIEWER_SET 決定（非 planner 系：自動選定がデフォルト）

`REVIEWER_SET` を決定する:

1. **ユーザーフラグのパース**: `$ARGUMENTS` に `--reviewers=<roles>` が含まれていればカンマ区切りを観点集合として採用（未知 role は無視）。`--all-reviewers` が含まれていれば全 5 観点を採用。両方指定時は `--reviewers=` を優先。フラグ抽出後の残りをタスク説明として扱う
2. **フラグ未指定時の自動選定**（以下を上から評価し該当観点を集合に追加）:
   1. `correctness` は常に含める（動作正否の最低限ゲート）
   2. 実装がコード変更を含む（ドキュメント・設定のみでない。implementer 返り値の変更ファイル一覧で判定） → `consistency` を追加
   3. タスク文言または `{RUN_DIR}/implementation-{IMPL_INDEX}.md` の差分テキストに**セキュリティ関連語句**（認証 / 認可 / auth / token / secret / password / credential / SQL / XSS / CSRF / シリアライズ / 外部API / ユーザー入力 / validate / sanitize / 権限 / 暗号 / crypto / 脆弱性）が含まれる → `security` を追加
   4. 実装で**新規ファイル追加**・**新規ディレクトリ作成**・**複数モジュール/レイヤー跨ぎ** → `architecture` を追加
   5. 実装で**新規関数・メソッド・クラスの追加**、または**ロジック変更行数 > 20 行** → `quality` を追加
   6. **判断に迷う**（implementation-*.md が読めない・タスク文言が曖昧・上記ルールで 1 体しか選ばれないが自信なし） → **全 5 観点にフォールバック**
3. 決定した `REVIEWER_SET` を最終サマリー（ステップ 4）に記録

### 2-2: reviewer を並列起動

スキル本体（メイン Claude）が `reviewer` サブエージェントを `Agent` ツールで **REVIEWER_SET の観点数ぶん並列起動** してください。1メッセージ内に Agent ツール呼び出しを **観点数ぶん** 並べて同時発火させること（逐次起動は禁止）。各体は `REVIEWER_ROLE` を変えて担当観点を分割する:

- `REVIEWER_ROLE=correctness`: バグ・正確性 / パフォーマンス / リグレッション
- `REVIEWER_ROLE=consistency`: 命名規則・構造一貫性 / 同一ロジック全適用網羅性 / 類似ファイル群波及網羅性
- `REVIEWER_ROLE=quality`: 保守性（局所スコープ）/ テストの質 / データアクセス重複 / スコープ逸脱
- `REVIEWER_ROLE=security`: セキュリティ（OWASP）/ 認可・認証 / シークレット漏洩 / 依存脆弱性
- `REVIEWER_ROLE=architecture`: レイヤリング / 循環依存 / 責務逸脱 / 抽象粒度

各体の起動パラメータ:

- model: `sonnet`
- プロンプト（共通。`REVIEWER_ROLE` のみ変える）:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `REVIEW_INDEX=01`（初回。再レビュー時はインクリメント。起動する全体で同じ番号を共有する）
  - `REVIEWER_ROLE=[correctness|consistency|quality|security|architecture]`（体ごとに変える。REVIEWER_SET に含まれる観点のみ）
  - `{RUN_DIR}/implementation-{最新 IMPL_INDEX}.md` のパス
  - 「plan.md は存在しません。implementation-*.md のみをレビュー対象としてください。レビューレポート本体は `{RUN_DIR}/review-{REVIEW_INDEX}-{REVIEWER_ROLE}.md` に書き出し、チャットには VERDICT + 要約のみ返してください」

### VERDICT 集約

**今回起動した reviewer** の VERDICT を以下のルールで集約する:

- **全体 VERDICT = PASS**: 起動した全員が `VERDICT: PASS`
- **全体 VERDICT = FAIL**: 1体でも `VERDICT: FAIL`

---

## ステップ 3: レビューループ (最大2回)

**LOOP_COUNT = 0 から始めてください。**

全体 `VERDICT: FAIL` の場合:

1. `LOOP_COUNT += 1`
2. `LOOP_COUNT >= 2` に達した場合はループを終了してステップ4へ進む
3. `implementer` を再起動する（`IMPL_INDEX` をインクリメント、**FAIL を返した全 reviewer の `{RUN_DIR}/review-{最新}-{ROLE}.md` パスを全て**レビュー指摘事項として渡す、元のタスク内容も渡す）
4. `reviewer` を **同じ REVIEWER_SET で**並列で再起動して VERDICT を確認する（`REVIEW_INDEX` をインクリメント、最新の `{RUN_DIR}/implementation-{最新}.md` のパスを渡す。PASS を返した観点も再レビューする。観点集合は初回選定を維持し途中で追加・削除しない）
5. 全体 FAIL なら繰り返す

全体 `VERDICT: PASS` になったらステップ4へ進んでください。

---

## ステップ 4: 最終サマリーの提示

```
## IR 完了サマリー

### タスク
[タスクの説明]

### 変更ファイル
[実装完了レポートから抜粋]

### レビュー結果
- 最終 VERDICT: [PASS/FAIL]
- ループ回数: [LOOP_COUNT]
- REVIEWER_SET: [起動した観点をカンマ区切り、例: correctness,consistency]
- 観点別の VERDICT: [REVIEWER_SET に含まれる観点のみ。例: correctness=[...], consistency=[...]]
- [主な指摘事項があれば記載]
```
