---
name: pir2
description: コーディングタスクを Plan → Implement → Review → Retrospect の4フェーズで実行する。複雑なタスク・設計が必要なタスク・品質保証が重要なタスク、大きな機能追加・リファクタリング・アーキテクチャ変更に使う。「ちゃんと作りたい」「しっかり実装して」「品質重視で」といった要望にも対応する。ユーザーが /pir2 と入力したら必ずこのスキルを使う。
argument-hint: [タスクの説明]
---

# PIR² — Plan → Implement → Review → Retrospect

PIR²ワークフローを実行します。このスキル本体（= メイン Claude）がオーケストレーターとなり、explorer → planner → implementer → reviewer → tester → retrospector を `Agent` ツールで順に起動します。サブエージェント内からの Agent 呼び出しは Claude Code の設計上不可能なため、オーケストレーションはここに集約されます。

**タスク**: $ARGUMENTS

---

## ステップ 1: プロジェクトメモリパスの確認

以下の Bash コマンドで現在のプロジェクトメモリパスとプロジェクトルートを取得し、以降のすべてのステップで使用してください:

```bash
sh ~/.claude/lib/pir-preflight.sh "$ARGUMENTS"
```

出力フォーマット（5 行の `KEY=VALUE`）:
- `PROJECT_MEMORY_DIR=...`
- `PROJECT_ROOT=...`
- `RUN_DIR=...`
- `HANDOFF_PATH=...`
- `RESUME_MODE=new|resume|passive-notice`

`RESUME_MODE` に応じて以降の挙動を分岐させる（詳細プロトコル: `~/.claude/pir-handoff.md`）:

- `resume`: ステップ 2（ブレスト）をスキップし、planner への入力に `HANDOFF_PATH=$HANDOFF_PATH` を含めて「handoff.md の未チェック項目のみを planning 対象にせよ」と指示する。スキル本体は handoff.md を上書きしない
- `passive-notice`: 「💡 前回の handoff が残っています: `$HANDOFF_PATH`」とユーザーに表示し、通常の新規タスクフローで続行する（handoff.md は触らない）
- `new`: 通常の新規タスクフロー。planner の plan.md 完成直後にスキル本体が handoff.md 初期版を Write する（プランのステップを `[ ]` チェックリスト化）

retrospector フェーズ完了後、スキル本体は handoff.md を Read し、全項目が `[x]` なら削除、残項目ありなら「最終更新」タイムスタンプを更新する。

以降の各サブエージェントへのプロンプトには必ず `PROJECT_MEMORY_DIR=[パス]` および `RUN_DIR=[パス]` を含めてください。

---

## ステップ 2: ブレインストーミング（状況に応じて実施）

タスクの仕様を評価し、以下のいずれかに該当する場合は brainstorm スキルを実行してから次のステップへ進んでください：

- 要件が曖昧で複数の解釈が可能
- アーキテクチャ上の選択肢が複数あり、どれを選ぶかユーザーに確認が必要
- ユーザーとの対話を通じて設計を固めたほうが手戻りリスクを減らせると判断される

実行方法: Skill ツールで `skill: "brainstorm"` を呼び出す。ユーザーとの対話で固まった設計はステップ4の planner に渡してください。

該当しない場合（タスクが明確、既存の設計がある、`docs/brainstorm/` に関連する設計ドキュメントが存在する）はスキップしてください。

---

## ステップ 3: 探索フェーズ（explorer）

コードベース探索はメイン Claude が **直接** Glob/Grep/Read で行ってはならない。必ず `explorer` エージェントを `Agent` ツールで起動し、調査を委譲してください。

### 起動ルール

- **最低1体起動**: タスクの規模にかかわらず初回探索は必須
- **最大3体並列**: 調査領域が独立している場合のみ並列起動
- **モデル使い分け**:
  - `haiku`: 広く浅い調査（ファイル構造、パターン列挙、grep 結果の収集）。最大3体並列可
  - `sonnet`: 深く読み解く調査（既存ロジックの意味理解、設計意図の把握）。最大1体
  - `opus`: sonnet でも読み解けなかった場合のフォールバック（高度な間接参照、メタプログラミング、複雑な状態遷移）。最大1体、他層と並列起動しない
