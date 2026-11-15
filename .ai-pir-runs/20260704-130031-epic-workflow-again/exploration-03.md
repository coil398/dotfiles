## 探索レポート: epic 初回実行の安全性と「L1 自律性」未実証仮定の評価材料

### 関連ファイル一覧

| ファイルパス | 役割・内容 | 変更の必要性 |
|------------|-----------|------------|
| `.claude/skills/epic/SKILL.md` | epic 本体（L0）が制御する Phase 1〜3。3階層ネスト構造・深さバジェット運用（3-3）・ユーザーゲート委譲（3-4）を規定。**現状 working tree clean で `a10aa8e` にコミット済み** | 参照のみ（本熟考は評価。実装は別タスク） |
| `.claude/agents/epic-planner.md` | エピック分割専任。自前で explorer をネスト起動し分割戦略のみ返す | 参照のみ |
| `.claude/skills/pir2/references/experimental.md` | 全実験の SSOT。`pir2-explorer-nesting` と `epic-orchestrator-nested-pir2` の Evidence Summary が両方 **全項目 0**（一度も実行されていない）と明記 | 参照のみ |
| `~/.claude/memory/experimental_observations.md` | git 管理外の実観測ログ。`pir2-explorer-nesting` の 2026-06-23 エントリも「まだ実運用での効果観測はない」と明記 | 参照のみ |
| `~/.claude/agent-delegation.md` | 「深さ上限5、推奨2-3」の記述元（11行目） | 参照のみ |
| `docs/deepthink/20260703-175327-deepthink.md` | 本セッション先行の /deepthink①。事象X（フリーズ＝捏造起点）・事象Y（ゾンビ成功）を CONFIRMED として一次分析し M1–M12 改善点・対立#1（L1 制御責務の是非）・MAST／#44783 引用元 | 参照のみ（既存一次資料として引用） |
| `docs/deepthink/20260703-190750-Fable5.md` | /deepthink②（完成形設計）。P5=「L1 が SKILL.md 全文を自律オーケストレーションできるか」を **未実証** と明示し、G1 dry-run でのみ埋まる不確実性としてラベル | 参照のみ |
| `docs/deepthink/20260704-002417-review-w0w1-6-3.md` | W0+W1（6-3 決定論的完了検証）の深レビュー。「6-3 の実行を誰が検証するか」という再帰的信頼の論点と可監査性3段チェーンでの条件付き受容を確定 | 参照のみ |
| `.claude/skills/pir2/references/deterministic-completion-check.md` / `verify-deterministic-check.sh` | 今回コミット済みの緩和策（6-3）本体。phantom-claim floor（file-set 存在の1次元のみ検証、substance 非検証） | 参照のみ |
| `.claude/skills/pir2/SKILL.md` (579行) | ネスト pir2 ランナー(L1)が自律解釈すべき対象そのもの。6-3 が実装済み（281〜320行付近） | 参照のみ |
| `~/.claude/projects/-Users-kawasetakumi-dotfiles/c43aea5a-c3c3-4204-9d47-5daf6624c055.jsonl` | 本セッションの実トランスクリプト。3件の実失敗の一次証拠（下記補足情報） | 参照のみ（会話ログ、非コード） |
| `.ai-pir-runs/20260704-130031-epic-workflow-again/rubric.md` | 本熟考の成功基準。#3「L1 ランナー設計の実行時健全性」・#4「初回実 run の安全性」が本探索の直接の親基準 | 参照のみ |

### 既存パターン・規約

- **実験追跡パターン**: `experimental.md` は Hypothesis / Implementation / Quality Guardrails / Metrics / Adoption Criteria / Rejection Criteria / Evidence Summary / Observation Log の固定フォーマットで、恒久採用可否を「観測データが一定数貯まるまで判断しない」設計に統一している。`epic-orchestrator-nested-pir2` もこの型に沿って `Epic executions 0` から始まっている。
- **deepthink 成果物の連鎖参照パターン**: `docs/deepthink/*.md`（人間可読サマリー）← `.ai-pir-runs/<run>/position-*.md`（熟考本体）という2層構造が確立しており、後続の deepthink（本 run）が前2回の結論を前提として明示的に引用する運用が既に3回連続している。
- **構造投資領域**: `.claude/skills/pir2/references/*.md` 配下に 17 ファイルの reference 分割群があり、epic は「epic 専用 reference を作らず既存 pir2 references を参照する」方針（SKILL.md 末尾「変更不要」節）を採っている。これは3個以上のクラスファミリーというより「共通基盤の再利用」パターンであり、今回の新規改善（もしあれば）も同パターンに従うのが自然。

