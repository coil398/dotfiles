# Implementation Delegation Protocol

PIR² の実装フェーズで、単一 implementer / 複数 implementer shard / main fallback を選ぶためのプロトコル。

このファイルの `implementer-shards` と `review-fix shard` は試験実装として扱う。実験の状態、観測ログ、採用/廃止判断は `~/.claude/skills/pir2/references/experimental.md` の `pir2-implementer-shards-and-review-fix-shards` を SSOT とし、retrospector が毎回評価・更新する。

`implementer-sequential`（順序付き unit の直列 fresh 実装）も試験実装で、SSOT は同 `experimental.md` の `pir2-implementer-sequential-units`。

## 実行形態

- `IMPLEMENTATION_ACTOR=implementer-subagent`: デフォルト。`implementer` subagent 1 体が plan.md に従って実装する（model: sonnet）。
- `IMPLEMENTATION_ACTOR=implementer-shards`: planner が独立 shard を提示し、ゲートを全て満たした場合のみ。最大 3 体まで（各 model: sonnet）。
- `IMPLEMENTATION_ACTOR=implementer-sequential`: planner が `IMPLEMENTATION_UNITS` を提示し、unit ゲートを満たした場合のみ。大きいが結合していて並列 shard にできない実装を、順序付き unit に分け、各 unit を **fresh な implementer subagent で直列に**実装する（unit ごとにコンテキストをまっさらにする）。後続 unit は先行 unit の実コードを前提にできる（model: sonnet）。
- `IMPLEMENTATION_ACTOR=main`: subagent 不可、小変更、plan 未成熟、または shard/unit ゲート不合格時の fallback。スキル本体（メイン Claude）が直接実装する。

## shard 許可条件

planner の `{RUN_DIR}/plan.md` に `IMPLEMENTATION_SHARDS` セクションがあり、各 shard に以下が明記されている場合のみ許可する:

- `SHARD_ID`
- 目的
- 許可ファイル/ディレクトリ
- 禁止ファイル/ディレクトリ
- 依存する shard（なければ `none`）
- 想定成果物 `{RUN_DIR}/implementation-{IMPL_INDEX}-{SHARD_ID}.md`

さらにスキル本体（メイン Claude）が以下を確認する:

- 許可ファイル集合が shard 間で重ならない
- 共通型、API schema、migration、lockfile、生成物、golden、共有 config、共通 helper を複数 shard が触らない
- shard 間に実装順序依存がない
- 片方の命名・抽象・データ形状をもう片方が前提にしない
- 統合後に単一 reviewer/tester ループで全体確認できる

1 つでも欠けたら `implementer-shards` は使わず `implementer-subagent` に戻す。

## 禁止パターン

- 同一ファイルまたは同一ディレクトリ配下の近接コードを複数 shard が編集する
- DB/API/domain model/schema など中心契約を複数 shard が触る
- codegen/golden/snapshot/lockfile の更新が複数 shard にまたがる
- 「まず A が抽象を作り、B がそれを使う」のような順序依存がある
- shard の境界が機能単位ではなく作業量だけで分けられている

## implementer プロンプト共通項目

- `PROJECT_MEMORY_DIR=[パス]`
- `RUN_DIR=[パス]`
- `IMPL_INDEX=NN`
- `{RUN_DIR}/plan.md` のパス
- `IMPLEMENTATION_ACTOR`
- shard 実行時のみ `SHARD_ID` と許可/禁止ファイル一覧
- `HANDOFF_PATH=$HANDOFF_PATH`（`RESUME_MODE` が `new` または `resume` の場合）
- 「実装完了レポート本体は `{RUN_DIR}/implementation-{IMPL_INDEX}.md`、shard 実行時は `{RUN_DIR}/implementation-{IMPL_INDEX}-{SHARD_ID}.md` に書き出し、チャットには要約のみ返してください」
- 「テストスイート実行は tester 専任。静的検証、型チェック、ビルド、コード生成、diff 確認までに留める。`make golden` などテスト実行を伴う生成も tester に委ねる」

## shard 統合確認

全 shard 完了後、スキル本体（メイン Claude）は以下を実行する:

1. 全 `implementation-{IMPL_INDEX}-*.md` を Read
2. `git diff` で shard 外ファイル編集がないことを確認
3. 同一ファイル競合、命名不整合、重複抽象、未接続の実装を確認
4. 問題があれば `IMPLEMENTATION_ACTOR=implementer-subagent` に戻して統合修正する
5. 問題がなければ reviewer へ進む

> ℹ️ ここ（6-2）は shard/unit 境界の **LLM 層の整合レビュー**（命名不整合・重複抽象・未接続の検出）。申告集合 vs 実 git diff の **決定論的 claim-vs-diff 集合照合**（PHANTOM_CLAIM / UNDECLARED_CHANGE）は 6-3（`~/.claude/skills/pir2/references/deterministic-completion-check.md`）が担い、デフォルト actor（pir2 の implementer-subagent）および Codex actor（pir2codex）を含む全実装 actor に適用する。6-3 は本節（shard/sequential 限定）の「一般化」であり、両者は別レイヤーで補完し合う。

## implementer-sequential（順序付き unit の直列 fresh 実装）

`implementer-shards` が「独立・並列」なのに対し、`implementer-sequential` は「結合・直列」。大きいが順序依存や共有契約のため並列分割できない実装を、planner が `IMPLEMENTATION_UNITS` で順序付き unit に分け、スキル本体（メイン Claude）が **unit ごとに新しい implementer subagent を直列に起動**する。各 implementer は fresh context で起動するため、1 体が plan 全体を抱えて後半 unit の品質が落ちる（context-rot）のを避けつつ、並列 shard の統合 divergence も避ける中間モード。

### unit 許可条件