- **ミックス起動可**: 広さと深さを同時に欲しい場合は haiku と sonnet を同ターンで並列起動してよい。opus は単独起動とする
- **opus 発動条件**: sonnet の探索レポートで「既存ロジックの意図を推測で補っている」「複数回の間接参照で追跡が途中で途切れている」「メタプログラミング/DSL により表層の grep では意味が取れない」と判断した場合のみ。常用しない

### プロンプトに必ず含めるパラメータ
- `PROJECT_MEMORY_DIR=[パス]`
- `RUN_DIR=[パス]`
- `EXPLORATION_INDEX=NN`（初回=`01`、並列起動時はスキル本体が `01`/`02`/`03` と割り振る）
- 「探索レポート本体は `{RUN_DIR}/exploration-{NN}.md` に書き出し、チャットには要約のみ返してください」

### プロンプトに必ず含める調査観点

- 変更対象と同一ドメイン・同一レイヤーの既存実装パターン（類似機能がどう実装されているか）
- 再利用可能な既存ユーティリティ・ヘルパー関数
- 変更対象のメソッド/関数内の他分岐が設定しているフィールド・処理の一覧
- フレームワークが自動処理する機能（新規コードで手動実装すべきでないもの）
- 調査対象がライブラリ・フレームワークの API 仕様に関わる場合は、公式 README / doc / Issue を WebFetch/WebSearch で裏取りし参照 URL をレポートに含めること（推測や記憶で結論を埋めさせない）

### 追加探索

初回レポートで不明点があれば追加で explorer を起動してください。回数上限なし。推測でプランを埋めるくらいなら追加探索を回す。追加探索時は `EXPLORATION_INDEX` を既存 `{RUN_DIR}/exploration-*.md` の最大値+1 に設定する。

### ライブラリ選定が必要な場合

新しいライブラリ・フレームワークの導入判断が必要なら `tech-validator` エージェントを起動する（既存の依存関係で解決できる場合はスキップ）。

---

## ステップ 4: プラン策定（planner）

`planner` エージェントを `Agent` ツールで起動し、タスク内容と探索レポート全文を渡してください。

- model: `opus`
- プロンプト:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - タスク内容
  - `{RUN_DIR}/exploration-*.md` のパス一覧（planner は本文を自分で Read する）
  - ブレインストーミング結果（ステップ2で実施した場合）
  - 「プランレポート本体は `{RUN_DIR}/plan.md` に書き出し、チャットには要約＋EXPLORATION_NEEDED の有無のみ返してください」

planner からプラン要約を受け取ってください。

### 既存パターン逸脱の事前申告

planner から「既存構造と異なる構成を採用する」判断が含まれたプランが返ってきた場合、実装着手前にユーザーに差分（既存 N 件中 M 件の構成 / 今回採用しようとしている構成 / 逸脱理由 / 代替案）を提示し、承認を得ること。承認なしに次のステップに進んではならない。

---

## ステップ 4.5: 能動的再探索ループ（最大5回）

planner の返り値要約に `### EXPLORATION_NEEDED` セクションがあり、かつ箇条書き項目（`- topic`）が1件以上含まれる（`- なし` 単独でない）場合、追加探索 → planner 再起動を繰り返す。

`REPLAN_COUNT = 0` から開始。

### 収束判定ロジック

planner の返り値要約テキストの `### EXPLORATION_NEEDED` セクションを見る:
- 見出しが存在しない、または直下が「なし」「- なし」のみ → **収束**。ステップ 5 へ進む
- `- topic` 形式の項目が1件以上列挙されている → 追加探索へ

### ループ本体

1. `REPLAN_COUNT += 1`
2. `REPLAN_COUNT > 5` に到達した場合、ループを強制終了してステップ 5 へ進む。最終サマリー（ステップ12）に「**planner が依然追加探索を要求中（ハードキャップ5回到達）**: [topic 一覧]」と明記する
3. planner が出した各 topic ごとに explorer を起動する（topic が独立なら最大3体並列）:
   - `EXPLORATION_INDEX` は `{RUN_DIR}/exploration-*.md` 既存ファイルの最大連番 + 1 から割り振る
   - プロンプトには topic 本文と共に「この topic の調査に集中する。既存探索レポート（`{RUN_DIR}/exploration-*.md` 参照可）の重複調査は不要」と指示
