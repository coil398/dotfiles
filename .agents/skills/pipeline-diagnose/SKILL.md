---
name: pipeline-diagnose
description: >-
  ステージ型パイプラインの run が「止まる」「同じところを回り続ける」「収束しない」
  ときに、durable な成果物とイベント列から原因を特定する診断手順の正本。
  BLOCKED / no_matching_case / 無限リトライ / 全部再生成 / sentinel 固定化のような
  症状を、推測ではなく実測で機構まで掘り下げる。パイプラインの構築・運用方針は
  /pipeline を参照。ユーザーが /pipeline-diagnose と入力したら使う。
---

# /pipeline-diagnose — パイプライン run の実測診断

症状（「動かない」「無限に回る」「毎回全部やり直す」）から機構的な原因までを、
durable state の実測だけで掘り切る手順。**推測で直しに行かない。**
失敗の分類・設計不変条件は `/pipeline` スキル側。ここは「読み方」の正本。

## 第0原則: durable state が唯一の真実

- report / summary は **settle 時点のスナップショット**。run 中・resume 後の真実は
  journal / workflow-events / gateway-events / artifacts レジストリにある
- 「プロセスが死んだ」「ログが止まった」は症状であって原因ではない。
  まず **durable に何が記録されたか** を読む
- イベントは1ファイル1レコードでも JSONL でもよく出る。まず **フィールド名を実測する**
  （`type`/`nodeId`/`stageId`/`instanceId`/`outcome`/`revision`…想定で grep しない）

## 観測面（durable に残る判断記録）

診断のたびに probe を書くのではなく、**run 実行中にパイプライン自身が残した**
構造化記録を先に読む。イベント記録の例:

- `runDir/compile-events.jsonl` — resume 時の live compile の各 extension
  ステップが `resume_compile_extension_step`（step・applied・before/after
  fingerprint）を残す。graft 判断の内訳は `*_grafted` / `*_skipped` /
  `*_dropped` イベントに reason・code・sealedCoordinate・expectedNodeId 付き。
  **silent drop（boundary は有効だが期待 nodeId が compile に無い）も
  `review_fail_extension_dropped` として残る**
- `runDir/forward-events.jsonl` — forward supervisor の hop ごとの分類
  （`forward_hop_classified`: kind/code/nodeId）、決着理由
  （`forward_hop_settled`: cli_startup_abort 等）、invoke 結果
  （`forward_hop_invoked`: state/detailCode）、hop 間待機
  （`forward_hop_retry_wait`）、上限到達（`forward_loop_exhausted`）、
  draft 配送（`draft_delivered`/`draft_delivery_failed`）
- **段階ごとの成果物配送**: durable state に保存された最終成果物を、適切な段階後に設定済みの成果物先へ原子的に配送する。任意の品質確認やレビューが停止しても、その時点の成果物を取得できるよう、配送はそれらのゲートと独立させる。手動実行が必要な場合は、そのプロジェクトで定めた export command を使う。
- `journal.jsonl` の `COMPLETED→STALE` transition — `detail.resumeReason` /
  `detail.durableOutcomeState` に「なぜ再利用不可だったか」が残る
  （旧形式は理由なしの素の遷移だけだった）
- `WORKFLOW_NODE_COMPLETED` outcome — conditional の `no_matching_case` に
  `expectedCaseVerdicts`・`hasDefaultCase` が、loop BLOCKED に
  `continueVerdicts`・`maxRounds` が載る。「verdict FAIL vs cases [PASS]」が
  journal 一発で読める
- `gateway-events.jsonl` / WORKFLOW_NODE_STALE(reason) / 既存の報告系は従来どおり

読み順: `forward-events.jsonl`（何を選んだか）→ `compile-events.jsonl`
（graft が効いたか/落ちた理由）→ journal + outcome detail（どこが再利用されず
どこが blocked になったか）。

## 症状 → 診断経路

### A. 同じサブツリーが resume のたびに全体再実行される（「全部再生成」）

1. **dispatch の座標を洗う**: 実際に dispatch された stage の instanceId/nodeId を
   全列挙し、座標（`...:patch:rN` / `...:reverify` / establish 座標）で分類する。
   patch 座標が一度も出なければ「patch 経路が生きていない」が確定
2. **stale の種を特定する**: resume plan の `staleArtifactIds` / `changedArtifactIds` /
   `resumeFrom` を読む。stage は「宣言した input **または** output が stale」で
   再実行される — **出力宣言でも巻き込まれる**（writer が `draft-round` を output
   宣言していれば、draft-round を stale に撒くだけで writer が全文再生成する）
3. **reseal の連鎖を辿る**: A が再 seal → A を input に持つ B が stale → …。
   「証拠 artifact が reseal するたびに生成 stage が全文書き直す」は典型事故

