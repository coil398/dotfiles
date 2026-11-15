## 探索レポート: /epic 完成形ワークフロー設計のための挿入点確定（M1/M2/M3/M9 + Phase1.5実内容 + Option A実コスト）

前提として `.ai-pir-runs/20260703-175327-deepthink/position-1.md`（ROUND1 position、M1〜M12・対立#1〜#4）を read 済み。本探索はその中で「実 SKILL.md 未読の推測」「追加探索が要る論点」として明示されていた 6 項目を実ファイルで確定するもの。

---

### 関連ファイル一覧

| ファイルパス | 役割・内容 | 変更の必要性 |
|---|---|---|
| `.claude/skills/epic/SKILL.md` | epic 本体オーケストレーションの全ステップ定義（Phase1〜3） | 変更あり（M1/M2/M3/M9/破壊的変更ゲート委譲の挿入先候補） |
| `.claude/agents/epic-planner.md` | エピック分割専任エージェント定義 | 参照のみ（分割レベルに専念、実装詳細を持たない設計は確定済み） |
| `.claude/skills/pir2/SKILL.md` | pir2 全13ステップの構造定義。L1（ネスト pir2 ランナー）が実行する手順そのもの | 参照のみ（Option A 採用時は epic SKILL.md 側に相当ロジックを移植する必要があり間接的に影響） |
| `.claude/pir2-protocol.md` | 共有機構（チーム運用・ファイル受け渡し・handoff・reviewer並列・refactor-advisor）の本籍 | 参照のみ（M1/M2 の恒久化先候補） |
| `.claude/skills/pir2/references/retrospector-prompt.md` | retrospector 起動仕様（model切替・渡すパラメータ一覧） | 参照のみ |
| `.claude/skills/pir2/references/run-dir-base.md` | RUN_DIR/handoff.md の基底パス SSOT | 参照のみ（epic の EPIC_RUN_DIR 設計もこれに倣う） |
| `.claude/skills/pir2/references/continuation-gate.md` | OUTER_LOOP_COUNT 上限到達時の単発ユーザーゲート | 参照のみ（永続化機構ではない） |
| `.claude/skills/pir2/references/next-steps-queue.md` | run-local な checkbox 状態管理（`{RUN_DIR}/next-steps.md`） | 参照のみ（M9 の一部として epic 側に相当設計が必要） |
| `.claude/skills/pir2/references/handoff-cleanup.md` | handoff.md の完了判定・削除/残置ロジック | 参照のみ |
| `.claude/skills/pir2/references/fan-out-gate.md` | reviewer 並列起動の自己コミットメント宣言＋違反検知 | 参照のみ（Option A コスト試算で必須要素として計上） |
| `.claude/skills/pir2/references/exploration-loop.md` | 能動的再探索ループ（最大5回）の収束判定ロジック | 参照のみ |
| `.claude/skills/pir2/references/implementation-delegation.md` | implementer-subagent/shards/sequential/main の actor 判定・統合確認プロトコル | 参照のみ（M2 の「統合確認＝決定論git突合」の既存先例として重要） |
| `.claude/skills/pir2/references/team-member-prompts.md` | pir2async 専用チームメンバープロンプト | 参照のみ（epic には直接関係なし） |
| `~/.claude/pir-handoff.md`（= `.claude/pir-handoff.md`） | handoff.md 全プロトコル（ファイル位置・フォーマット・ライフサイクル） | 参照のみ（M9 で「プロジェクト単位1ファイル」という制約が epic 並列実行と衝突する根拠） |
| `.claude/skills/pir2/references/experimental.md` | epic-orchestrator-nested-pir2 実験セクション含む実験レジストリ | 参照のみ（Adoption/Rejection Criteria に M1〜M9 相当のメトリクスが一部既に定義済み） |
| `.claude/skills/pir2/references/plan-choice-gate.md` | プラン選択肢ユーザー確認ゲート（epic Phase1.5 が「倣う」と明記する先） | 参照のみ |
| `.claude/skills/pir2/references/destructive-change-check.md` | 破壊的変更フラグ(a-e)＋動作変更フラグ(f1-f3)の2軸判定・Auto modeでも省略不可の事前ゲート | 参照のみ（epic 配下での格下げの実証に使用） |
| `.claude/skills/pir2/references/feedback-conflict-gate.md` | 直前 feedback 自己照合ゲート | 参照のみ |