4. 追加探索が完了したら planner を再起動する:
   - プロンプトは初回と同じだが、`{RUN_DIR}/exploration-*.md` のパス一覧に新しく追加されたものも含める
   - `plan.md` は上書き更新される（planner は同じパスに Write する）
5. planner の新しい返り値要約の EXPLORATION_NEEDED をチェック → 収束していればステップ 5 へ、まだ要求が残っていれば 1. に戻る

> **注**: 「既存パターン逸脱の事前申告」のユーザー承認判定はループ収束後、ステップ 5 の直前に1回だけ行う（ループ中の中間プランに対しては承認を求めない）。

---

## ステップ 5: プラン保存

`docs/plans/` ディレクトリがなければ作成し、以下の形式でプランを保存してください:

**保存先**: `docs/plans/YYYY-MM-DD-<feature>.md`（YYYY-MM-DD は今日の日付）

保存したらユーザーにパスを提示:

```
プラン: docs/plans/YYYY-MM-DD-<feature>.md
```

ファイル内容のテンプレート:

```markdown
# [タスク名] 実装記録

_作成: YYYY-MM-DD | ステータス: 進行中_

## 目標

[タスクの概要]

## 実装計画

- [ ] ステップ1: [ステップ名]
- [ ] ステップ2: [ステップ名]
...

---

## 設計詳細

[{RUN_DIR}/plan.md を Read し、その内容をここに転記する]

---

## 実装ログ

### 実装完了

- 変更ファイル: （実装完了後に埋める）
- 実装内容: （実装完了後に埋める）

---

> このドキュメントは内容を確認後に削除してください。
> `rm docs/plans/YYYY-MM-DD-<feature>.md`
```

---

## ステップ 5.5: handoff.md 初期版生成（`RESUME_MODE=new` の場合のみ）

`RESUME_MODE=resume` または `passive-notice` の場合はこのステップをスキップしてください（既存 handoff.md を温存する）。

`RESUME_MODE=new` の場合のみ実行:

1. `{RUN_DIR}/plan.md` を Read し、「実装ステップ」に相当する項目を抽出する
2. `$HANDOFF_PATH` に `~/.claude/pir-handoff.md` の「フォーマット」節に従った内容で Write する:
   - `最終更新`: 現在時刻 + `run: $(basename $RUN_DIR)`
   - `タスク`: ユーザー指示の一行要約
   - `背景・決定事項`: plan.md から抽出した主要決定（なければ空セクションのまま）
   - `残 TODO`: 抽出した実装ステップを `- [ ] <ステップ名>` 形式に変換
   - `既知の問題 / 要確認`: 空セクションで用意
   - `関連 artifact`: `最新 plan: {RUN_DIR}/plan.md`

handoff.md のパスをユーザーに提示:

```
handoff: $HANDOFF_PATH
```

`RESUME_MODE=passive-notice` だった場合はこの時点で「💡 前回の handoff が残っています: `$HANDOFF_PATH`（`引継いで` で resume 可能）」とユーザーに表示してから次ステップへ。

---

## ステップ 6: 実装（implementer）

`INNER_LOOP_COUNT = 0`、`OUTER_LOOP_COUNT = 0` から開始してください。

`implementer` エージェントを `Agent` ツールで起動し、プラン全文を渡してください。

- model: `sonnet`
- プロンプト:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `IMPL_INDEX=01`（初回。再実装時は呼び出し元がインクリメント）
  - `{RUN_DIR}/plan.md` のパス（implementer が Read する）
  - （`RESUME_MODE` が `new` または `resume` の場合のみ）`HANDOFF_PATH=$HANDOFF_PATH` と「実装完了した項目を handoff.md で `[x]` 化し、新規発見の TODO は追記すること。詳細: `~/.claude/pir-handoff.md`」
  - 「実装完了レポート本体は `{RUN_DIR}/implementation-{IMPL_INDEX}.md` に書き出し、チャットには要約のみ返してください」
  - **役割境界の厳守（必須明示）**: 「プランに `go test` / `pytest` / `npm test` / `jest` / `rspec` など**テストスイート実行のステップ**が書かれていても、それは tester 専任のため **implementer は実行しないこと**（planner の誤記として扱い、実装完了レポートの『注意点・未解決事項』にスキップした旨を記録する）。実行してよいのは静的検証（lint / 型チェック）・ビルド・コード生成（`make apigen` など）・diff 確認まで。`make golden` もテスト実行を伴うため実行せず、golden の実生成は tester に委ねる」

