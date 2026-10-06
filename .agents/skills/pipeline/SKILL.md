---
name: pipeline
description: >-
  ステージ型パイプライン（declared inputs → declared outputs の実行単位を繋ぐ構成）と
  その監視ダッシュボードの設計・構築・運用・改善の約束。パイプラインを作る
  （DAG 設計・stage 追加・component 化）・回す・形を変える・resume する・
  失敗を分類して直す・lab で計測改善する・監視 UI を作る・監視側と実行状態を
  同期する、といった作業全般に使う。特定のリポジトリやドメインに限定しない。
  ユーザーが /pipeline と入力したら使う。
---

# /pipeline — ステージ型パイプラインと監視ダッシュボード

複数の LLM / 外部サービス / 決定的処理を繋ぐパイプラインで、繰り返し躓いた構造的判断の正本。
実装仕様は各リポジトリのコードと SSOT に残し、ここには **どんなパイプラインにも効く約束** を書く。

## パイプラインの最小正典

- **各 stage は declared inputs → declared outputs の実行単位**。完了トリガーは実行の終了（exit / `.done` 中継）だけ
- **LLM・worker はパイプラインを制御しない**。verdict 解釈・次段起動・収束・blocked 判定はエンジンが機械的に行う。プロンプト内の LLM 判断にフロー制御を委譲しない
- **transport は adapter であり契約ではない**（CLI spawn / bridge 中継 / SDK 呼出し）。特定ランタイム専用の機構を stage 契約や resume 規則に組み込まない。run 途中で transport を差し替えても成果物契約だけで継続する設計が健全（実測: 同一 run 内で 3 transport を横断して収束）
- **直列化・並列化は engine の責務**。stage 側は自分の I/O だけを知る
- **semantic stage と deterministic stage を分離する**。生成・意味・品質判断など規則化できない部分を LLM に残し、入力解決・依存追跡・再利用・集計・遷移・再試行はプログラムで決定する。LLM は recommendation を出し、最終決定（集計・publish 可否・receipt 発行）は決定的 stage が担う

## 止まってよいのは2つだけ

1. **品質 verdict**（FAIL 系 — コンテンツ判定・検証結果）
2. **human-gate の実承認待ち**

それ以外 — hash・fingerprint・provenance・証跡一致の不一致、照合不成立、改ざん検知、transport 障害 — は **メタデータ記録**であって停止理由にしない。

成果物の再利用可否は2分岐のみ:

- 存在し、記録が現行定義と整合 → 黙って再利用
- 不在・不整合・判定不能 → 黙って当該スコープを再実行（入力が変われば下流へ連鎖）

**なぜか**: 失敗のたびに照合・証明・承認ゲートを足すと、resume 機構が膨張して「普通の運用で止まるパイプライン」になる（実測例: resume 機構が 403→1,724 行に膨張、「証跡がずれた」だけで resume が起動後 0 秒死を繰り返した）。この層を**官僚ゲート**と呼び、新設・維持を禁止する。削除しても別層で再燃し得る — 「コードを1行直しただけで run が死ぬ」「本文は完成しているのに resume が殺される」兆候を見たら全層を洗い直す。照合系の検査は resume 経路ではなく CI に寄せる。

**settle の意味を一箇所に固定する**。「葉 stage が COMPLETED」を run 完了に写さない（**偽 COMPLETED**。手で report を直しても次の葉で再発する）。完了の定義は「最終成果物イベントが journal にあり disk に実体がある」に統一する。

## パイプラインの作り方（DAG 設計と component 化）

### 宣言・解決・実行の3層を分ける

「型ごとに形が違う」は実行グラフの問題ではなく **宣言の編成** の問題として扱う:

- **宣言層**: flat な node リスト（`id`/`kind`/`dependsOn`/`roleRef`/`outputs`）+ 型別 parameters（`enabled`・`roleRef`・`outputArtifactIds`・`mode`・fanout 数）
- **解決層（compiler）**: parameters を型・variant で解決して不要 node を prune し実行グラフを生成。宣言と写像の不一致は exact 検証で fail-closed（黙って無視しない）
- **実行層**: engine は compile 済みグラフだけを見る。型やドメインの知識を持たない