---

### 既存パターン・規約

- **L1 は fresh context の Agent 呼び出し**: epic SKILL.md 3-0（85行）は `subagent_type=general-purpose` を毎回新規起動する設計。これは pir2 の「サブエージェント間はファイル経由・要約のみ返す」という telephone-game 回避パターン（`pir2-protocol.md` 11-23行）を epic レベルに一段拡張したものであり、**L1 という中間層が「N サブタスク分の実行状態を L0 の連続コンテキストから隔離するリセット境界」として機能している**点が構造的な特徴。
- **ファイル経由の状態共有 + 要約のみ返す**は pir2 全体の一貫パターン（探索・プラン・実装・レビュー・テストすべて `{RUN_DIR}/<kind>-NN.md` に本体を書き、チャットには要約のみ）。epic もこれを継承し `{EPIC_RUN_DIR}/epic-plan.md` / `epic-exploration-*.md` / `epic-runs.md` に同じ設計を適用している。
- **Fan-Out Gate の自己コミットメント宣言**（`fan-out-gate.md` 1-29行）は「並列発火直前のターン本文に必ず宣言テンプレートを書く」という、モデルの手癖（1体ずつ逐次起動）を防ぐための構造的フェンス。epic のステップ3-1（89-91行）もこれを踏襲している。
- **ユーザーゲートは常にオーケストレーター（メイン Claude 相当）に集約**という規約が pir2/epic 共通で貫かれている（サブエージェントはユーザー対話不可）。

---

### 問い1: M1（L1 テレメトリ return）の挿入点

| 項目 | 実ファイル該当箇所 | 確定事実 |
|---|---|---|
| L1 起動プロンプトの現状 | epic SKILL.md 3-0（83-87行） | 起動プロンプトは「あなたはこのサブタスクの PIR² オーケストレーターです。`~/.claude/skills/${SUBTASK_SKILL}/SKILL.md` を Read し、その手順に従って...実行してください」のみ。**返り値フォーマットを明示指定する記述は一切ない** |
| epic 本体が L1 の返り値に期待する内容（暗黙の前提） | epic SKILL.md 3-2（93-95行） | 「後続の起動プロンプトに、先行サブタスクの返り値から得た `作業ディレクトリ(サブ RUN_DIR)` パス・変更ファイル一覧・`git diff` 確認指示を注入」と書かれている＝epic 本体は **L1 の返り値に RUN_DIR と変更ファイル一覧が含まれることを前提にしている**が、この前提を満たすための返り値フォーマット規定がどこにも無い（ギャップ） |
| epic-runs.md への記録内容 | epic SKILL.md 3-5（105-107行） | Ti → サブ RUN_DIR の対応のみ。Phase/timestamp は無い（M3 で後述） |
| L1 が実際に返すテキストの型 | pir2 SKILL.md ステップ12（511-554行） | L1 は pir2 SKILL.md を Read してオーケストレーターとして動くため、**正常終了すればこのステップ12のテンプレート**（タスク・実装記録・変更ファイル・レビュー結果VERDICT・INNER_LOOP_COUNT・リファクタ提案・テスト結果VERDICT・OUTER_LOOP_COUNT・REPLAN_COUNT・RUN_DIR・振り返り）が L1 → epic 本体への Agent 応答本文として返る |

**確定した挿入点**: epic SKILL.md ステップ 3-0（83-87行）に「L1 は pir2 ステップ12 の最終サマリーに加え、構造化テレメトリ（claimed 変更ファイル一覧・INNER_LOOP_COUNT・OUTER_LOOP_COUNT・REPLAN_COUNT・最終到達フェーズ）を返り値冒頭に明示すること」という指示を追記する形が自然（pir2 ステップ12 は既にこれらの値をほぼ含んでいるため、実質は「フォーマットの明示規定」＋「epic 側が明示的にこれを Read/パースする」ことの明文化）。