### B. conditional が完走するのに分岐が一度も発火しない

**決定的シグナル**: `WORKFLOW_NODE_COMPLETED` があるのに
`WORKFLOW_CONDITIONAL_SELECTED` が一度もない（全履歴で0件）。

- その conditional の outcome を読む: `{state:'BLOCKED_CONTENT', reason:'no_matching_case',
  decisionVerdict:'FAIL'}` なら **verdict は読めているが case が compile 時に無い**
- 次に調べるのは **case を作らなかった条件関数**（compiler 内の allow* / gate）。
  verdict を疑う前に「どの条件で FAIL case が落ちたか」を当該座標で再現する
- conditional が adoption（STALE→COMPLETED 同秒）で済まされている場合もある —
  adoption は記録済み outcome を返すだけで **分岐を再実行しない**。
  分岐内に未完の node が残っているなら、選択済み分岐が再駆動されない設計を疑う

### C. round が永遠に 1 のまま / evidence が毎回 sentinel

- 証拠 artifact を全版読む: `mode:'no-previous'`・`reviews:[]` が **全版** なら
  round 座標が producer に届いていない
- round の導出経路を実測する: `reviewLoopControl` / instanceId の `round-N` /
  `:patch:rN` 座標 — producer が読む経路と、実際の instanceId の形が一致するか
- 「rebase / carry 用の別 stage があるが artifact が0件」なら、その経路は休眠。
  正常系（establish→patch 分岐）がその stage を経由しているかを compile 済み
  グラフで確認する

### D. spine / continuation / sealed 座標の誤認

「loop が linear continuation で再 compile される」系では、sealed 座標の導出を
**必ず実 run のイベント列で再現**する:

- `includes(prefix)` / `startsWith()` 系の substring 一致は、**ネストした別 loop の
  座標を自 loop の spine と誤認する**（実例: `...:review:draft-quality:patch:r2`
  が `...:review` を prefix に含むため review spine と誤認 → `sealedCoordinate` が
  draft-quality 配下に食い込み → compile 時の spine token 検査が `patch:rN`
  を期待して不一致 → FAIL case が消える → no_matching_case → 永久ループ）
- 正しい問いは「prefix の直後のトークンがこの loop の spine 語彙
  （`patch:rN`/`escalate:rN`/`reverify`/`waive`/…）か」。**座標の深さではなく
  トークン列の所属**で判定する
- **sealed tip は「journal に実在する最深トークン」まで取る**。spine 導出が
  `patch:rN` で止めてしまうと、その先に記録済みの selector 分岐
  （`:waive`/`:reverify`）が切り捨てられる。次 round の continuation は
  selector 分岐内の suffix 座標からしか生えない設計なら、tip を patch 座標で
  止めた時点で continuation の発火点（loop decision が居る座標）を失う
  （実例: `patch:r4:waive` 完了済みなのに sealed=`patch:r4` と切り詰め、
  期待 continuation `patch:r4:patch:r5` が compile に永久に存在しない）
- **seal 延長の完了判定はトークン境界で行う**。`includes('…:patch:r4:waive')`
  は `…:patch:r4:waiver`（waiver receipt）に部分一致して false positive
  する。`endsWith(coord)` / `includes(coord+':')` / `includes(coord+'--')`
  の3形で判定する（実装: `deepestCompletedDraftPatchSpine` の
  `coordinateTail` — `:reverify` と `:waive` 両方に適用済み）
- **boundary が期待する nodeId と compiler が emit する nodeId が同じ語彙か**を
  compile 済みグラフで直接照合する。sealed tip 配下の emit を全列挙し、
  boundary の `expectedNodeId` と突き合わせる — 「sealed tip で閉じた分岐
  （waive/reverify が false）しか残っていない」「direct 入れ子を期待するが
  実装は selector 経由でしか emit しない」が典型事故
- **report の boundary は settle 時点の値**。journal がその先まで進んでいるなら
  stale boundary を疑い、「journal の最深 COMPLETED」と「boundary.nodeId」の
  前後関係を必ず比較する（古い decision を rerun しても前には進まない）
- **fail-forward 拡張が「main spine だけ」をカバーしていないか**を疑う。
  `REVIEW_CEILING_WAIVER_ARTICLE_TYPES` は初版（`2da47e1`）で
  `{weekly, market}` だったが `f226e48` で `{market}` に縮められた —
  根拠は「weekly は bounded fail-forward で linear suffix を1つずつ延ばす」。
  **これは一次対応** であり、その fail-forward は main review spine の
  sealed 座標しか延ばさない。publish subtree 等にネストした別座標の
  review loop（例 `root:publish:…:math-loop:review`）は base clamp
  （weekly は `reviewCorrectionMaxRounds=1`）のままで FAIL case を持たず、
  r1 で FAIL した瞬間に case なし BLOCKED → resume が同じ判定を無限に
  replay する。対処の選択肢は「ネスト座標にも fail-forward を効かせる」か
  「waiver 集合の一次対応を見直す」かであり、コメント本文
  （"a weekly that never ships is worse than a provisional one"）が
  weekly を外した設計と矛盾している点に注意する
