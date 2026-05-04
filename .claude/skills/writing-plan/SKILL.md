---
name: writing-plan
description: 実装計画を作成し、各ステップ完了後にドキュメントへ追記して最終的に実装記録として残す。PIR²のP+Iフェーズとしても単独でも使う。「計画を立てて」「ステップバイステップで進めて」「段階的に実装して」「実装記録を残したい」といった要望にも対応する。ユーザーが /writing-plan と入力したら必ずこのスキルを使う。
argument-hint: [タスクの説明]
---

# ライティングプラン — 計画 → 実装追記 → ドキュメント化

**タスク**: $ARGUMENTS

実装計画を作成し、各ステップの完了後にドキュメントへ追記します。このスキル本体（= メイン Claude）がオーケストレーターとなり、`planner` / `implementer` / `reviewer` を `Agent` ツールで順に起動します。reviewer は correctness / consistency / quality / security / architecture の 5 観点から **REVIEWER_SET に含まれる観点のみ並列起動** します（planner 系スキルなのでデフォルトは全 5 観点固定。`--reviewers=<roles>` / `--all-reviewers` フラグで上書き可能）。サブエージェント内からの Agent 呼び出しは Claude Code の設計上不可能なため、起動責任はスキル本体に集約されます。
最終的にこのドキュメントは「実装記録」として機能します（確認後に削除する想定）。

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
- `HANDOFF_PATH=...`（/writing-plan では使用しない）
- `RESUME_MODE=...`（/writing-plan では使用しない）

`/writing-plan` は handoff 連携を行わないため、`HANDOFF_PATH` と `RESUME_MODE` は無視してください。

---

## ステップ 1: 実装計画の作成

スキル本体（メイン Claude）が `planner` サブエージェントを `Agent` ツールで起動してください。

- model: `opus`
- プロンプト:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - タスク内容（$ARGUMENTS）
  - タスクを独立した bite-sized なステップに分解し、各ステップの完了基準を明確にした計画を作成するよう指示する
  - 「プラン本体は `{RUN_DIR}/plan.md` に書き出し、チャットには要約のみ返してください」

プラン要約を受け取ったら次のステップへ進んでください。

---

## ステップ 2: ドキュメントの初期化

`docs/plans/` ディレクトリがなければ作成してください。

以下の形式でドキュメントを作成してください。
ブレインストーム設計ドキュメント（`docs/brainstorm/` 配下）が存在する場合は参照先として記載してください。

**保存先**: `docs/plans/YYYY-MM-DD-<feature>.md`（YYYY-MM-DD は今日の日付）

ファイルを保存したら、**すぐに**以下の形式でパスをユーザーに提示してください：

```
プラン: docs/plans/YYYY-MM-DD-<feature>.md
```

```markdown
# [タスク名] 実装記録

_作成: YYYY-MM-DD | ステータス: 進行中_

## 目標

[タスクの概要]

## 実装計画

- [ ] ステップ 1: [ステップ名]
- [ ] ステップ 2: [ステップ名]
- [ ] ステップ 3: [ステップ名]

---

## 設計詳細

[`{RUN_DIR}/plan.md` を Read して詳細プランをそのまま転記（対象ファイル・変更内容・理由・検証方法・影響範囲）]

---

## 実装ログ

<!-- 各ステップ完了時に追記される -->
```

---

## ステップ 3: 実装と追記のループ

計画の各ステップについて順番に以下を繰り返してください。`IMPL_INDEX` と `REVIEW_INDEX` は全体を通じて連続してインクリメントします（計画ステップをまたいで継続）。初期値は `IMPL_INDEX=00`・`REVIEW_INDEX=00`。

### 3-1. 実装

`IMPL_INDEX += 1`（2桁ゼロ埋め）してから、スキル本体（メイン Claude）が `implementer` サブエージェントを `Agent` ツールで起動する。

- model: `sonnet`
- プロンプト:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `IMPL_INDEX=[NN]`
  - `{RUN_DIR}/plan.md` のパス
  - 該当ステップの詳細
  - 「このステップのみ実装してください。実装完了レポート本体は `{RUN_DIR}/implementation-{IMPL_INDEX}.md` に書き出し、チャットには要約のみ返してください」

