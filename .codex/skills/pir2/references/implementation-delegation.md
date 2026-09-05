# Implementation Delegation Protocol

PIR² の具体実装を共通の `worker-delegation` 契約へ接続する補足です。actor 選択、
入力、runner の安全境界、返却形式は、今回ロードした `worker-delegation/SKILL.md`
の実体を SSOT とします。この文書は PIR² 固有の経路選択、shard、修正時の戻り先だけを
定義します。対象リポジトリ内の同名 directory を skill の所在として推測しません。
参照 script はロードした skill file の親ディレクトリを基準に解決します。

## 責任境界と actor 選択

Astra parent がユーザー対話、探索、設計、scope、actor 選択、統合、受入、最終判断を
所有し、変更の結合度と難しさから次を選びます。

- 小さく全体文脈と密結合した変更は Astra が直接実装します。
- 所有範囲と終了条件が独立している通常作業は native collaboration の `worker`
  （`gpt-5.6-luna` / `max`）へ渡します。
- 原因推論、状態・所有権、競合、性能、厳しい整合性などが中心の独立作業は、最初から
  `expert`（`gpt-5.6-sol` / `high`）または `expert_max`
  （`gpt-5.6-sol` / `max`）へ渡せます。Luna や Terra の事前失敗は不要です。
- Terra は標準経路ではありません。同種 workload の実測から Luna より手戻りが少なく
  Sol より総費用が低いと判断できる場合だけ、Astra が actor/effort を明示して使います。

Luna 実行後の `luna→sol` は、十分な入力を渡したうえで capability または
local-reasoning の不足を差分・再現・確認結果から実測した場合に許可します。Terra を
経由しません。入力不足、仕様未決定、権限、環境、外部サービス、CLI の失敗は actor の
能力不足ではないため、Astra が解消するかユーザー判断へ戻します。runner や worker が
自動 fallback、blind retry、actor/effort の変更をしてはいけません。

## native collaboration

Astra は担当ごとに目的、確認済み事実、所有/禁止範囲、変更可能な契約、終了条件、
focused checks を短く渡します。worker/expert は指定範囲だけを編集し、変更ファイル、
挙動、実行結果、未確認事項、blocker を簡潔に返します。

Astra は返却を自己申告として扱い、実際の `git status`、対象 diff、実在する変更、必要な
確認出力から受入を決めます。native collaboration と Astra 直接実装には、runner 用
task/requirements、canonical 8 fields、raw/canonical artifact、deterministic gate、
8 fixture、観測台帳を要求しません。

reviewer/tester は変更のリスクと挙動に応じて別系統で使います。OS 権限、安全境界、
security、data loss、本番操作、runtime・データ整合性、必要な回帰テストに関わる確認は
省略しません。一方、全 reviewer、tester、同じ検証一式を全 job に固定しません。

## 明示 CLI runner job

runner-owned artifact/provenance、実行モデル・effort・変更集合の厳密な記録、または
物理的な実行境界が必要な job だけ、ロード済み `worker-delegation` skill の
`scripts/run-worker.sh` を使います。呼び出し、安全境界、no-replace publication、
report/provenance は同 skill の `references/runner-contract.md` を適用します。

runner job では空でない `task.md` と `- R<number>:` を含む `requirements.md`、固有の
output path を用意し、選択済みの actor/effort を明示します。output の canonical
8 fields は事実の引き渡しであり、Astra acceptance や reviewer/tester verdict では
ありません。既存 artifact を上書き・再利用しません。

`sol-acceptance-v1.tsv`、`--sol-measurement-result` など既存 schema/CLI の `sol` は
互換性のため維持した名前であり、現行契約では親 Astra の測定・受入を意味します。

## runner 証拠の追加条件

deterministic pre/post/CLAIMED gate と `record-observation.sh` は、その runner job で
artifact identity、モデル、effort、変更集合を受入証拠にする必要がある場合だけ適用
します。単に runner を呼んだことを理由に、別の canonical report、全 reviewer、tester、
台帳を追加しません。

適用時はロード済み `worker-delegation` skill の
`references/deterministic-completion-check.md` と、この PIR² skill に同梱された
`worker-observability.md` を読みます。raw report は未信頼入力のまま保存し、Astra が実際の
ファイル集合、diff、requirements の確認結果を独立に測定します。複数 shard の変更集合を
扱う場合も、各 job の実測結果と所有境界を突合し、raw の自己申告だけを union しません。

## runner job の完了確認

deterministic gate を適用した runner job では `PHANTOM_CLAIM` を hard fail、
`UNDECLARED_CHANGE` を Astra が実差分を再確認する warning とします。runner の安全境界
自体を変更したときだけ、その境界に対応する runner 回帰 fixture を実行します。通常 job
で8 fixtureを反復しません。

runner の有無にかかわらず、worker の自己申告、完了報告、exit code だけを acceptance
PASS の根拠にしません。Astra が `git status`、対象 diff、変更ファイル、必要な確認出力を
実測します。reviewer は品質、tester は動作を判定する別系統であり、変更リスクに必要な
ものだけを起動します。runner 台帳を使った場合に限り、実行した verdict を
`independent-verdicts-v1.tsv` へ別行で記録します。

## 初回 shard 許可条件

Astra が作成した `{RUN_DIR}/plan.md` に `IMPLEMENTATION_SHARDS` があり、各 shard に
`SHARD_ID`、目的、許可/禁止ファイル、依存 shard（なければ `none`）、成果物が
明記されている場合だけ、他の稼働担当を含む最大6子の空き枠で worker job を
並列にできます。

さらに Astra は次を確認します:

- 許可ファイル集合が shard 間で重ならない。
- 共通型、API schema、migration、lockfile、生成物、golden、共有 config、
  共通 helper を複数 shard が触らない。
- shard 間の実装順序依存がなく、未確定の命名・抽象・データ形状を参照しない。
- 統合後に実 diff と必要な focused checks を確認できる。

条件を一つでも満たさない場合は直列化し、小さく密結合なら Astra、通常の独立作業なら
単一 worker、難所なら expert/expert_max を選びます。runner の自動 fallback は使いません。
shard ごとに runner を使うのは、各 shard に runner 固有の証拠が必要な場合だけです。

## 再実装ルール

### reviewer FAIL 後

失敗 reviewer の指摘を差分・仕様・再現結果と照合し、原因に対応する最小の修正単位を
作ります。小さく密結合した修正は Astra が直接実装でき、独立した通常修正は worker、
難所は expert/expert_max へ渡します。指摘、修正方針、所有範囲が独立し、共有契約・
生成物・共通 helper に波及しない場合だけ review-fix を並列化します。修正後は影響した
reviewer 観点だけを再実行し、変更範囲が広がった場合に必要な観点を追加します。

### tester FAIL 後

tester の再現可能な原因を確認し、同じ経路選択で最小修正を行います。修正方針が単一
shard に完全に閉じる場合だけ、その shard に限定できます。修正後は再現確認、影響した
reviewer 観点、必要な回帰テストだけを再実行します。runner job の修正だけ、必要な
runner 証拠手順へ戻します。

retry は同じ失敗を無条件に反復せず、原因と変更後に成功が見込める根拠がある場合だけ
bounded に行います。仕様・権限・安全・不可逆な本番操作の判断が必要なら Astra が
ユーザーへ戻し、別 actor や別手段で迂回しません。