> ⚠️ **推測・要検証（技術的制約）**: `Agent` ツールでのネスト起動は同期的なブロッキング呼び出しである（本探索では実機検証していないが、環境ツール仕様上 Agent 起動に対する `run_in_background`/`Monitor` 相当の非同期監視手段は明示されていない）。この前提が正しい場合、**L1 が完了して return するまで epic 本体はその呼び出し結果を一切受け取れない**。したがって L1 がフリーズ（事象X型）した場合、L1 は一切 return せず、M1（return テレメトリ）は**フリーズ検知には原理的に寄与できない**（return 自体が発生しないため）。M1 が実際に効くのは「L1 が完了はしたが内容が捏造/矛盾している」ケース（事象Y型ゾンビ成功）の検知のみであり、position ファイルの残課題「①SubagentStop/Stop hook が Agent メタデータを決定論取得できるか」と同根の未解決点として残る。ここは deliberator/gate が確定的事実として扱わないこと。

---

### 問い2: M2（L0 決定論的 git-diff 検証）の挿入点

| 項目 | 実ファイル該当箇所 | 確定事実 |
|---|---|---|
| epic 側・依存サブタスク直列時 | epic SKILL.md 3-2（93-95行） | 「先行の変更は working tree に残っており後続 pir2 の explore フェーズが拾える」との記述はあるが、**epic 本体が先行サブタスクの claimed 変更ファイル集合と実 `git diff --name-only` を集合照合するロジックは一切書かれていない** |
| epic 側・Phase3 統合確認 | epic SKILL.md ステップ4（113-115行） | 全サブ pir2 完了後、epic 本体が `git diff` で「結合点（サブタスク境界をまたぐインターフェース・命名・未接続実装）の整合」を確認する記述はあるが、これは**目視の整合性確認**であり、claimed 集合 vs 実 diff の**決定論的集合一致検証**ではない |
| pir2 側・implementer→reviewer 境界（デフォルト actor） | pir2 SKILL.md ステップ6-1→7（279-306行、359行〜） | `IMPLEMENTATION_ACTOR=implementer-subagent`（デフォルト単一 implementer）の場合、implementer 完了直後から reviewer 起動までの間に **git diff と claimed 変更ファイルを機械照合するステップは存在しない**（reviewer は `implementation-{NN}.md` の記述内容とコードを自分で Read するのみ） |
| pir2 側・既存の決定論 git 突合の先例 | `implementation-delegation.md` 57-65行（shard統合確認）・103-110行（unit統合確認） | **shard/sequential actor 使用時のみ**、スキル本体が「全 `implementation-*.md` を Read → `git diff` で shard 外編集・同一ファイル競合・命名不整合・未接続実装を確認」という決定論チェックが既に存在する。ただし対象は shard 境界の整合性チェックであり、「claimed 集合 vs 実 diff」の照合という M2 が指す形とは目的が異なる（既存先例はあるが M2 そのものではない） |

**確定した挿入点**: pir2 側はデフォルト actor（`implementer-subagent`）に対しても shard 統合確認と同型の git 突合ステップを新設する必要がある（例: 6-1 と 7 の間に新ステップ「6-3: 決定論的完了検証」を追加。既存の shard/sequential 統合確認ロジックを一般化する形が既存パターンに最も整合的）。epic 側は 3-2（依存サブタスク先行成果注入の直前）または Phase3 のステップ4（統合確認）に、同様の決定論ゲートとして明記する挿入が候補。

---

### 問い3: M3（epic-runs.md の Phase+timestamp）の挿入点

| 項目 | 実ファイル該当箇所 | 確定事実 |
|---|---|---|
| 現 epic-runs.md 記述内容 | epic SKILL.md 3-5（105-107行） | 「各サブタスクの `Ti → サブ RUN_DIR` 対応を `{EPIC_RUN_DIR}/epic-runs.md` に追記して観測可能性を担保してください」——**書く内容は Ti ↔ サブ RUN_DIR の対応表のみ**。Phase 遷移・timestamp・現 DAG ノードの記録指示は一切無い（確定・grep でも epic SKILL.md 内に「timestamp」「Phase遷移」の語は出現しない） |

**確定した挿入点**: 3-5 の記述を「各サブタスク起動直前に開始 timestamp、完了直後に終了 timestamp + 完了フェーズを epic-runs.md に追記する」に拡張する。

> ⚠️ **問1と同じ制約が波及する**: epic 本体が記録できるのは L1 の Agent 呼び出しの**前後2点**（起動直前・完了直後）のみ。L1 内部の Phase 遷移（explorer→planner→implementer→reviewer→tester→retrospector）を epic 本体が呼び出し中にリアルタイム観測することは、前述の同期呼び出し制約が正しければ構造的にできない。M3 が実現できるのは「サブタスク単位の開始/終了 timestamp」までであり、「L1 内部の Phase 単位の粒度」は M1 のテレメトリ return（完了時にまとめて報告される事後情報）に依存する。