### 3-2. ドキュメントへの追記

実装要約を受け取ったら、ドキュメントを更新する：

1. 計画セクションの `[ ]` を `[x]` に変更
2. 実装ログセクションに追記（`{RUN_DIR}/implementation-{IMPL_INDEX}.md` を Read して詳細を転記）：

```markdown
### ステップ N: [ステップ名]

- 変更ファイル: [一覧]
- 実装内容: [概要]
```

### 3-3. レビュー (Sonnet ハイブリッド並列)

初回ステップでのみ `REVIEWER_SET` を決定する（全計画ステップで同じ集合を使い回す。途中で追加・削除しない）:

1. **ユーザーフラグのパース**: `$ARGUMENTS` に `--reviewers=<roles>` が含まれていればカンマ区切りを観点集合として採用（未知 role は無視）。`--all-reviewers` があれば全 5 観点。両方指定時は `--reviewers=` を優先。フラグ抽出後の残りをタスク説明として扱う
2. **フラグ未指定時のデフォルト**: 全 5 観点 `[correctness, consistency, quality, security, architecture]`（planner 系スキル）
3. 決定した `REVIEWER_SET` をドキュメントのヘッダー部（「実装記録」）に記録

`REVIEW_INDEX += 1`（2桁ゼロ埋め）してから、以下の Fan-Out Gate 手順で reviewer を並列起動する。

#### 3-3A: 起動宣言（Fan-Out Gate — 並列発火の直前に必ず書く）

reviewer 並列起動メッセージを送信する **直前のターン本文中** に、以下のテンプレートを必ず生成すること。このテンプレートが本文に出現していないターンで Agent 起動を発火させた場合は、ステップ完了判定を取り消して 3-3A からやり直す。

> **Fan-Out Gate（reviewer）**
> - REVIEWER_SET = [<観点をカンマ区切りで全列挙>]
> - 起動体数 = <N>（= len(REVIEWER_SET)、必ず一致）
> - 同一 function_calls ブロックに <N> 個の Agent 起動を並べる
> - 1 体ずつ起動・後追い起動・観点削減はいずれも違反

このブロックは「起動直前の自己コミットメント」であり、自分の手癖（1 体ずつ逐次起動する癖）を止めるためのフェンスとして機能する。各計画ステップのレビュー時と、修正ループでの再レビュー時にも毎回この宣言を書くこと。

#### 3-3B: 並列発火（同一メッセージ内）

直前ターンで宣言した REVIEWER_SET の各観点について、同一の `<function_calls>` ブロック内に Agent ツール呼び出しを **N 個** 並べて 1 メッセージで同時送信する。各体は `REVIEWER_ROLE` を変えて担当観点を分割する:

- `REVIEWER_ROLE=correctness`: バグ・正確性 / パフォーマンス / リグレッション
- `REVIEWER_ROLE=consistency`: 命名規則・構造一貫性 / 同一ロジック全適用網羅性 / 類似ファイル群波及網羅性
- `REVIEWER_ROLE=quality`: 保守性（局所スコープ）/ テストの質 / データアクセス重複 / スコープ逸脱
- `REVIEWER_ROLE=security`: セキュリティ（OWASP）/ 認可・認証 / シークレット漏洩 / 依存脆弱性
- `REVIEWER_ROLE=architecture`: レイヤリング / 循環依存 / 責務逸脱 / 抽象粒度

違反パターン（次のいずれかが発生したら違反として検出し 3-3A からやり直す）:
- function_calls ブロックが 2 ターン以上に分かれる
- 並んだ Agent 起動の数が宣言した N より少ない
- 観点を独自判断で減らした
- 直前ターンの宣言テンプレートが省略された

各体の起動パラメータ:

- model: `sonnet`
- プロンプト（共通。`REVIEWER_ROLE` のみ変える）:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `REVIEW_INDEX=[NN]`（起動する全体で同じ番号を共有する）
  - `REVIEWER_ROLE=[correctness|consistency|quality|security|architecture]`（体ごとに変える。REVIEWER_SET に含まれる観点のみ）
  - `{RUN_DIR}/plan.md` のパス
  - `{RUN_DIR}/implementation-{最新 IMPL_INDEX}.md` のパス
  - 「レビューレポート本体は `{RUN_DIR}/review-{REVIEW_INDEX}-{REVIEWER_ROLE}.md` に書き出し、チャットには VERDICT + 要約のみ返してください」

### 3-4. VERDICT 集約とループ (最大2回)

- **全体 VERDICT = PASS**: 起動した全員が `VERDICT: PASS` → 次のステップへ
- **全体 VERDICT = FAIL**: 1体でも `VERDICT: FAIL` → 修正ループへ

**修正ループ**: 各計画ステップごとに `LOOP_COUNT = 0` で開始。

1. `LOOP_COUNT += 1`
2. `LOOP_COUNT >= 2` に達した場合はループを終了し、当該ステップを FAIL として記録して次の計画ステップへ進む
3. `implementer` を再起動する（`IMPL_INDEX` をインクリメント、**FAIL を返した全 reviewer の `{RUN_DIR}/review-{最新}-{ROLE}.md` パスを全て**レビュー指摘事項として渡す、`{RUN_DIR}/plan.md` のパスも渡す）
4. **3-3A（Fan-Out Gate 宣言）→ 3-3B（並列発火）の手順で** `reviewer` を **同じ REVIEWER_SET で**並列で再起動して VERDICT を確認する（`REVIEW_INDEX` をインクリメント、最新の `{RUN_DIR}/implementation-{最新}.md` のパスを渡す。PASS を返した観点も再レビューする。**再レビュー時も Fan-Out Gate を省略しないこと**）
5. 全体 FAIL なら繰り返す

---

## ステップ 4: ドキュメントの最終化

すべてのステップが完了したら、ドキュメントのヘッダーを更新してください：

```markdown
_作成: YYYY-MM-DD | ステータス: **完了** YYYY-MM-DD_
```

末尾に総括セクションを追加してください：

```markdown
## 総括

- 完了ステップ数: N/N

> **このドキュメントは内容を確認後に削除してください。**
> `rm docs/plans/YYYY-MM-DD-<feature>.md`
```

複数セッションにまたがる大きな機能を実装している場合（= 今回のセッションで全ステップが完了していない場合）は、総括の代わりに以下の「次セッションへの引き継ぎ」セクションを追加し、ドキュメントは削除せず残してください。

```markdown
## 次セッションへの引き継ぎ

### 今セッションで完了したもの
- [変更・追加したファイル一覧]

### 意図的に今回スコープから外したもの
- [項目] — 理由: [なぜ今回やらないか]

### 次セッションで着手すべきタスク
- [タスク名] — 前提: [このタスクに取り掛かる前に確認すべきこと]

### 設計から変更した点
- [変更点] — 理由: [なぜ設計ドキュメントから逸脱したか]

### 詰まったポイント・迂回した仕様
- [詰まりの概要と暫定対応]
```

設計書（`docs/brainstorm/` 配下）は不変の全体像、実装プラン（`docs/plans/` 配下）はセッション単位の進捗、という役割分担を守ってください。次セッションはこの handoff セクションだけを読めば再開できる状態にすることが目的です。

---

## ステップ 5: 完了サマリーの提示

```
## ライティングプラン 完了

### タスク
[タスクの説明]

### 実装記録
docs/plans/YYYY-MM-DD-<feature>.md

### 完了ステップ
- [x] ステップ 1: ...
- [x] ステップ 2: ...

### レビュー集約
- REVIEWER_SET: [起動した観点のカンマ区切り、例: correctness,consistency,quality,security,architecture]
- 各ステップごとに REVIEWER_SET の観点で並列レビューを実施
- FAIL で上限 2 回の修正ループに到達したステップがあれば明記

> 内容を確認後、docs/plans/YYYY-MM-DD-<feature>.md を削除してください。
```