planner の `{RUN_DIR}/plan.md` に `IMPLEMENTATION_UNITS` セクションがあり、各 unit に以下が明記されている場合のみ許可する:

- `UNIT_ID`（`UNIT_1` / `UNIT_2` … 実行順を表す）
- 目的
- 主対象ファイル（後続 unit と重複してよい）
- 依存する先行 unit（なければ `none`）
- 想定成果物 `{RUN_DIR}/implementation-{IMPL_INDEX}-unit-{UNIT_ID}.md`

さらにスキル本体（メイン Claude）が以下を確認する:

- 実装規模が「大きい」（複数機能・多ファイル横断・大きな diff のいずれか）。小さい実装は単一 `implementer-subagent` に倒す
- unit を順序通りに直列実行すれば成立する（先行 unit の成果物に後続が乗る形になっている）
- `IMPLEMENTATION_SHARDS` と同時に提示されていない（独立なら shards、結合なら units の二択）
- 各 unit が「意味のある境界」で切られている（作業量だけで機械分割していない）

1 つでも欠けたら `implementer-sequential` は使わず `implementer-subagent` に戻す。

> ℹ️ shards と違い unit 間でファイルが重なってよい（直列なので write 衝突が起きない）。独立分割できるなら待ち時間の短い `implementer-shards` を優先し、`implementer-sequential` は「大きいが絡んでいて並列にできない」ケースの受け皿とする。

### 直列実行プロトコル（handoff）

unit を `UNIT_ID` の昇順に 1 体ずつ実行する（先行 unit の完了を待って次を起動）。unit K の implementer を起動するとき、「implementer プロンプト共通項目」に加えて以下を渡す:

- `UNIT_ID` と当該 unit の spec（目的・主対象ファイル・依存先）
- **完了済み unit の `{RUN_DIR}/implementation-{IMPL_INDEX}-unit-*.md` パス一覧**（implementer が Read して先行成果を把握する）
- 「起動後にまず `git diff` で先行 unit の変更を確認し、先行 unit の命名・抽象・データ形状に従うこと。逸脱が必要なら実装完了レポートの『注意点・未解決事項』に理由を記載すること」
- 成果物は `{RUN_DIR}/implementation-{IMPL_INDEX}-unit-{UNIT_ID}.md` に書き出させる

fresh subagent でも先行 unit の実コードを Read して接続できるため、直列でも一貫性を保てる（これが直列モードの肝）。

### unit 統合確認

全 unit 完了後、スキル本体（メイン Claude）は以下を実行する:

1. 全 `implementation-{IMPL_INDEX}-unit-*.md` を Read
2. `git diff` で unit 境界をまたぐ命名不整合・重複抽象・未接続の実装がないか確認
3. 問題があれば `IMPLEMENTATION_ACTOR=implementer-subagent` に戻して統合修正する
4. 問題がなければ reviewer へ進む

> ℹ️ ここ（6-2）は shard/unit 境界の **LLM 層の整合レビュー**（命名不整合・重複抽象・未接続の検出）。申告集合 vs 実 git diff の **決定論的 claim-vs-diff 集合照合**（PHANTOM_CLAIM / UNDECLARED_CHANGE）は 6-3（`~/.claude/skills/pir2/references/deterministic-completion-check.md`）が担い、デフォルト actor（pir2 の implementer-subagent）および Codex actor（pir2codex）を含む全実装 actor に適用する。6-3 は本節（shard/sequential 限定）の「一般化」であり、両者は別レイヤーで補完し合う。

> ℹ️ v1 では `implementer-sequential` は**初回実装のみ**に適用する。reviewer / tester FAIL 後の再実装は、統合済み diff に対する下記「再実装ルール」（review-fix shard または単一 implementer）に従う（unit 単位での再実装はしない）。

## 再実装ルール

### reviewer FAIL 後

reviewer FAIL 後は、初回実装より並列修正を積極的に使ってよい。planner の `IMPLEMENTATION_SHARDS` は不要で、失敗 reviewer レポートから `REVIEW_FIX_SHARDS` をスキル本体（メイン Claude）が組み立てる。

許可条件:

- 各指摘に具体的なファイルパスがある
- shard ごとの修正対象ファイル集合が重ならない
- 共通型、API schema、migration、lockfile、生成物、golden、共有 config、共通 helper を複数 shard が触らない
- 修正が「同じ根本原因」の別症状ではない
- reviewer の指摘内容だけで修正方針が明確

条件を満たす場合、最大 5 体まで implementer を並列起動してよい。各 shard には `REVIEW_FIX_SHARD_ID`、対象 review レポート、許可ファイル、禁止ファイルを渡し、成果物は `{RUN_DIR}/implementation-{IMPL_INDEX}-fix-{REVIEW_FIX_SHARD_ID}.md` に書かせる。全 review-fix shard 完了後、スキル本体（メイン Claude）は「shard 統合確認」と同じ手順（全 `implementation-{IMPL_INDEX}-fix-*.md` を Read、`git diff` で shard 外編集・同一ファイル競合・命名不整合・未接続実装を確認、問題があれば `implementer-subagent` に戻して統合修正）を実施してから再 reviewer に進む。

条件を満たさない場合は `IMPLEMENTATION_ACTOR=implementer-subagent` に戻して、統合済み diff を単一 implementer が修正する。

### tester FAIL 後

tester FAIL 後は原則として `IMPLEMENTATION_ACTOR=implementer-subagent` に戻して統合済み diff を修正する。テスト失敗は根本原因が共有契約・状態・実行順序にあることが多いため、review-fix shard より保守的に扱う。例外として、FAIL が単一 shard の許可ファイル内に完全に閉じており、共有契約や他 shard に影響しない場合のみ、その shard だけ再起動してよい。
