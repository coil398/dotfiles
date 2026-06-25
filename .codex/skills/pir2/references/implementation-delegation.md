# Implementation Delegation Protocol

PIR² の実装フェーズで、単一 implementer / 複数 implementer shard / main fallback を選ぶためのプロトコル。

このファイルの `implementer-shards` と `review-fix shard` は試験実装として扱う。実験の状態、観測ログ、採用/廃止判断は `~/.agents/skills/pir2/references/experimental.md` の `pir2-implementer-shards-and-review-fix-shards` を SSOT とし、retrospector が毎回評価・更新する。

## 実行形態

- `IMPLEMENTATION_ACTOR=implementer-subagent`: デフォルト。`implementer` subagent 1 体が plan.md に従って実装する。
- `IMPLEMENTATION_ACTOR=implementer-shards`: planner が独立 shard を提示し、ゲートを全て満たした場合のみ。最大 3 体まで。
- `IMPLEMENTATION_ACTOR=main`: subagent 不可、小変更、plan 未成熟、または shard ゲート不合格時の fallback。

## shard 許可条件

planner の `{RUN_DIR}/plan.md` に `IMPLEMENTATION_SHARDS` セクションがあり、各 shard に以下が明記されている場合のみ許可する:

- `SHARD_ID`
- 目的
- 許可ファイル/ディレクトリ
- 禁止ファイル/ディレクトリ
- 依存する shard（なければ `none`）
- 想定成果物 `{RUN_DIR}/implementation-{IMPL_INDEX}-{SHARD_ID}.md`

さらにメイン Codex が以下を確認する:

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

全 shard 完了後、メイン Codex は以下を実行する:

1. 全 `implementation-{IMPL_INDEX}-*.md` を Read
2. `git diff` で shard 外ファイル編集がないことを確認
3. 同一ファイル競合、命名不整合、重複抽象、未接続の実装を確認
4. 問題があれば `IMPLEMENTATION_ACTOR=implementer-subagent` に戻して統合修正する
5. 問題がなければ reviewer へ進む

## 再実装ルール

### reviewer FAIL 後

reviewer FAIL 後は、初回実装より並列修正を積極的に使ってよい。planner の `IMPLEMENTATION_SHARDS` は不要で、失敗 reviewer レポートから `REVIEW_FIX_SHARDS` をメイン Codex が組み立てる。

許可条件:

- 各指摘に具体的なファイルパスがある
- shard ごとの修正対象ファイル集合が重ならない
- 共通型、API schema、migration、lockfile、生成物、golden、共有 config、共通 helper を複数 shard が触らない
- 修正が「同じ根本原因」の別症状ではない
- reviewer の指摘内容だけで修正方針が明確

条件を満たす場合、最大 5 体まで implementer を並列起動してよい。各 shard には `REVIEW_FIX_SHARD_ID`、対象 review レポート、許可ファイル、禁止ファイルを渡し、成果物は `{RUN_DIR}/implementation-{IMPL_INDEX}-fix-{REVIEW_FIX_SHARD_ID}.md` に書かせる。

条件を満たさない場合は `IMPLEMENTATION_ACTOR=implementer-subagent` に戻して、統合済み diff を単一 implementer が修正する。

### tester FAIL 後

tester FAIL 後は原則として `IMPLEMENTATION_ACTOR=implementer-subagent` に戻して統合済み diff を修正する。テスト失敗は根本原因が共有契約・状態・実行順序にあることが多いため、review-fix shard より保守的に扱う。例外として、FAIL が単一 shard の許可ファイル内に完全に閉じており、共有契約や他 shard に影響しない場合のみ、その shard だけ再起動してよい。