---

### 問い4: M9（resume 台帳）の挿入点

| 項目 | 実ファイル該当箇所 | 確定事実 |
|---|---|---|
| pir2 の continuation-gate | `continuation-gate.md` 全文 | OUTER_LOOP_COUNT 上限到達時のみ発動する**単発の判定ゲート**。何かを永続化する機構ではない（「1 サイクル中に通過できるのは最大1回」で使い捨て） |
| pir2 の next-steps-queue | `next-steps-queue.md` 全文、pir2 SKILL.md ステップ5.6（243-249行） | `{RUN_DIR}/next-steps.md` に checkbox リストを Write し、各ステップ完了直後に `[x]` 化（5.6-2）。「ユーザー会話による**1ターン以上の中断後**、次の判断前に必ず Read する」（5.6-3）という **run-local な状態管理**。ライフサイクルは単一 pir2 run（＝1 L1 インスタンス）内で閉じる |
| pir2 の handoff.md | `pir-handoff.md` 17-23行 | ファイル位置は `${PROJECT_ROOT}/.ai-pir-runs/handoff.md`。**「プロジェクト単位で1ファイル」（per-run ではない）**と明記。複数回の /pir2 実行にまたがって共有する設計 |
| epic での並列時の扱い | epic SKILL.md 内に該当記述なし（grep 結果: 「handoff」の語は epic SKILL.md 内に一切出現しない） | epic SKILL.md には handoff.md のスコープ分離に関する記述が**一切ない**。したがって並列 fan-out されたサブタスク（3-1）の各 L1 は、各々が pir2 SKILL.md ステップ1のデフォルト挙動（`${PROJECT_ROOT}/.ai-pir-runs/handoff.md`）をそのまま使うことになり、**複数 L1 が同一 handoff.md に同時書き込みする競合が構造的に起こりうる**（対立#3で示唆されていた「並列競合回避」の実体はこれ） |

**確定した挿入点**: epic SKILL.md ステップ 3-0（L1 起動プロンプト）に「HANDOFF_PATH はプロジェクト単位のデフォルトを使わず、サブ RUN_DIR スコープの handoff 相当ファイル（例: `{サブRUN_DIR}/handoff.md`）を使うこと」という上書き指示を追加する必要がある。next-steps-queue（run-local）はスコープ的に元々サブ RUN_DIR 内で完結するため epic 側の追加介入は不要。continuation-gate は L1 内部で完結する単発ゲートなので epic 側の永続化とは無関係。

---

### 問い5: Option A の実コスト（対立#1 の決着材料）

Option A（L0 が L1 ランナーを廃し pir2 の各フェーズを直接オーケストレーションする）を採用した場合、epic 本体が単一の連続コンテキストで直接回さねばならない pir2 SKILL.md の全構造を以下に列挙する。

#### pir2 SKILL.md の全ステップ・ゲート・ループ（L0 が直接肩代わりする対象）