- **suffix 座標配下では emit の次 round 採番が durable 消費数とずれる**。
  suffix emit（`buildSuffix(patchRound, coord+':waive'/:reverify')`）が
  `patchRound+1`（ローカル起点）で次 patch を emit するのに対し、boundary は
  `sealedRound+1`（durable 消費数）を期待する。suffix 配下でさらに patch が
  消費されると乖離する（実例: `patch:r9:waive` が `patch:r10` を消費済みなのに
  emit は `patch:r10` を再生成、boundary は `patch:r11` を期待 →
  `expected_draft_patch_absent_in_extended_graph` で silent drop）。
  **sealed-tip では emit が `reviewLinear.nextRound` を使うべき** —
  `buildReviewAttempt` patch-mode buildSuffix で適用済み（W40 fx）
- **boundary 側の座標抽出が suffix トークンに盲目だと救助経路が死ぬ**。
  `r12PatchCoordinateFrom` が `:reverify` しか剥がさず `:waive` 経由で
  FAIL した r12 を受理しない → `final-preservation-repair` が
  INELIGIBLE で永久に選ばれない（W40 equity: r12 消費済みなのに到達不能）。
  認識側（boundary の座標パース）と emit 側（case 発火条件、例
  `allowFinalPreservationReviewFail`）の**両方**を同じ suffix 語彙で揃える
- **手動 `--resume` は live supervisor の子 walk と journal を競合させる**。
  親（`run-weekly-v2` 等）が生存しているなら手動 resume を打つな — 
  同じ runDir の並行 walk は `decision must precede tip` DRIFT で
  fail-closed される（これは正しい防御）。まず `ps` で親を確認し、
  supervisor が駆動しているならそちらに任せる
- **selector 両分岐への同一 subtree emit は duplicate-id で compile 死**。
  r12 の `:reverify`/`:waive` 両分岐に同じ salvage seq を出すと
  node id が衝突して `GRAPH_COMPILE_INVALID`（W40 equity）。emit は
  broad suffix match ではなく **durable に blocked した decision の
  exact 座標**に絞る — boundary が `decisionCoordinate` を receipt に
  載せ、emit 側は `branchCoordinate === decisionCoordinate` で判定
- **recompile carrier の receipt は trigger 別 exact keys を満たせ**。
  post-salvage の carrier compile で mint する receipt が trigger ごとの
  必須キー（preservation-reject は `patchCoordinate`、review-fail は
  `decisionCoordinate`）を欠くと exact-keys で `GRAPH_COMPILE_INVALID`。
  compile error は `mapCompilerReviewExtensionCeiling` が wrapper メッセージに
  握り替えるため、compile-events には生の理由が出ない — 同じ引数で
  `composition.compile` を直接叩いて生の例外を取ること（W40: W33 fixture が
  preservation-reject carrier の `patchCoordinate` 欠落を露呈させた）
- **`decision must precede tip` 系の drift 検査は実 BLOCKED conditional に限る**。
  boundary が anchor（stage の FAIL verdict イベント）を blockedDecision に
  フォールバック代入する設計では、walk 中断状態（decision 書き込み済み・
  root terminal 未伝播）は常に `anchor.revision > tip.revision` になり
  健康な resume を wedge させる。比較前に
  `blockedDecision.outcome?.state==='BLOCKED_CONTENT'` を要求すること
  （W40 fx: 殺された walk の anchor FAIL が tip より新しく永久 fail-closed 化）

### E'. 高 CPU・高 RSS だが journal が伸びない（replay / 状態再読の二次爆発）

**決定的シグナル**: プロセスは生きて CPU 100%+・RSS が GC 上限（Node 旧世代
~4GB）に張り付いているのに、`workflow-events/` のファイル数・`journal.jsonl` が
30分以上伸びない。子プロセスなし。

- Node の `--inspect` を `kill -USR1` で起動して CDP CPU profile を数秒取る。
  `readJson` / `JSON.parse` / `replay*` が支配的で leaf が GC なら、
  **状態ストアの全件再読ループ**が確定
- 典型構造: 「node 実行ごとに readRun() → 全 event segment を再読・再 parse」
  の **O(nodes × events)**。events が数千ファイル/100MB 級になると
  1 node あたり数百 MB の GC churn で実質停止