### 影響範囲

- **直接影響**: 本タスクは調査であり、コード変更は行っていない。次の一手（G1 dry-run 実行 / W2 先行実装 / 保留）の決定が `.claude/skills/epic/SKILL.md`・`epic-planner.md`・`experimental.md` の今後の改訂に波及する。
- **間接影響**: epic を実際に1回動かす（G1 dry-run）と judgment が下れば、`epic-runs.md`・`deferred-decisions.md` 等の成果物が新規生成され、`experimental.md` の Evidence Summary が初めて非ゼロになる。

### 依存関係

- `epic` SKILL.md は `pir2` / `pir2codex` SKILL.md 全文に依存（L1 ランナーがこれを Read して自律解釈する設計）。
- `epic-planner.md` は `planner.md` の USER_DECISION_REQUIRED 判断慣習・CLAUDE.md の既存ルールに準拠する設計。
- 6-3（決定論的完了検証）は `implementer.md`（NO_OP_JUSTIFIED マーカー・申告ファイルを自分で git add しない規律）に依存。

---

### 補足情報（本探索の中心：3つの観点への回答）

#### 観点1: L1 自律性の実証状況 — 結論「未実証」

`experimental.md` を確認した結果、関連する2実験はいずれも **Evidence Summary が全項目 0**。

- `pir2-explorer-nesting`（Started 2026-06-23）: 「Nested explorer runs: 0」。`~/.claude/memory/experimental_observations.md` の同実験エントリも「まだ実運用での効果観測はない」と明記（2026-06-23 時点の記述のまま更新なし）。
- `epic-orchestrator-nested-pir2`（Started 2026-07-03）: 「Epic executions: 0」「Parallel fan-outs: 0」「Depth fallbacks: 0」。

さらに、本セッション以前に実施済みの2本の /deepthink（`20260703-175327-deepthink.md` と `20260703-190750-Fable5.md`）が、この論点を **既に明示的に核心の未解決事項としてラベル済み** であることを確認した。

> `20260703-190750-Fable5.md` 14行目: 「**残る最大の不確実性**: L1 が pir2 SKILL.md 全文を自律オーケストレーションできるか（P5）は未実証」

> 同 188/195行目: P5 は「未実証」「U1 で G1 に反証条件として接続」「B 恒久を暫定採用（未実証）」「G1 dry-run。連続2回契約不履行→A-lite 常用化を上程」

つまり「サブエージェントが 579行の SKILL.md（explorer/planner/implementer/reviewer/tester の起動・ループ管理・VERDICT 集約・ユーザーゲート委譲判断を含む）を Read して自律的に多段オーケストレーションを完遂する」という epic の核心仮定は、**リポジトリ内のどの実行記録にも実証がない**。既存の2本の deepthink 自身が「G1 dry-run（1-unit epic, executions 0→1）でしか埋まらない」と結論しており、本探索の調査もこれを追認する形になった。

> ⚠️ 「未実証」であることは「危険」と同義ではない点に注意。既存 deepthink（Fable5）は「反証トリガ内蔵の条件付き恒久採用」（G1 で契約不履行が是正1回を挟んで連続2回起きたら A-lite へ降格）という設計で、未実証のまま小さく検証する運用を既に組み込んでいる。

#### 観点2: 本セッションで観測した実失敗の epic への波及

本セッションのトランスクリプト（`c43aea5a-...jsonl`）を直接確認し、ユーザー言及の3件が実際に発生していたことを一次証拠として確認した。