| # | ステップ | 内容 | Option B（現行）での扱い | Option A での epic本体の負担 |
|---|---|---|---|---|
| 1 | ステップ1 | RUN_DIR/PROJECT_MEMORY_DIR確定・RESUME_MODE判定 | L1 が自分の bash で計算・完結 | epic本体が**サブタスクごとに**同じ bash 計算・RESUME_MODE判定ロジックを保持・実行 |
| 2 | ステップ2 | brainstorm 要否判定 | L1 が判断 | epic本体が判断（サブタスク文脈保持が必要） |
| 3 | ステップ3 | explorer起動（haiku/sonnet/opus使い分け、最大3並列、追加探索無制限ループ） | L1 が起動・レポート要約保持 | epic本体が起動、explorer要約を**全サブタスク分**自コンテキストに保持 |
| 4 | ステップ4 | planner起動（opus） | L1 が起動 | epic本体が起動、plan.md要約保持 |
| 5 | ステップ4.5 | 能動的再探索ループ（最大5回、REPLAN_COUNT管理） | L1内で完結・カウンタもL1限定 | epic本体が**サブタスクごとに独立した**REPLAN_COUNTを保持・管理（cross-subtask汚染防止が必須） |
| 6 | ステップ4.6 | プラン選択肢ユーザー確認ゲート（複数案/USER_DECISION_REQUIRED/字義解釈確認/v2→v3切替確認、Auto modeでも必須） | L1がbubble-up（3-4）でDEFERRED_USER_DECISIONSに集約、epic本体は事後一括報告可 | epic本体が**都度**ユーザーに直接確認（ブロッキングゲート、サブタスクごとに発生しうる） |
| 7 | ステップ5 | プラン保存（docs/plans/） | L1が実行 | epic本体が実行 |
| 8 | ステップ5.5 | handoff.md初期版生成 | L1が実行（プロジェクト単位1ファイルの競合リスクは既存のまま） | epic本体が実行（同上、かつ複数サブタスク分を一元管理） |
| 9 | ステップ5.6 | next-steps-queue初期化+全ステップでのcheckbox更新（必須運用） | L1が自分のRUN_DIR内で完結 | epic本体が**サブタスク数分の**next-steps.md状態を並行管理 |
| 10 | ステップ5.7 | 破壊的変更チェックリスト（2軸・8項目判定、Auto modeでも省略不可のユーザー確認） | L1が判定・bubble-up | epic本体が**都度**2軸8項目を機械判定＋該当時ユーザー確認（ブロッキング） |
| 11 | ステップ5.8 | 直前feedback自己照合ゲート（14日以内5件Read+突合） | L1が実行 | epic本体が**サブタスクごとに**MEMORY.md/feedback_*.mdを再Read・突合 |
| 12 | ステップ6 | 実装actor決定（subagent/shards/sequential/mainの判定）+ implementer起動 + 統合確認 | L1が判定・起動 | epic本体が判定・起動、IMPL_INDEX等をサブタスクごとに管理 |
| 13 | ステップ6.5 | 未解決事項ユーザー確認（A/B/C選択、ブロッキング） | L1がbubble-up | epic本体が**都度**ブロッキング確認 |
| 14 | ステップ7 | レビューループ最大3回（Fan-Out Gate宣言必須・5観点ハイブリッド並列・VERDICT集約・差し戻し時review-fix shard判定） | L1が実行、INNER_LOOP_COUNTもL1限定 | epic本体が**サブタスクごとに独立したFan-Out Gate宣言**を正しく発火（宣言テンプレートの自己コミットメント文言をcross-subtaskで混同しないこと自体が新たなリスク） |
| 15 | ステップ7.5 | refactor-advisor起動+ユーザーゲート（all/番号/none/custom）+適用後retest | L1がbubble-up | epic本体が**都度**ユーザーゲート開放 |
| 16 | ステップ8 | テストループ最大3回（OUTER_LOOP_COUNT管理、FAIL時implementer再起動+レビュー再ループへの巻き戻し） | L1が実行 | epic本体が管理、OUTER_LOOP_COUNTをサブタスクごとに独立保持 |
| 17 | ステップ8-2-G | 続行可能ゲート（4条件判定、Auto modeでも必須） | L1がbubble-up | epic本体が**都度**判定・ブロッキング確認 |
| 18 | ステップ9 | ウォークスルー生成（フル版+サマリー版） | L1が実行 | epic本体が実行 |
| 19 | ステップ10 | メモリ記録（モデルスイープ計装） | L1が実行 | epic本体が**サブタスクごとに**PROJECT_MEMORY_DIR/pir_skill_log.mdへ追記 |
| 20 | ステップ11 | retrospector起動（model切替条件） | L1が実行 | epic本体が実行（Phase3のメタretroとは別に、サブタスクごとの通常retroも必要） |
| 21 | ステップ11.5 | handoff.md完了判定 | L1が実行 | epic本体が実行 |
| 22-23 | ステップ12-13 | 最終サマリー・ウォークスルー提示 | L1が要約をepic本体に返す（epic本体はこの要約のみ受け取る） | epic本体が自ら生成・保持（後述の「コンテキストリセット境界喪失」の核） |

#### 定量的な負荷見積もり材料