この構造があると「形を変える」は宣言層だけの作業になる（実例: 82 ノード宣言が型解決で 44 ノードの実行グラフに prune される）。直列化・fanout・loop の機構は engine 側で共有され続ける。

### 単一 DAG + 型別 prune vs 別 DAG

- **分離してよい層**: 宣言の編成。大きくなったら fragment + composer で型ごとの flat DAG を生成してよい — 出力が同じ flat DAG なら engine・bindings・resume・correction・validator がすべてそのまま生きる
- **分離してはいけない層**: engine・artifact binding・resume・correction machinery・verdict 語彙・成果物命名規約。複製すると drift しか生まない（実例: 別契約 schema + 独自 runner/resume に分岐した系列は「2つ目の契約宇宙」になり、契約の二重ミラーで形状変更のたびに run が死んだ）
- **型別 DAG 化の等価性条件**: 型別に生成した compile 結果（位相順序 + binding 集合）がモノリス + 型別パラメータの compile 結果と一致すること — 「正しい分離」の唯一の客観的定義
- **component 境界は「変動点 × correction-loop 閉包」で引く**。loop をまたぐ境界分割は reentry 経路を壊す。典型境界: 共有 entry → 型固有 producer（interface 成果物だけ固定し producer 名は変えてよい）→ 共有閉包（fanout→synthesis→critic→patch の loop が閉じる単位を割らない）
- **生成物はチェックイン + CI regen-diff 検査**。共有 component を直すと全型に波及するので「生成せず手で育てる」運用は drift で死ぬ
- **分離の動機を実測で確認する**: 「その型の失敗」が DAG 形状起因でない（timeout policy・stage 実行問題等の）実測があるなら、構造分離は over-scope

### fanout / variant / provided input の3パターン

- **fanout（数が決まっている並列）**: shard 配列（`ordinal`/`identity`/`profileRef`/`artifactId`）+ 「数 → artifactId リスト」の逆引き表（cardinalityOutputs）を宣言し、compiler が個数と集合の exact 照合で fail-closed
- **variant（同型の異種）**: variant → 入力 artifactIds のマップを宣言し、variant 必須・未知値拒否を compiler が検証
- **provided input（外部供給）**: producer stage を起動せず外部 artifact だけで入力 contract を満たすモード。別パイプラインの産物を入力にする「入力提供のみの component（ノードなし）」を宣言だけで表現できる。compiler は producer が binding に含まれないことで非起動を検証する
- 条件付きグループはグループレベルの `when` 式で宣言（compiler が `when` を exact 文字列で受理）

### correction loop の設計不変条件

- **forward DAG と back-edge を分離**: `dependsOn` は DAG（非巡回）のまま、再入場は loop メタデータだけで表現。DAG に直接 back-edge を書かない
- **loop 宣言の完全な要素**: owner（判定を出す node）・decisionSource（owner 出力への参照）・transitions（verdict → reentryTarget）・counterRef（上限パラメータ参照）・onExhaustion・coversGates・priority
- **bounded**: `maxRounds` は有限、`onExhaustion` は stop（使い切りで強制 PASS にしない）。ラウンド証拠は `toRound = fromRound + 1` で owner/verdict/contentHash の整合を検証
- **生成 stage は establish-once**: 最初に産物を作る stage（writer 等）は correction loop の再入場先にしない。修正は専用 patch stage への reentry。validator + check script + runtime supervisor の多層で強制する（実例: writer/初期 fanout への reentry を 3 層で fail-closed）
- **evidence の閉包**: 各 loop の再入場が必要とする前ラウンド成果物を `loopId | reentryTarget | previousRoundArtifactId | transitionVerdict` の binding で宣言し consumer を exact 指定。round 1 は「前ラウンドなし」sentinel、round 2+ は直前ラウンド snapshot 必須、fanout 時は全 shard が同一 evidence を入力
- **patch が「全部書き直し」しない仕組みを用意する**（whack-a-mole の発生源。計装層の節を参照）