- append-only の immutable segment store なら修正は **runDir 単位の
  revision-keyed 増分キャッシュ**: 前回 revision 以降の新規ファイルだけ読む。
  イベントの不変性を `Object.freeze` で構造担保すれば共有参照も安全
  （実測: replay 483ms→6ms、RSS 3.6GB→1GB）
- 「遅い」だけで止めず、**read の回数 × read のコスト** を掛け算で説明できるかを
  確認する。単発の重い読み込みは問題にならない

### E''. 「X 完了後にだけ発火する機構」を X の完了チェックで潰している

- early-return / ガード条件が「完了したら return」系なら、**その機構の発火条件が
  「その X が完了していること」を前提にしていないか**確認する
  （実例: 「salvage 完了済みなら return」が「salvage 完了後にだけ走る
  reconciliation graft」を恒久的に殺していた — graft の発火条件とガードの
  除外条件が同じ出来事を見ていた）
- 一般形: 「前提条件の達成」を「スキップ条件」に流用していないか。
  冪等性は「この機構が二度目に走るのを防ぐ」だけに使い、「初回の発火」を
  殺さない

### E. verdict / 計測が「間違っている」ように見える

- reviewer/LLM が報告した数値が実物と違うとき、まず **機械計測が注入済みか** を
  確認する（dispatch 層が実測値を prompt に差し込む設計なら、report 値と注入値を
  突き合わせる）。注入されていれば LLM は幻覚していない — **計測定義**
  （prose のみ・表除外 等）と **閾値の出所**（plan の字数帯が writer の実力を
  超えていないか）を疑う
- 同じ FAIL が繰り返されるなら whack-a-mole ではなく **到達不能な閾値**の可能性。
  前回 PASS した run の計測値と plan 帯を横に並べる

## 診断の進め方（手順の型）

1. **run dir の地図を作る**: `artifacts.json`（レジストリ）/ `journal.jsonl` /
   `workflow-events/` / `gateway-events.jsonl` / `workspace/shadow/` — どこに
   何があるかを ls で確定させてから読む
2. **タイムラインを引く**: `NODE_STALE` / `NODE_COMPLETED` / `CONDITIONAL_SELECTED` /
   `BARRIER_BOUND` / `ATTEMPT_DISPATCH_*` を時系列で並べ、1 resume サイクルの
   推移（何が stale になって何が dispatch されてどこで終わるか）を1回分読み切る
3. **同じ結末の繰り返し回数を数える**: sentinel 27版・decision 15回完走で
   selection 0、のような「回数」が構造問題の強度を表す
4. **原因候補のコードを「その座標で」実行する**: 実 run の events を replay して
   derive 関数（境界選定・spine 導出・round 解決）を実データに通す。
   静的に読むだけでなく **その run の入力で再現**させる
5. **原因が compile 時なら、どの条件関数が false を返したかまで特定する**。
   「case が無い」で止めず `allowX(coordinate, round)` の各分岐を潰す

## 収束しないループの構造的チェックリスト

- [ ] hop/forward ループに「同じ分類なら止める」dedup が紛れ込んでいないか。
      分類の同一性は進捗ゼロを意味しない（裏で shard 再生成や graft が
      進んでいても同じ分類を返しうる）。dedup は表向き収束に見えて、実際は
      実行中の回復 hop を握り潰して再起動ループを生む。停止条件は
      hop 上限（`forward_loop_exhausted`）に一本化し、同一分類でも毎回
      invoke する（W40 実害: `repeated_classification_fingerprint` が
      terminal-recovery の回復を止め続けた）
- [ ] conditional が verdict に対応する case を持っているか（compile 後の定義で確認）
- [ ] FAIL → patch 分岐の座標が journal に実在するか（存在しない=分岐未発火）
- [ ] resume ごとに round 指標が前進するか（`toRound`/`patch:rN`/`maxRounds`）
- [ ] resume plan の stale 種が「次に必要な stage」だけを巻き込むか
      （establish 済みの生成 stage まで stale に撒いていないか）
- [ ] evidence / 証拠 artifact がラウンドをまたいで内容を保持するか
- [ ] patch の対象と review の対象が **同じ draft** か
      （rewrite → review → patch の順だと patch は常に「さっき書き直した稿」
      を直すことになり、前ラウンドの patch を次の resume の rewrite が破壊する）

## 直しに行く前の確認

- 原因層を一言で言えるか: 「compiler の spine 誤認」「resume plan の stale 範囲」
  「producer の round 解決」「閾値のキャリブレーション」等
- その修正で **観測した全症状** が説明できるか（一部分だけ説明する原因は
  別の主因がある）
- 修正が「既存の設計した経路を生かす」ものか（迂回・ゲート追加・対処療法は禁止
  — `/pipeline` の不変条件を参照）
- 直したあと「次の resume で何が起きるべきか」をイベント語彙で予言できる状態に
  してから実機で確認する