- **ユーザーブロッキングゲート数**: pir2内に少なくとも4種類（4.6 プラン選択肢／6.5 未解決事項／7.5 refactor-advisorゲート／8-2-G続行可能ゲート）+ 条件次第で5.7破壊的変更ゲートの計最大5種類。Option Bでは L1 がこれらを保守的デフォルト選択＋`DEFERRED_USER_DECISIONS`に集約し、epic本体は**サブタスク完了ごとに1回**まとめて確認すればよい（epic SKILL.md 3-4、101-103行）。Option Aではこれらを**都度・N個のサブタスク×最大5ゲート=最大5N回**、epic本体が直接ユーザーと対話しなければならない。
- **ループカウンタの数**: REPLAN_COUNT・INNER_LOOP_COUNT・OUTER_LOOP_COUNT・IMPL_INDEX・REVIEW_INDEX・TEST_INDEXの6種類。Option Bでは各L1インスタンスのfresh contextに閉じる。Option Aではepic本体が**サブタスクの数だけ独立したこれら6カウンタの集合**を、cross-subtask汚染なく単一コンテキストで並行管理する必要がある。
- **コンテキストリセット境界の喪失（最大の構造コスト）**: L1は`subagent_type=general-purpose`のfresh起動であり、pir2の全内部ステップ（explorer要約・plan.md・各implementation-*.md・各review-*.md・各test-*.md・各ゲートのQ&A）はL1自身のコンテキストで消費され、epic本体へは**pir2ステップ12の最終サマリー1本のみ**が返る（telephone-game回避と同じ設計思想、pir2-protocol.md 15-17行の「オーケストレーターのcontextに各段階の全文が載ると後段で情報が欠落・歪曲する」目的そのもの）。Option Aはこの境界を除去するため、**epic本体の単一コンテキストにサブタスク数×pir2内部フェーズ数ぶんの情報が線形〜超線形に蓄積**する。zero-retryの最短経路でも1サブタスクあたり最低20+のオーケストレーション行為（起動・Read・Write・ゲート判定）が発生する（上表1〜23の各行）ため、N個のサブタスクでは単純計算で20N+のオーケストレーション行為がepic本体単一コンテキストに残ることになる。
- **Fan-Out Gate宣言の複雑性**: 7-2A（fan-out-gate.md 1-29行）の自己コミットメント宣言は「直前ターン本文に必ず書く」設計であり、Option Aでは**epic本体がサブタスクごとに独立してこの宣言を正確に発火**する必要がある。宣言の検証（`fan-out-gate.md`の違反パターン検出リスト: 「function_callsブロックが2ターン以上に分かれる」「観点を独自判断で減らした」等）もサブタスクごとに行う必要があり、cross-subtaskで宣言内容や観点集合を混同するリスクが新たに生じる（Option Bには存在しないリスク）。

**結論（事実ベースの整理、判断はしない）**: Option Aを採用すると、epic本体は「1 Agent起動＋1 return受信」（Option B、3-0）から、「pir2の23ステップ相当＋最大5種のユーザーブロッキングゲート＋6種のループカウンタをサブタスク数ぶん並行管理」に負荷が拡大する。この拡大の核心は**L1が果たしていた「fresh context = per-subtaskのコンテキストリセット境界」の喪失**であり、pir2-protocol.mdが明示するtelephone-game回避設計そのものをepicレベルで放棄することを意味する。この定量化は position ファイルの対立#1（「L0直接統率＝epicの価値提案`/pir2を丸ごとネスト再利用`を壊しL0 contextが爆発する」）の「爆発」を具体的なステップ数・ゲート数で裏付けるものである。

---

### 問い6: Phase 1.5 の実内容（前回は推測ベース）