### stage を追加するときの全登録面

stage・role・artifact の追加は「1ファイル宣言」では済まない。健全なパイプラインでは **契約が複数の検証層でミラーされている** — どれか一つ抜けると compile か CI で fail する設計が正常。一般形:

1. workflow 定義に node 追加（`id`/`kind`/`dependsOn`/`roleRef`/`outputs`）
2. 宣言パラメータ: 型定義（`enabled`/`roleRef`/`outputArtifactIds`）、artifact manifest（物理パターン・最低件数・schemaId・条件付きマーカー）、型の artifactSet 参照
3. 入力契約: consumer 側の requiredArtifactIds、条件付き入力は `when` 式 + 解決先 ref
4. compiler: resolver 分岐・active artifacts 分岐・manifest conditional の skip・conditional 入力の受理
5. 論理出力 → 物理 artifact の binding。決定的 producer なら producer 定義 + operationId の用途別リスト登録
6. contract catalog（contractId/nodeId/roleRef/入出力/schemaId/適用型）
7. **role 追加なら role ファイル + manifest/catalog の両方**。片方だけでは解決しない。missing/empty role は fail-closed
8. semantic-oracle（正準入力集合の期待値）と CI check スクリプト — 両方がミラー層
9. mutation test・compiler test（enabled/disabled/不正 override/未知参照の pin）
10. **fixture・lab case・docs の同期** — params 変更はテスト fixture や lab case の複製にも波及させる

correction loop に関与するなら correctionLoops + reentryBindings + evidenceConsumers も。フェーズ名を消費するもの（detect-phase・進捗集計・dashboard）があればそれも登録面。

## 失敗の分類（再発時はまず型を特定する）

| 型 | 症状 | 構造的原因 | 正しい対処 |
|---|---|---|---|
| 官僚ゲート | 証跡・pin・fingerprint 不一致で resume・進行が殺される | 照合を admission gate 化 | 照合は記録のみ。品質 verdict と human-gate だけが止まれる |
| whack-a-mole | patch が全部書き直す → 前回の指摘が別の形で再発 → FAIL が無限供給 | 修正に必要な情報が不足（mustFix の機械列挙・mustPreserve・台帳がない） | retry やゲート追加ではなく **情報層**で担保: 機械列挙・保存契約・closure attestation・差分計測 |
| transport 障害 | `RESULT_NOT_SUBMITTED`・timeout・worker 消失・spawn ハング | adapter 層の障害を stage 失敗と混同 | stage 失敗として記録し resume で再 dispatch。契約に transport を混ぜない |
| evidence 死 | 前ラウンドの成果物が構造的に参照されない（静的展開と staleness 判定の衝突など） | データフローと証跡解決の不整合 | aggregate の inputHashes → 実ファイル hash 逆引き等、実測で証跡を辿る |

追加の障害パターン:

- `.done` を worker が早期に書く → 下流が途中状態を読む競合（「完了してから書く」契約を明示）
- structured result schema への過度な依存 → 本文が妥当でも FAIL（salvage 経路を用意）
- dev server 偽陽性 → 本番 bundle（`vite preview` 相当）で検証する
- 大きな成果物の一括書き込み → kill で途中切断、不正 JSON が残る（小分け書き込み＋読み直し検証）
- 親子 run で occupancy/lease が「途中 state を新規起動から塞ぐ」→ stale RUNNING や ABANDONED が溜まる。occupancy 判定と掃除規約を決める
- **外部 quota 枯渇は transport 障害と分けて記録する**。429/rate-limit 系は「一定時間 retry しても無駄」な時間窓の失敗 — 連続するなら provider の usage endpoint で残量層（5h/週/月など）を直接確認してから再開間隔を決める。retryable として放置すると bounded retry を燃やし尽くすだけ（実例: OpenCode Go `GoUsageLimitError`、週次 100% で ~6日停止）

## resume の契約