implementer から実装要約を受け取ってください。

---

## ステップ 6.5: 実装者の未解決事項ユーザー確認（該当時のみ）

implementer の返り値要約で「注意点・未解決事項の有無」が **「あり」** の場合、次ステップへ進む前に必ずユーザーに判断を仰ぐ。スキル本体がスコープ縮小や仕様変更を独断してはならない。

### 6.5-1: 内容の確認

1. `{RUN_DIR}/implementation-{最新 IMPL_INDEX}.md` の「注意点・未解決事項」セクションを Read する
2. 未解決事項の性質を分類する:
   - **(a) プラン逸脱の報告**（プランの一部が実装できなかった / 前提が崩れた）
   - **(b) プラン通りに実装したが新たに発見した問題**（スコープ外の副次的な気づき）
   - **(c) 判断を委ねる事項**（implementer が明示的に「planner/ユーザーに判断を委ねる」と記載した箇所）

### 6.5-2: ユーザーへの提示

未解決事項の要点と分類を1〜3文で要約し、以下の選択肢を提示してユーザーの判断を受け取る:

- **(A) スコープ縮小を承認してレビューへ進む**: 未解決事項を次フェーズ繰越しとして記録し、ステップ 7 へ。`docs/plans/YYYY-MM-DD-*.md` の「注意点・未解決事項」セクションにも繰越し内容を明記する
- **(B) 再プラン**: ステップ 4 に戻り、planner に現在の implementation 状態と未解決事項を渡してプラン再策定（fallback 設計切り替え）。`{RUN_DIR}/implementation-{最新}.md` のパスも planner に渡すこと
- **(C) 追加指示で再実装**: implementer を再起動し、ユーザーからの追加指示を渡して再試行。`IMPL_INDEX` をインクリメントする

### 6.5-3: 判断の記録

ユーザーの選択と理由を `{RUN_DIR}/user-decisions.md` に追記する（ファイルがなければ作成）。形式:

```
## [YYYY-MM-DD HH:MM:SS] 未解決事項ユーザー確認

### 未解決事項の要約
[1〜3文]

### 選択
[A / B / C]

### 理由（ユーザーから得られた場合）
[理由]
```

### 6.5-4: スキップ条件

implementer の返り値要約で「注意点・未解決事項の有無」が **「なし」** の場合は本ステップをスキップし、ステップ 7 へ直接進む。

> **重要**: 仕様変更判断（スコープ縮小・フェーズ繰越し・API 変更等）はスキル本体ではなくユーザーに委ねる。「小さな変更だから」「fallback で動くから」を理由にユーザー確認を省略してはならない。

---

## ステップ 7: レビューループ（reviewer 5体並列、最大3回）

### 7-1: reviewer を 5体並列起動

`reviewer` エージェントを `Agent` ツールで **5体並列起動** してください。1メッセージ内に Agent ツール呼び出しを5つ並べて同時発火させること（逐次起動は禁止）。5体はそれぞれ `REVIEWER_ROLE` を変えて担当観点を分割する:

- `REVIEWER_ROLE=correctness`: バグ・正確性 / パフォーマンス / リグレッション
- `REVIEWER_ROLE=consistency`: 命名規則・構造一貫性 / 同一ロジック全適用網羅性 / 類似ファイル群波及網羅性
- `REVIEWER_ROLE=quality`: 保守性（局所スコープ）/ テストの質 / データアクセス重複 / スコープ逸脱
- `REVIEWER_ROLE=security`: セキュリティ（OWASP）/ 認可・認証 / シークレット漏洩 / 依存脆弱性
- `REVIEWER_ROLE=architecture`: レイヤリング / 循環依存 / 責務逸脱 / 抽象粒度

各体の起動パラメータ:

- model: `sonnet`
- プロンプト（5体共通）:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `REVIEW_INDEX=01`（初回。再レビュー時はインクリメント。5体で同じ番号を共有する）
  - `REVIEWER_ROLE=[correctness|consistency|quality|security|architecture]`（体ごとに変える）
  - `{RUN_DIR}/plan.md` のパス
  - `{RUN_DIR}/implementation-{最新 IMPL_INDEX}.md` のパス
  - 「レビューレポート本体は `{RUN_DIR}/review-{REVIEW_INDEX}-{REVIEWER_ROLE}.md` に書き出し、チャットには VERDICT + 要約のみ返してください」

### 7-2: VERDICT 集約

5体の VERDICT を以下のルールで集約する:

- **全体 VERDICT = PASS**: 5体すべて `VERDICT: PASS` の場合
- **全体 VERDICT = FAIL**: 1体でも `VERDICT: FAIL` を返した場合

### 7-3: 判定

- 全体 `VERDICT: PASS` → ステップ 8 へ
- 全体 `VERDICT: FAIL` →
  1. `INNER_LOOP_COUNT += 1`
  2. `INNER_LOOP_COUNT >= 3` ならステップ 8 へ強制移行（失敗として記録）
  3. `implementer` を再起動（`IMPL_INDEX` をインクリメント、**FAIL を返した全 reviewer の `{RUN_DIR}/review-{最新}-{ROLE}.md` パスを全て渡す**、`{RUN_DIR}/plan.md` のパスも渡す。マージ要約は作らず、implementer に各レポートを直接 Read させる）
  4. `reviewer` を 5体並列で再起動（`REVIEW_INDEX` をインクリメント、最新の `{RUN_DIR}/implementation-{最新}.md` のパスを渡す。PASS を返した観点も再レビューする = 修正による新たな退行を検知するため）
  5. 全体 PASS になるまで繰り返す

---

## ステップ 8: テストループ（tester、最大3回）

### 8-1: tester 起動

`tester` エージェントを `Agent` ツールで起動し、plan と最新 implementation のパスを渡してください。

- model: `sonnet`
- プロンプト:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `TEST_INDEX=01`（初回。再テスト時はインクリメント）
  - `{RUN_DIR}/plan.md` のパス
  - `{RUN_DIR}/implementation-{最新}.md` のパス
  - 「テストレポート本体は `{RUN_DIR}/test-{TEST_INDEX}.md` に書き出し、チャットには VERDICT + 要約のみ返してください。テストデータのクリーンアップはユーザー明示指示まで実行しないこと」

### 8-2: 判定

- `VERDICT: PASS` → ステップ 9 へ
- `VERDICT: FAIL` →
  1. `OUTER_LOOP_COUNT += 1`
  2. `OUTER_LOOP_COUNT >= 3` ならステップ 9 へ（失敗として記録）
  3. `INNER_LOOP_COUNT = 0` にリセット
  4. `implementer` を再起動（`IMPL_INDEX` をインクリメント、`{RUN_DIR}/test-{最新}.md` のパスを tester 指摘事項として渡す）
  5. **ステップ 7 に戻る**（レビューループを再実行、`REVIEW_INDEX` は継続インクリメント）
  6. tester を再起動（`TEST_INDEX` をインクリメント）
  7. PASS になるまで繰り返す

---

## ステップ 9: ウォークスルー生成（メイン Claude が直接）

変更されたファイルを Read して最終的な実装内容を確認し、ウォークスルーを作成します。

### フル版（内部記録）

各ファイルについて以下を記述:

```
#### [ファイルパス]
- 何を変更したか: [追加・変更・削除した内容]
- 主要なコード:
  [変更の核となるコード片を引用]
- なぜこの実装にしたか: [既存パターンとの整合性、トレードオフ、代替案を採用しなかった理由]
```

### サマリー版（統合レポートに載せる）

```
### ウォークスルー（サマリー版）

#### 変更の全体像
[30秒で把握できるよう3〜4文で。「何ができるようになったか」「何が直ったか」中心]

#### ファイルごとの変更
- `path/to/file1` — [1〜2行。必要なら核心のコード片を最大5行]
- `path/to/file2` — [同上]

#### 設計判断（非自明なもののみ）
[代替案がある中でなぜこの方法を選んだか。自明なら「特になし」]

#### レビュー総括
[何を確認し、なぜ PASS/FAIL としたか。簡潔に]
```