| 項目 | 実ファイル該当箇所 | 確定事実 |
|---|---|---|
| 検出トリガー・確認フォーマット | epic SKILL.md ステップ2.5（69-77行）冒頭 | 「検出トリガー・確認フォーマットは pir2 の plan-choice-gate に倣います」と明記。**epic 専用の新規トリガーは定義されていない**。既存 `plan-choice-gate.md`（複数案提示／USER_DECISION_REQUIRED／スコープ縮小fallback／外部依存不足の4トリガー）をそのまま再利用する設計 |
| 提示内容 | epic SKILL.md 73行 | epic 本体が `{EPIC_RUN_DIR}/epic-plan.md` を Read し「**サブタスク一覧＋依存グラフ＋各 pir2 タスク記述**」をユーザーに提示して承認を得る |
| 承認前の進行禁止 | epic SKILL.md 73行 | 「承認前に Phase 2 へ進んではなりません」と明記（ブロッキング必須） |
| USER_DECISION_REQUIRED/EXPLORATION_NEEDEDの扱い | epic SKILL.md 75行 | epic-planner が出していれば必ずここで提示。ユーザーが分割方針を変えた場合は epic-planner を再起動 |
| 実行者の限定 | epic SKILL.md 77行 | 「このゲートは必ず epic 本体で行う（サブエージェントはユーザー対話不可のため）」と明記 |
| 破壊的変更の事前/事後ゲートの有無 | epic SKILL.md 全文をgrep相当で確認 | **「破壊的」という語はepic SKILL.md内に一切出現しない**。epic固有の破壊的変更事前ゲートは存在しない |
| pir2内部の破壊的変更ゲートの epic 配下での扱い | epic SKILL.md ステップ3-4（101-103行） | pir2 のステップ5.7（`destructive-change-check.md`「Auto modeでもこのユーザー確認は省略不可」88行、と明記される**強いブロッキングゲート**）が L1 内部で発火した場合でも、epic 配下では 3-4「ユーザーゲートの epic 本体への委譲(bubble-up)」の指示に従い、**L1は「保守的デフォルトを選び、その決定点をdeferred-decisions.mdに記録しDEFERRED_USER_DECISIONSに列挙する」**——つまり pir2単独運用ならAuto modeでも即時ブロックされる破壊的変更ゲートが、epic配下では「保守的デフォルト選択＋事後報告（サブタスク完了ごとの一括報告）」に**格下げされる** |

**確定した事実（重要）**: Phase1.5は「分割方針」レベルの事前承認ゲートであり、個々のサブタスク内部の実装内容の破壊性（OpenAPIリネーム・golden波及・controller大量変更等）に対する事前ゲートではない。両者は別レイヤーのゲートであり、**pir2単体では「Auto modeでも省略不可」と明記される破壊的変更ゲートが、epic配下では明示的にbubble-up経由の事後報告に置き換わる**ことが実ファイル記述から確定した（前回positionのM7「破壊的変更ゲートが事後承認化」指摘の直接的な実装根拠）。

---

### 補足情報

- **本探索で「実装・ファイル編集・git状態変更」は一切行っていない**（Read/Bash mkdirのみ使用、mkdirはRUN_DIR確保のためのスクラッチ操作）。
- **視覚的一次情報（スクリーンショット等）は本タスクに含まれていない**ため、視覚情報との自己整合チェックは非該当。
- 問1・問3で述べた「Agent ネスト起動の同期ブロッキング性」は本探索の**推測**であり、環境のツール仕様書（本エージェント自身が渡された tool 定義）にも Agent ツールの非同期監視手段（`run_in_background`/Monitor 相当）は明記されていない、という間接証拠に基づく。これは deliberator/synthesizer が「M1はフリーズ検知に効かない」と断定してよい根拠としては**中程度の確度**であり、実機検証（1 unit の epic dry-run でL1が明示的にフリーズした際、epic本体側にAgent呼び出しがタイムアウトなく返るか/返らないかを観測）が必要。position ファイル自身も同じ論点を「追加探索が要る論点 ②」として未解決に残していた。
- 検索した主なキーワード: 「破壊的」（epic SKILL.md 内 0 件）、「timestamp」「Phase遷移」（epic SKILL.md 内 0 件）、「handoff」（epic SKILL.md 内 0 件）。「存在しない」と結論した箇所はいずれもこの grep 相当確認（ファイル全文読了による目視 grep）に基づく。
- `experimental.md` の `epic-orchestrator-nested-pir2` セクション（218-279行）には既に M3/M9相当のメトリクス（「サブタスク境界の結合不整合の発生回数」「`DEFERRED_USER_DECISIONS`の発生・ブロッキング化回数」）が Metrics として定義済みだが、これらを収集する**実装（epic-runs.md への具体的な書き込みロジック）はまだ存在しない**（Metrics定義とImplementationの間にギャップがある）。

### 呼び出し元への依頼

- 本探索は read-only 調査のみで完結しており、追加 explorer の並列起動は不要と判断する。
- 「Agent ネスト起動の同期/非同期特性」は코드探索では確定できない実機挙動の問題であり、次の deliberator ラウンドで扱う場合は「推測」であることを明示した上で、可能なら 1 unit の epic dry-run による実機検証をユーザーに提案してほしい（tech-validator 領域ではなく、Claude Code プラットフォーム仕様の確認に近いため、必要なら `WebSearch`/公式リリースノート確認、または実行観測が適切）。