- resume は **現行の宣言で live 再コンパイル**する設計が主流。run 途中に宣言を変えると **新しい形で続行**される — workspace 内の宣言スナップショットは再コンパイルに使われない
- 起動フラグ一式を再指定する（`--run-id` だけでは起動しない実装が多い）
- worker 消失・kill・transport 障害は stage 失敗として記録 → resume で同一 prompt の再 dispatch（prompt は byte 一致で再生成されるのが望ましい — 番号・内容が同じなら中断前と同じ dispatch を再発行できる）
- **再利用は評価対象だけでなく消費した全入力に紐付ける**: 本文・計画・採用条件・未解決事項・role/審査基準など判定に使う入力と版を宣言し、実際の消費記録と一致させる。評価対象と消費版は成果物メタに永続化し、resume で復元できないプロセス内フラグを正本にしない。engine が入力・定義の変更を検知し、影響 stage と下流だけを再計算する。同じ入力なら再利用、不整合・判定不能なら対象を再実行する。再利用可否を LLM に判断させず、本文だけの版比較・無意味な本文変更・全工程の巻戻しで代用しない。旧判定は履歴として保持し、現行入力に対応する判定だけを集計する。回帰確認は入力不変の再利用、本文以外の依存入力変更による再審査、無関係入力変更の非波及を含む
- 成果物契約は「存在する」→「**存在しパース可能**」に引き上げる。不正な成果物が残ると resume しても同じ箇所で再クラッシュする無限ループになる
- resume cursor（metrics 等）の破損は空 cursor へ degrade + WARN（kill が write 中に刺さると truncated JSON が残る）
- positional な dispatch 番号を使うなら、同名の `.done`/`.result` は dispatch 開始時に除去する（前回試行のシグナルで即時 resolve して worker が走らない）
- **状態イベント store は append-only + immutable segment + 増分 replay にする**。「node 実行ごとに全イベントを再読する」構造は O(nodes×events) で、数千イベント級になると RSS が GC 上限に張り付き実質停止する（実測: 8000ファイル/110MB を毎回再読で 4.5 時間空転 → revision-keyed キャッシュで 483ms→6ms）。イベントを `Object.freeze` しておけばキャッシュ共有も安全
- **resume boundary が期待する nodeId と compiler が emit する nodeId を同じ座標語彙で書く**。「sealed tip の直下に `patch:rN`」を期待するのに compiler が selector 分岐（`:waive:`/`:reverify:`）経由でしか emit しない、のような語彙のズレは「graft 不発 → replay だけ空転 → BLOCKED 固定」の直接原因になる。継続 continuation は「journal の最深実在トークン（selector 分岐を含む）」を tip として派生させ、期待 node が compile 済みグラフに実在することを compile 時に検証する
- **「前提条件の達成」を「スキップ条件」に流用しない**。「salvage 完了済みなら return」が「salvage 完了後にだけ発火する reconciliation」を恒久的に殺した実例がある — early-return のガード対象と、機構の発火前提が同じ出来事を指していないか確認する
- 合成 resume: run dir をコピーして成果物を置くだけで resume 対象になる設計にしておくと検証が楽
- **scope 指定 resume の識別子はバイト厳密一致**。node instanceId（座標語彙を含む長大な ID）はイベントログから機械抽出して渡す — 手転写で `:`→`/` を1箇所潰すと、scope が何も警告なく unmatched になって全 composite が replay されるだけの静黙不発になる。scope 要求の受理時と settle 時に durable イベント（受領 ID 一覧・matched/unmatched + 最近傍候補）を残すと転写ミスが即座に可視化される
- **死んだ RUNNING attempt の回収 close-out は専用の遷移 identity で書く**。回収用の `RUNNING→FAILED_RETRYABLE` を新しい代替 attemptId で書くと、直後の dispatch 失敗が同じ attemptId・同じ edge を書いて idempotency 衝突で wedge する。かといって previousAttemptId 帰属は、過去の誤帰属 edge が残ると再衝突する。`<attemptId>:recovery-close` のような hop ごと一意の scope id で記録し、実装固有の詳細と回帰テストは対象プロジェクト側で管理する。
- **quota が乏しいときは resume scope を失敗 leaf に絞る**。広い scope は配下の全 descendant を force-rerun するため、成功するはずの上流 stage が貴重な quota 枠を先取りし、真に必要な失敗 stage が饿死する（実測: evidence が毎 hop 完走して plan が永遠に 429）
- **自動 resume 分岐は全て durable な発火イベントを出す**。複数の recovery 経路が存在する runner で「どの分岐が resume を横取りしたか」が静黙だと、resumeFrom が届いているのに scope 不発のような不可解な状態になる。入口で recoveryReason を記録するだけで全分岐をカバーできる

