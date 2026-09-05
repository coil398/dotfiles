# Implementation Delegation Protocol

PIR² の実装フェーズで、単一 implementer / 複数 implementer shard / main fallback を選ぶためのプロトコル。

Cursor では子担当を `Task(subagent_type=...)` で起動し、通常の Task の `model` は省略または `inherit` として親の Auto に従わせる。Cursor の agent 定義も `model: inherit` を維持し、Codex/Astra 用のモデル名や effort をここへ持ち込まない。

このファイルの `implementer-shards` と `review-fix shard` は試験実装として扱う。実験の状態、観測ログ、採用/廃止判断は `${CURSOR_SKILLS_DIR}/pir2/references/experimental.md` の `pir2-implementer-shards-and-review-fix-shards` を SSOT とし、retrospector が毎回評価・更新する。`CURSOR_SKILLS_DIR` は読み込み済みの本 `SKILL.md` の実体パスから解決し、対象アプリケーション側の固定配置を仮定しない。

## 実行形態

- `IMPLEMENTATION_ACTOR=implementer-subagent`: デフォルト。`Task(subagent_type="implementer")` 1 体が、親から渡された plan と契約に従って実装する。
- `IMPLEMENTATION_ACTOR=implementer-shards`: メインが独立 shard を plan に記載し、ゲートを全て満たした場合のみ。最大 3 体まで。
- `IMPLEMENTATION_ACTOR=main`: Task が利用できない、小変更、plan 未成熟、または shard ゲート不合格時のメイン Cursor agent fallback。

## shard 許可条件

メインが管理する `{RUN_DIR}/plan.md` に `IMPLEMENTATION_SHARDS` セクションがあり、各 shard に以下が明記されている場合のみ許可する:

- `SHARD_ID`
- 目的
- 許可ファイル/ディレクトリ
- 禁止ファイル/ディレクトリ
- 依存する shard（なければ `none`）
- （必要時のみ）親が事前に確定した成果物の種類と実在する保存先

さらにメインエージェント が以下を確認する:

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

親がその run で実際に使う値だけを渡し、存在しない path や不要な固定入力を作らない。

- `PROJECT_MEMORY_DIR`、`RUN_DIR`、`IMPL_INDEX`、plan path は、親が解決・作成し実在を確認した場合だけ渡す
- `IMPLEMENTATION_ACTOR`
- shard 実行時のみ `SHARD_ID` と許可/禁止ファイル一覧
- `HANDOFF_PATH` は resume または handoff 更新が必要で、親が安全性を確認した実在 path の場合だけ渡す
- 成果物を保存する場合は、親が事前に確定した実在する保存先だけ渡す。保存不要なら Task のチャット要約を返す
- テストスイートの実行と tester verdict は tester 専任。implementer は必要な静的検証、型チェック、ビルド、コード生成、diff 確認に留め、テスト実行を伴う生成も親が tester の範囲へ割り当てる

Cursor の native Task に、runner の schema、初期化、台帳、canonical report など別経路の契約を追加で要求しない。

## shard 統合確認

全 shard 完了後、メインエージェント は以下を実行する:

1. 親が保存した実在する `implementation-*` report があれば Read（未生成の path を作業開始条件にしない）
2. `git diff` で shard 外ファイル編集がないことを確認
3. 同一ファイル競合、命名不整合、重複抽象、未接続の実装を確認
4. 問題があれば `IMPLEMENTATION_ACTOR=implementer-subagent` に戻して統合修正する
5. 問題がなければ reviewer へ進む

## 再実装ルール

### reviewer FAIL 後

reviewer FAIL 後は、初回実装より並列修正を積極的に使ってよい。初回の `IMPLEMENTATION_SHARDS` は不要で、失敗 reviewer レポートから `REVIEW_FIX_SHARDS` をメインエージェントが組み立てる。

許可条件:

- 各指摘に具体的なファイルパスがある
- shard ごとの修正対象ファイル集合が重ならない
- 共通型、API schema、migration、lockfile、生成物、golden、共有 config、共通 helper を複数 shard が触らない
- 修正が「同じ根本原因」の別症状ではない
- reviewer の指摘内容だけで修正方針が明確

条件を満たす場合、最大 5 体まで implementer を並列起動してよい。各 shard には `REVIEW_FIX_SHARD_ID`、実在する対象 review レポート、許可ファイル、禁止ファイルを渡す。修正記録が必要な場合だけ、親が事前に確定した実在 path を渡し、不要ならチャット要約を受け取る。

条件を満たさない場合は `IMPLEMENTATION_ACTOR=implementer-subagent` に戻して、統合済み diff を単一 implementer が修正する。

### tester FAIL 後

tester FAIL 後は原則として `IMPLEMENTATION_ACTOR=implementer-subagent` に戻して統合済み diff を修正する。テスト失敗は根本原因が共有契約・状態・実行順序にあることが多いため、review-fix shard より保守的に扱う。例外として、FAIL が単一 shard の許可ファイル内に完全に閉じており、共有契約や他 shard に影響しない場合のみ、その shard だけ再起動してよい。