| # | 失敗事象 | トランスクリプト上の記述（該当行） | 発生した層 | epic への波及リスク |
|---|---------|-------------------------------|-----------|-------------------|
| (a) | レビューフェーズでのフリーズ | 「フリーズの根本原因は特定済み（CONFIRMED）: epic を実装していた pir2 セッションで、API エラー resume 直後に **implementer 完了報告が捏造**（行数が実ファイルと不一致）→ 5 reviewer 全 FAIL →19分迷走。`parse-failure-continue-hook` は整形式出力のため検知できなかった」（jsonl line 119, 338 で参照） | **L0（メイン Claude）自身**が resume 直後にツール呼び出し無しで完全捏造（`docs/deepthink/20260704-002417-review-w0w1-6-3.md` 30行目で確認） | epic のネスト機構（DAG/fan-out/深さバジェット/L1 ランナー）を**一切通っていない**。つまり epic 固有のリスクではなく、L0 自身の捏造という「もっと浅い層」で既に発生する現象。epic がこの現象の**発生確率を下げも上げもしない**が、L1 ランナー配下で同型の捏造が起きた場合、**epic は L0 からさらに1階層遠い**ため検知・介入が一段遅れる（下記「M1: L0 が L1/サブの内部状態を境界で受け取れず black box」に直結） |
| (b) | explorer のゾンビ成功 | 「explorer B（ステップ番号 citation）は `tool_uses: 0`・約 4.8 秒で異常終了しています（実質何もせず死亡）」（jsonl line 62）。`status:completed` を返し検出は呼び出し元の偶然の注意のみに依存、どのエージェント定義にも異常検知手順が無い（`20260703-175327-deepthink.md` 45行目で確認） | L0 → L1（直接起動、深さバジェット無関係） | epic は L1 ランナー自身がさらに explorer をネスト起動する（L2）ため、**この種のゾンビ成功が L1 の内部で起きた場合、L0 まで異常が伝播しない**懸念が強まる。`20260703-175327-deepthink.md` の M1「L1 境界テレメトリ return」はこのリスクへの直接対応策だが、**未実装**（epic SKILL.md 現状にテレメトリ return の明示的な契約項目は無い） |
| (c) | implementer 05 の API parse エラー早期終了 | 「実装エージェント(IMPL 05)が API パースエラーで早期終了。これは transient なエラー（プロンプトのロジック問題ではない）なので、ブラインドリトライ禁止の例外として1回だけ再試行します」（jsonl line 684）。再試行1回で成功（line 694） | 素の /pir2（6-3 実装作業そのもの） | epic は L1 が pir2 全体を１セッションとして長時間走らせるため、**parse エラー等の transient 障害に遭遇する母数（ターン数・API 呼び出し回数）が単純に増える**。L0 には `parse-failure-continue-hook`（Stop hook・loop guard 付き）があるが、**L1/L2 のネストされたサブエージェント内で同種の parse 失敗が起きた場合に同等の自動継続機構が働くかは未検証**（hook は Stop イベントの transcript 末尾解析に依存しており、ネスト階層でのフック発火挙動は本探索では確認できなかった） |

**総括**: 3件はいずれも根本原因が「resume 状態の外部化ゼロ」「self-report 依存で外形検証がない（6-3 導入前）」「異常検知手順がどのエージェント定義にも無い」という **epic 固有ではない共通層の脆弱性** であり、深さ・並列が増えると発生**機会**（起動回数）は単純に増えるが、発生**確率**自体が epic のネスト機構で悪化するという証拠はない。一方で、epic 固有に生じる **追加リスク** は「検知・介入の階層が1つ遠くなる」点に集約される（L0 がテレメトリなしに L1 の内部状態を観測できない black box 化）。この点は `20260703-175327-deepthink.md` の M1/M2/M6 で既に指摘・設計提案済みだが、**epic SKILL.md / epic-planner.md の現状コミット内容にはまだ反映されていない**（本探索で `.claude/skills/epic/SKILL.md` を確認した限り、L1 からのテレメトリ return の契約は明記されていない）。

#### 観点3: 深さバジェットの余裕

公式ドキュメント（後述の外部ソース参照）で正確な仕様を確認した:

> Depth is counted as the number of subagent levels below the main conversation, regardless of whether each level runs in the foreground or background. A subagent at depth five doesn't receive the Agent tool and can't spawn further. The limit is fixed and not configurable.

この定義に基づき epic の階層をカウントすると:

| 層 | 実体 | depth |
|----|------|-------|
| main conversation | epic 本体（L0） | 0 |
| ネスト pir2 ランナー | `subagent_type=general-purpose`（L1） | 1 |
| pir2 が起動する explorer/planner/implementer/reviewer/tester | （L2） | 2 |
| L2 の planner/reviewer がさらに explorer をネスト起動 | （L3、`pir2-explorer-nesting` 実験） | 3 |

epic SKILL.md ステップ 3-3 は明示的に「L3 が必要になったら explorer を再ネストせず L1 ランナー自身が直接 Glob/Grep/Read で調べる縮退運用にフォールバックする」と規定しており、**設計上は depth 3 で頭打ちにする運用**になっている。depth 5 の上限に対し数値上の余裕は 2 階層分ある。

ただし以下は**未検証**（本探索の範囲内では確認できず、公式ドキュメントにも明記なし）:

- 独立サブタスクの**並列 fan-out**（複数の L1 ランナーを同時起動）時、各 L1 がさらに L2 を起動する組み合わせでの実際の context 消費・レイテンシ挙動
- 6-3（決定論的完了検証）や `parse-failure-continue-hook` のような **L0 専用に設計された機構が L1/L2 の内部で同等に機能するか**（hook がネスト階層のどのレベルで発火するかは公式ドキュメントからは読み取れなかった）