## 品質ゲートの分類（blocking / advisory）

- **常に blocking**: 数値・算術不整合、主張の内部矛盾・因果混同、根拠なき断定・出典偽装、必須契約違反、保存対象（mustPreserve）の破壊
- **advisory**（pass-with-known-issues 相当で通過可）: 文体・リズム・生成物らしさ、読者好み、消費側 accessibility、改善提案
- 「指摘ゼロの FAIL」を許容判定に降格しない。pass-with-known-issues を完全失敗と同一視しない
- 決定的 checker（export 整合・数値 SSOT・必須構造）が final publish ゲートに向く。LLM verdict は upstream の修正信号としては有効でも、skip・forced-pass・監査タイミング起因で実効性が揺らぐことを実測済み

## パイプラインの改善の仕方

### 回しながらテストし、実測で改善を決める

改善は「止まって相談」ではなく **実行中の計測ループ** で決める:

- **run を止めずに診断する**。stage が失敗・停滞していても journal / gateway-events / reservation / shadow 成果物は読める。まず実物の状態を見てから動く
- **孤立 probe で再現する**。本 run の retry を浪費する前に、失敗した stage と同じ入力・role・出力契約を gateway に直接流す最小再現を組む（実例: 実 role md + 実 staged inputs を `gateway.run()` に渡すプローブ。RESULT_NOT_SUBMITTED 系は `error.diagnostics` の assistantTextPreview / finishReason / executedToolCount に生存情報が入る）。本パイプラインを回さず失敗型を確定できる
- **対照実験で切り分ける**。同じ endpoint で「小さい write_output」「大きい write_output」「別タスク」を流して、契約・payload サイズ・タスク形状のどれが原因かを潰す
- **同型失敗が3連続したら構造問題として扱う**。stochastic retry に賭けず、タスク形状・契約・経路のどれかを変える（実例: endpoint が `<|DSML|>` markup を漏らし tool call が degenerate 化 → 4 連続空 submit で endpoint 限界と判定）
- **改善するかどうかも実測で決める**。「直せるか」を推測や確認ではなく、小さい実験の成否で判定してから本線に適用する

### lab / shadow 経路を用意する

- **production 正本と実験 snapshot をバージョン分離**（case = 入力一式 + role/プロンプトセットのバージョン dir）。同じ case で role・計装の差分を A/B 計測し、品質退化なしを確認してから本番に port する
- lab の run は production と同じ stage 契約・同じ resume 規則で動かす。lab だけ別機構にすると「lab で通って本番で死ぬ」になる
- **失敗した実 run を lab case に fixture 化する**。失敗資産が計測基盤に還流する構造を作る（実例: 実運用の失敗ケースを lab の case として再現・修正検証）

### 収束を止めるのは retry ではなく情報層

whack-a-mole（patch が全部書き直す → 前回の指摘が別形で再発 → FAIL が無限供給。実測 49 ラウンド BLOCKED）の根治は「情報層」:

- **mustFix の機械列挙**: 「見つけたら直せ」ではなく、エンジンが FAIL 成果物から blocking 指摘を抽出して patch へ列挙注入。列挙外の suggestions・自由記述を変更入力にしない（「走査せよ」→「見つけた全箇所を列挙せよ」の言い換えが効いた実績）
- **mustPreserve 台帳**: PASS 観点・保存条件を累積台帳化し、patch が触れるなら両条件を満たす統合を要求（ついで直しの禁止）
- **closure attestation**: findingId ごとの RESOLVED/UNRESOLVED を成果物に書かせ機械が集計
- **patch 差分計測**: changeRatio（変更行比率）で「外科修正か全部書き直しか」を数値化（健全な外科修正の実測値は 0.01〜0.17）
- **退行スキャン**: 前ラウンド PASS の軸は全量再レビューではなく差分走査で済ませる（時間短縮と PASS→FAIL 退行の計測を両立）
- **判定不能は収束に数えない**: verdict 解析不能・dispatch 失敗の軸があるラウンドは「未完」として resume で欠けた軸だけ再 dispatch