サマリー版の原則:
- 箇条書きは1階層まで。ネストしない
- コード片引用は変更の核心のみ、最大5行程度
- 「なぜ」は非自明な判断のみ
- 推測でコードを書かない。実際に Read したコードのみ引用する

実装記録ドキュメント（ステップ5で作成したファイル）の「実装ログ」セクションを埋めてください。

---

## ステップ 10: メモリへの記録

`PROJECT_MEMORY_DIR` 配下にタスクの振り返り材料を追記します:

- まず `mkdir -p {PROJECT_MEMORY_DIR}` でディレクトリを作成
- パス: `{PROJECT_MEMORY_DIR}/pir_skill_log.md`
- フォーマット: `## [タスク名] — [気づき・課題・パターン]`

---

## ステップ 11: 振り返り（retrospector、常に実行）

`retrospector` エージェントを `Agent` ツールで起動してください:

- model: `INNER_LOOP_COUNT が 0 かつ OUTER_LOOP_COUNT が 0 の場合は sonnet`、いずれかが 1 以上の場合は `opus`
- プロンプト: 以下の情報をすべて渡す
  - `PROJECT_MEMORY_DIR`
  - `PROJECT_ROOT`
  - `RUN_DIR`
  - `META_MODE=false`（/pir2 は常に通常モード。メタモードは `/retro --meta` で明示起動する）
  - `INNER_LOOP_COUNT`
  - `OUTER_LOOP_COUNT`
  - `REPLAN_COUNT`
  - `{RUN_DIR}/review-*.md` のパス一覧（retrospector が必要に応じて Read する）
  - `{RUN_DIR}/test-*.md` のパス一覧
  - 最終的な VERDICT

retrospector のレポートに「メタ改善推奨」項目が含まれていた場合、その旨をステップ12の最終サマリーに必ず転記してユーザーに通知してください（自動でメタモードは起動せず、ユーザーが `/retro --meta` を実行するかどうかを判断できるようにする）。

---

## ステップ 11.5: handoff.md 完了判定と後処理

`$HANDOFF_PATH` が存在する場合のみ実行:

1. `$HANDOFF_PATH` を Read し「残 TODO」セクションの `[ ]` と `[x]` を数える
2. 全項目が `[x]` の場合: `Bash(rm "$HANDOFF_PATH")` で削除し、最終サマリーに「🎉 handoff.md 全項目完了 → 削除済み」と記載する
3. 残項目ありの場合: `Edit` で `最終更新` 行を `YYYY-MM-DD HH:MM (run: $(basename $RUN_DIR))` に更新し、最終サマリーに「⏭️ handoff.md に未完 N 項目残置: `$HANDOFF_PATH`」と記載する

`$HANDOFF_PATH` が存在しない場合（`RESUME_MODE=passive-notice` 直後や implementer が一度も走らなかった場合など）はスキップ。

---

## ステップ 12: 最終サマリーの提示

以下の内容をユーザーに提示してください:

```
## PIR² 完了サマリー

### タスク
[タスクの説明]

### 実装記録
docs/plans/YYYY-MM-DD-<feature>.md

### 変更ファイル
[実装完了レポートから抜粋]

### レビュー結果
- 最終 VERDICT: [PASS/FAIL]
- 内側ループ回数: [INNER_LOOP_COUNT]
- [主な指摘事項があれば記載]

### テスト結果
- テスト VERDICT: [PASS/FAIL]
- 外側ループ回数: [OUTER_LOOP_COUNT]

### 再探索ループ回数
- REPLAN_COUNT: [回数]
- [ハードキャップ到達時のみ]: planner が依然追加探索を要求中: [topic 一覧]

### 作業ディレクトリ
{RUN_DIR}

### 振り返り
[retrospector の改善内容の要約]

### メタ改善推奨（retrospector レポートに含まれていた場合のみ）
[内容を転記し、`/retro --meta` の実行をユーザー判断に委ねる旨を添える]
```

---

## ステップ 13: ウォークスルーの提示

ステップ9で作成したサマリー版ウォークスルーをユーザーに提示してください。フル版は内部記録として保持し、ユーザーから「詳細を見せて」等の要求があれば提示します。

末尾に `詳細なウォークスルーが必要な場合はお知らせください。` と添えてください。