### 視覚情報との整合チェック

本タスクにはユーザー提供のスクリーンショット等の視覚的一次情報は含まれていない。該当なし。

### リファレンス実装からの移植チェック

本タスクは移植タスクではない（既存ワークフローの信頼性評価）。該当なし。

---

### 参照した外部ソース

| ソース種別 | URL | 確認した内容 |
|-----------|-----|------------|
| 公式ドキュメント（Claude Code） | https://code.claude.com/docs/en/sub-agents | ネスト深さの正確なカウント方法（main conversation からの階層数）・depth 5 で Agent ツール剥奪・上限は fixed で設定不可・background subagent の depth はスポーン時点で固定（resume しても変わらない）ことを確認。epic の L0→L1→L2(→L3) が depth 3 で収まることの根拠として使用 |
| 公式 GitHub Issue（anthropics/claude-code） | https://github.com/anthropics/claude-code/issues/44783 | Closed as not planned を確認。並列 Bash ハング時、ハングしていない側の完了済みサブエージェントの結果すら親に配信されず親セッションが永久にブロックする実際の症状を確認。epic ステップ 3-1（並列 fan-out）への直撃リスクとして既存 deepthink の引用が正確であることを裏付け |
| 一次論文（arXiv） | https://arxiv.org/abs/2503.13657 （"Why Do Multi-Agent LLM Systems Fail?"） | Multi-Agent System Failure Taxonomy（MAST）が system design issues / inter-agent misalignment / task verification の3カテゴリ・14失敗モードで構成されることを確認。**ただし「41.8%」という具体数値は WebFetch では表・図の生データにアクセスできず独立確認できなかった**（検索要約では近似値として「44.2%」という記述もあり、出典間で数値の揺れがある可能性がある。既存 deepthink の「41.8%」を鵜呑みにせず、数値精度は要再確認として明記） |
| 一次論文（arXiv） | https://arxiv.org/abs/2505.06120 （"LLMs Get Lost In Multi-Turn Conversation"） | マルチターンで平均39%の性能低下、6生成タスク・20万超の模擬会話で検証。低下の主因は aptitude（能力）低下でなく unreliability（一貫性）低下。「一度誤ったターンを取ると回復しない」という知見を確認。長い SKILL.md を自律解釈しながら多段実行する L1 ランナーの信頼性リスクの外部裏付けとして使用 |
| 二次情報（ブログ、depth=5 の背景解説） | https://chatforest.com/builders-log/claude-code-nested-sub-agents-depth-5-token-math-builder-guide/ | v2.1.172 リリース背景・depth カウントの解釈上の曖昧さ（ルート含む/含まないかが公式に明記されていない懸念）を参照。**最終的な正確性は上記の公式ドキュメント（code.claude.com）を優先し裏取りした** |
| 二次情報（rollout 定石） | https://apxml.com/courses/llm-alignment-safety/chapter-7-building-safer-llm-systems/safe-deployment-rollout-strategies | Canary deployment（1-5% トラフィックから開始し段階的に拡大）・shadow mode（新エージェントを並列稼働させ出力比較するが本番出力はしない）・閾値超過時の自動ロールバックという一般的な安全投入パターンを確認。マルチエージェント特有の助言として「本番と同じ組織構造で reading fidelity と task completion を事前検証すべき」との記述を確認 |

### 呼び出し元への依頼

- 本探索は割り当てられた5観点（L1 自律性実証状況・本セッション実失敗の波及・深さバジェット・初回投入定石・自律実行信頼性の一般論）に集中したため、**epic-planner.md の分割ロジック自体の妥当性**や**6-3（決定論的完了検証）の実装コード品質**の深掘りは行っていない。これらが熟考の争点になる場合は別 explorer への追加委譲を検討されたい。
- MAST 論文の「41.8%」という具体数値は本探索では独立に確認できなかった（上記参照）。この数値を熟考の根拠として厳密に使う場合、arXiv PDF の Table を直接参照できるツール（またはユーザーによる目視確認）での再確認を推奨する。
- 「6-3 のようなフック機構が L1/L2 のネスト階層でも同等に発火するか」は公式ドキュメントに明記がなく、本探索では未解決のまま残した。これは G1 dry-run で実測すべき観測項目の一つとして rubric #2/#3 に直結するため、熟考側での明示的な「未知」としての扱いを推奨する。