### 計測すべき収束形状

ラウンド数・mustFix 件数・resolved / unresolved / regressed・patchChangeRatio・軸の PASS→FAIL 退行数。「収束したか」ではなく「**何ラウンドで・退行ゼロで・未解決ゼロで収束したか**」を見る。run 間のばらつき（mustFix 6→4→7 で収束形状が同じ）は正常。

- **検証は本番と同じ経路で**: dev server の偽陽性は本番 bundle で排除、図・画像は機械検査と別に実画像目視
- **失敗の情報を stage に流す**: retry 時は detailCode → 修正指示の対応表を prompt に注入し、feedback は上限 bounded にする

### transport の堅牢化

- timeout は「即 resolve(error) → grace → プロセスグループ kill」。SIGTERM を無視する worker で永久ハングし、孫プロセスが stdout pipe を握ると子が死んでも EOF が来ない（実測で発生）
- ハーネス差し替え（CLI→bridge→別 CLI）で成果物契約だけで継続できることを確認しておくと、provider 障害時の復旧が「別 transport で resume」になる
- `.env` は export なしなら `set -a; source .env; set +a` が必要（単純 source では子に届かない）

## 監視ダッシュボードの作り方

### アーキテクチャ: 単一 snapshot API への一本化

- **観測データの単一契約を1本の snapshot エンドポイントに集約する**。サーバがファイルシステム・プロセス・ログを一括走査して 1 JSON を返し、ブラウザ UI・CLI・TUI は全て同じ snapshot を読む。クライアントごとに独自走査させると状態判定ロジックが drift する
- snapshot には生データだけでなく **UI が必要な派生値**（counts・active リスト・activity 時系列・稼働フラグ）までサーバ側で計算して入れる。しきい値・スキャン範囲等のメタ情報も snapshot に載せ、UI 側にハードコードしない
- **定期ポーリング + fingerprint 差分描画**で十分（WebSocket 不要）。間隔は「人が古いと感じない下限」とスキャンコストのバランス（実例: 5 秒・応答 ~56ms/438KB でキャッシュ・部分取得は不要と判断）。client は fingerprint 比較で変化した DOM だけ更新する。`force` 更新を fingerprint skip 条件で上書きしない
- **`bootId` でサーバ再起動を検知**: プロセス起動ごとに一意 ID を snapshot に含め、client は変化で「再起動」バナーを出す。自動 reload ではなくユーザー確認（フォーム入力中の強制リロード回避）。fetch 失敗時は最後の正常 snapshot を保持して「fetch failed」を示す
- **既定 loopback**。外部公開は明示フラグ + 認証必須。ファイル本文配信は許可ルート配下に厳格限定（パス正規化 + symlink 拒否）し、外部公開時は本文を返さずメタのみ
- **実行系ごとにモードを分ける**（production / calibration / lab 等）：モード別にデータ源と UI セクションを割り当て、ヘッダにモード別稼働インジケータを出す。非表示セクションは `hidden` で描画・計測・イベントの対象外にする
- **走査は壊れたファイルで落とさない**: 監視対象は run 中に書き換わるので fs 読み取りは全て例外捕捉で null/空を返し、1行の失敗が snapshot 全体を落とさない（実害: `new Date(null)` で API が 500）
- **ノイズ分離**: 「中断・未完」（WIP）やアーカイブ済みを active 一覧から fold 分離する（実測: active の 96% が WIP だった）。アーカイブ判定規約が環境依存なら暫定と明記する

### 実機検証ワークフロー

- 「UI が正しい」は **DOM の textContent・API の値・スクリーンショットの3つを別々に確認**して初めて言える。API が正しくても描画バグ・ソート・fingerprint キャッシュで表示が違うことがある
- `pageerror` / console error / HTTP≥400 を全ページ遷移・全操作で収集する。初回表示・別モード・別タブでだけ出るエラーを見落とさない
- screenshot は DOM/API と一致を確認してから撮る。polling 途中・再起動直後・非表示タブの screenshot は古い/空になり得る
- **非表示要素を測らない**: `hidden`/`display:none` の高さ 0 は仕様であって欠陥ではない。計測・scroll・操作の前に可視性を確認し、重い描画は `clientWidth===0` で早期 return
- **非同期 fetch に stale ガード**: 応答が返るまでに選択が変わったら結果を捨てる（リクエスト時の選択キーと応答時のキーを照合）
- **URL に全選択状態を持たせる**（タブ・フィルタ・選択・展開）: reload/back/deep link で復元。URL 由来の値は許可値にクランプする
- 実測で効いた改善: mark 遷移の Δ バッジ（tick 間の状態変化を可視化）・stale 超過時間の行内表示・detail の permalink + ファイル preview・sticky thead・大規模グラフは Map/NodeList キャッシュ + rAF 集約

## 監視側が実行状態を読む方法（dashboard ↔ pipeline の同期）

### 進行中の identity は settle 前情報源から補完する

settle 後の最終レポートだけでは「いま何が動いているか」は読めない — **実行中は report がまだ書かれていない**。情報源を「新しさ」と「確度」で優先順位付けする:

- **journal（状態遷移ログ）の末尾が report の mtime より新しければ run は live**。report は settle 時点のスナップショットなので、resume/再 dispatch で journal が伸び続けている run は journal と実行予約を優先する（`live = journalTs > reportMtime`）
- run の identity（runtime/model/profile）は複数箇所に分散し得る。優先順位の一般形: **gateway event → attempt reservation（実行予約ファイル）→ profile 定義 SSOT**。report は settled 時だけ正
- 「いま走っている stage」は journal tail を逆順に走査して最後の RUNNING/RETRYABLE 系遷移を拾う。in-flight attempt は gateway event がまだ無くても reservation に identity が出ている（実害: 進行中 stage の model 欄が空だった原因が gateway event 未到達）

### raw state と UI mark を分離する

- エンジンの raw state（PENDING/RUNNING/COMPLETED/FAILED_RETRYABLE/BLOCKED_*/CANCELLED 等）と UI 表示語彙（PASS/FAIL/FLAKE/RUN/HUNG/WIP/TODO）は **別物**。変換ロジックを1関数に集約し、UI は mark だけ描画する。「失敗」を1語で済ませず、優先順位付きの一意ルールにする
- **HUNG = `running` 状態だが heartbeat/更新が stale 閾値超過**。status ファイルだけ残って実体が死んでいる run を「正常稼働」と誤認しない。HUNG 行には stale 超過時間と「runner プロセスがあるか」のヒントを出す
- **FLAKE（retryable 失敗）と FAIL（停止・ブロック系）を分ける** — 「様子見」と「要介入」を区別できる。WIP（成果物はあるが非実行）と TODO（signal なし）も分ける

### 読み取りの堅牢性

- JSONL ログは **末尾だけ部分読み**（末尾 N KB を読み、先頭の不完全行を捨ててから各行を個別 parse）。大きな journal を全文読むとメモリを食う
- run 一覧は mtime 降順 + 件数 cap
- 監視側からの mutation（stale 状態の掃除・sweep）は既定 OFF の opt-in にし、読み取り経路と分ける
- **失敗の内因と retry 位置を run 一覧に出す**。最終 gateway event の `providerError`（429/quota/接続障害の区別）と supervisor の forward hop 位置（`forward_hop_retry_wait hopN` 等）を snapshot に含めると、「コードの失敗か quota 待ちか」が一覧から即判る（実例: `scanPipelineRuns` で gateway-events/forward-events の tail から拾う）

## 運用の罠（実測済み）

- 外部 API trial / 検証枠は本番の **数倍遅い**ことがある（実測 5〜7 倍）。疎通・契約・provenance・retry 経路の確認には十分だが、完走の実用的な検証は本番経路で行う
- `params` 変更は run 途中でも resume で反映される。形状比較を測るなら基準 run を先に完走させてから変えるか、変わることを前提にする
- timeout は constructor 既定値ではなく **request 単位の policy** で解決される経路を確認する（profile に書いても gateway が読まなければ届かない）
- 並列に見える stage でも実 spawn は直列 lease されていることがある — stage の RUNNING 時刻と worker spawn 時刻を混同しない
- 長時間走る worker は timeout 既定を実測から取る（実例: 旧 30 分既定が健全な 35〜60 分の dispatch を潰していた → 90 分に）
- resume 中の worktree で vendor/依存ファイルを消す移行ジョブを同時に走らせない — import が `MODULE_NOT_FOUND` で死ぬ運用事故になる
- **即失敗する retryable エラーは bounded retry を数分で燃やす**。429/transport が即座に返る環境では hop 間に設定可能な delay を挟まないと「16 hop の回復窓」が数分で尽きる。quota 待ちなら長い delay で監視窓を伸ばす。
- **汎用 worker エラー（ASSISTANT_EMPTY 等）に基底の provider/HTTP エラーを乗せる**。`finishReason:"error"` だけ記録すると quota 枯渇と endpoint 障害と契約問題が区別不能になる。session/assistant/message のエラーフィールドを防御的に走査して redact 済み `providerError` として durable event に残すと、本当の原因（実例: `429 GoUsageLimitError`）が一発で見える
- **LLM worker の「ストリーム死」と「遅いだけ」をプロセス I/O で区別する**。`/proc/<pid>/io` の `read_bytes` はブロック層（ディスク）しか数えず socket 受信を含まない — stream 生存は **`rchar` の delta** で見る（全 read() syscall バイト）。`wchan=do_epoll_wait` や単なる stat 睡眠は生死を区別しない。プロセス内 watchdog では自己読み取りノイズを閾値（delta ≤ ~2KB/poll で停滞判定）で弾く。cap 時間ちょうどの SIGTERM が連発する場合は「死んだ stream」ではなく「cap が生きた stream を切っている」可能性を先に疑う — SIGTERM 直前に rchar が伸びていれば後者確定
- **worker に stream-idle watchdog がないと、死んだ stream は stage timeout cap まで放置される**。SDK が `finish_reason` なし切断を throw しない型ではプロセスが永久待ちになる。activity 信号（rchar delta 等）で停滞を検出して retryable 失敗として早期返却 + 明示的 `process.exit` すると、cap 時間の待ちが消えて retry 効率が上がる。閾値は「健全な生成 pause」より十分長く取る（実測では数分の無音 pause が正常な endpoint がある）

## 知見の出所（事例）

繰り返しの実運用、対照実験、障害分析から得た一般化可能な運用知見をまとめる。具体的なプロジェクト名・コード位置・内部資料は各プロジェクトのドキュメントに記録し、この共有スキルには再利用可能な原則だけを置く。

## このスキルを使うときの約束

- 失敗を見たらまず **4型のどれか** を実測で特定してから直す。症状だけを patch しない
- 照合・証明・承認系の停止条件を新設しない
- 形を変えるときは宣言層（parameters / manifest / catalog）で行い、engine・contract の骨格は変えない
- stage 追加は **全登録面をリスト化してから着手**する。ミラー層を1つでも抜くと compile/CI で fail する
- 「パイプラインが通らない」と「成果物の品質が悪い」は別問題として切り分ける。前者は官僚ゲート・transport・evidence、後者はコンテンツ verdict
- 監視 UI を作るときは snapshot API 一本化・bootId・安全な fs 読み取りから始める。クライアント独自の状態判定を増やさない
- 改善は lab で計測してから本番へ。「収束形状（ラウンド数・退行 0・未解決 0）」を見ずに「動いた」で終わらせない
