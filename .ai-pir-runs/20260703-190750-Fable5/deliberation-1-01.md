## 熟考レポート（ROUND 1 / 01）: /epic（＋ネスト多エージェント機構）の完成形ワークフロー設計

### レンズ
第一原理・機序 / 反証・レッドチーム / 二次波及・境界条件 / 設計統合（完成形フロー仕様）を fable-solo で内省的にすべて通す。成果物は「改善リスト」ではなく「実行順に追える1本の完成形フロー設計仕様」。

---

### 思考の起点（前提の確認）

**context から確定的に言える事実（出典つき）**

| # | 事実 | 出典 |
|---|------|------|
| F1 | L1（ネスト pir2 ランナー）は fresh-context の Agent 呼び出しで、per-subtask のコンテキストリセット境界として機能。epic 3-2 は L1 return に RUN_DIR＋変更ファイル一覧を**前提**にしているが、return フォーマット規定はどこにも無い（ギャップ） | exp-01 問1 |
| F2 | Option A の実コスト＝pir2 約23ステップ＋最大5種ブロッキングゲート＋6種ループカウンタ×サブタスク数 N を L0 単一 context で並行管理。核心はコンテキストリセット境界の喪失（telephone-game 回避設計の放棄） | exp-01 問5 |
| F3 | M2 の git-diff 集合照合は hook も LLM 判断も不要の純 bash で**完全に可能** | exp-02 C |
| F4 | `SubagentStop` hook は `agent_transcript_path` / `last_assistant_message` / `agent_type` を返す。tool_uses/duration は直接は無く、transcript JSONL の jq 解析で決定論算出（**JSONL 実構造は未検証**）。`decision:"block"` でサブ本人に再指示可能 | exp-02 A/B |
| F5 | `PostToolUse(matcher=Agent)` の `tool_response` に `totalToolUseCount`/`totalDurationMs`/`status` が乗るのは**フォアグラウンド実行時のみ**。v2.1.198+ は既定バックグラウンド（実機 2.1.199 確認済み）。強制同期は `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`（セッション全体に効く） | exp-02 §2 |
| F6 | #44783（並列 fan-out ハング）は CLOSED/NOT_PLANNED（stale bot）。単一サブエージェントでも再現報告あり＝並列固有ではなく親↔サブ結果受け渡しチャネルの脆弱性。本リポ PIR² は既に並列 fan-out を採用済み＝リスクは既負担 | exp-02 §4 |
| F7 | pir2 デフォルト actor（implementer-subagent）では implementer→reviewer 間に機械照合ステップが存在しない。shard/sequential actor には統合確認の決定論チェック先例が既にある（`implementation-delegation.md` 57-65 / 103-110 行） | exp-01 問2 |
| F8 | epic-runs.md の記録は Ti↔サブ RUN_DIR 対応のみ。timestamp / Phase / handoff / 破壊的 の語は epic SKILL.md に 0 件 | exp-01 問3/6 |
| F9 | pir2 の破壊的変更ゲート（5.7、Auto mode でも省略不可）は epic 配下では 3-4 の bubble-up により「保守的デフォルト＋事後報告」へ**格下げ**される（M7 の実装根拠） | exp-01 問6 |
| F10 | handoff.md はプロジェクト単位1ファイル。epic 並列時は複数 L1 の同時書き込み競合が構造的に起こりうる | exp-01 問4 |
| F11 | durable resume（決定論リプレイ）/ Saga 自動補償 / 真のブロッキング HITL は本環境で構造的に不可。LangGraph 型「台帳ベース手動 resume」は要適応で可能。Claude Code ネイティブ OTel（beta）は `agent_id`/`parent_agent_id` で L0→L1→L2 を計装可能 | exp-03 |
| F12 | epic は executions 0（実験段階）。experimental.md にはメトリクス定義済みだが収集実装ゼロ | exp-01 補足 / exp-03 |
| F13 | 本リポに SubagentStop 使用例は無し。既存 hook 設計パターン（jq・fail-open・`~/.claude/logs/` 退避・`{"decision":"block"}`）は転用可能 | exp-02 §5 |

**前提として置くもの（崩れると結論が変わる仮定）**

- P1: サブの完了報告は claim であって ground truth ではない（前回 position の認識論的前提を継承）。
- P2: 全レイヤ（L0/L1/L2）は**同一 working tree を共有**する。→ git がレイヤ横断の共有 ground truth になる（本設計の要）。
- P3: 初回題材は運用者が選べる（線形・additive-only 寄りに寄せられる）。
- P4: epic は対話セッションで実行される（無人運転は対象外）。
- P5: L1 が SKILL.md 全文を自律オーケストレーションできる（**未実証**。移行パス G1 で検証し、決着トリガに接続）。

**前回の到達点とゲート指摘（今回上積みすべき点）**

前回 position は「計器 vs 堅牢化」の framing・M1–M12・4対立までで、**フェーズ単位の完成形フロー仕様・対立の決着・実装アンカーの実現可能性評価・移行パス**が未提出。今回はこの4点を、今回探索3本の確定事実で埋める。

---

### 段階的推論（設計を導出する5段）

**段1: 第一原理 — 「検証は claim が届く場所でなく、ground truth が在る場所で行う」**

観測された失敗2件（事象X=捏造、事象Y=ゾンビ成功）の機序は「自己申告を事実扱いした」こと。分散システムの原則で言えば、信頼できない語り手の報告は境界で外形照合するしかない。ここで本環境固有の決定的な構造がある: **L0/L1/L2 は同一 working tree を共有する（P2）**。つまり L2 のファイル操作は L0 から `git diff --name-only` 一発で**直接**観測できる。前回対立#3の「L0 は L2 の操作を直接見られない」は、ファイル副作用に関する限り**誤った前提**だった。
→ 導出される原則: **claims-up / evidence-local-pull**。上に運ぶのは軽量な claim（ファイル名リスト・カウンタ・VERDICT）だけ。証拠は各境界の検証者が git から O(1) で**引く**。証拠は context を一切上らない。
（自己点検: この原則が効かない領域＝ファイル副作用を持たない純分析サブタスク。→ 契約に ARTIFACTS リストを含め `test -f` で存在検証する補完を後述。それでも「読んだが結論を捏造」は決定論では捕まらない＝残存限界として明示する。）

**段2: 対立#1の決着 — Option B を完成形として採用（A は per-node フォールバックに降格して生存）**

- F2 により A のコストは N に比例して増える構造コスト（23ステップ×N・5ゲート×N・6カウンタ×N の単一 context 管理）。
- **機序からの決定打**: 今回恐れている失敗クラス（捏造）は「context 圧・resume 真空 → 穴埋め」で発生する（前回 position の事象X機序）。Option A は L0 の context 圧を構造的に増大させる＝**守ろうとしている失敗の発生確率を上げる向きの設計**。B＋境界計器は context 圧を増やさずに検証だけ足す。
- D-03 の A 寄り論拠「脆弱な L1 の上に信頼性を積むと不信頼性を継承する」への応答: 本設計は L1 の上に信頼性を**積まない**。L1 の**外側**（L0 境界）に、L1 が偽装できない ground truth（git）での検証を置く。継承論が成立するのは L0 が L1 の self-report を信頼する場合のみで、本設計はそれを禁止している。
- よって**時間軸付き両論（前回）を更新**: 「試験段階は B、恒久時に A 再評価」ではなく、「**B が恒久アーキテクチャ。A は N=1 相当の per-node inline フォールバック（A-lite）としてのみ生存**」。A のコストが N 比例である以上、恒久・大規模ほど A は不利になる（前回の直感と逆）。
- **客観的決着トリガ（P5 の反証条件）**: G1 dry-run で L1 return に M1 契約の必須見出しが揃わず、起動プロンプト修正を1回挟んでも連続2回契約不履行なら、「L1 自律オーケストレーション不能」と判定し、epic アーキテクチャ再設計（A-lite 常用化を含む）を**ユーザーに判断上程**する（無言切替はしない）。
- 副産物: **C1（inline フォールバック造語）の是正**は「A-lite の仕様を実際に定義する」ことで達成する（後述 §5-2d）。非在概念を消すのでなく、定義を与えて実在化する。

**段3: 対立#2/#3/#4 の決着**

- **対立#2（fan-out）**: 決着＝「**試験段階は幅1（直列）既定。並列 ≤2 は客観条件を全て満たしたときの opt-in**」。根拠: (i) F6 により直列でもハングリスクはゼロにならない（単一サブでも再現）＝「直列なら安全」も「並列だから危険」も過大評価で、争点は露出面の大小と**診断可能性**。実験段階は速度より診断（どのノードで何が起きたか）を買う。(ii) 新たに浮上した「M2 フォアグラウンド要件 vs 並列」の干渉は、**M2 主経路を SubagentStop（B経路、実行モード非依存）にする**ことで解消——`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` のグローバル設定は採用しない。決定的な二次波及根拠: この env はセッション全体の background 機能を殺すため、CLAUDE.md が必須とする「codex MCP 相談は background Agent 経由」を**破壊する**（クロス SSOT 違反）。よって A経路（PostToolUse メトリクス）は「フォアグラウンドで走った場合の補完クロスチェック」に格下げ。
  - **opt-in 解禁の客観条件（全て AND）**: ①直列 epic 完走2回でクリーンな計器データ、②hook が block モード（W4）で稼働、③epic-planner が対象ノード対の書込集合非交差を宣言（M11）、④Phase 1.5 でユーザー明示承認、⑤バックグラウンド起動時のハートビート観測（サブ RUN_DIR の next-steps.md mtime）が G1 で実証済み。
- **対立#3（summary-up vs evidence-up）**: 段1の原則で**解消**——第三の解「claims-up＋evidence-local-pull」。検証は claim が越境する**全境界**で各検証者が実施: L2→L1 は pir2 新ステップ 6-3（pir2 本体が implementer の claim を git 照合）、L1→L0 は epic 3-2（epic 本体が L1 の集約 claim を起動前ベースラインとの delta で照合）。二重検証は冗長ではない——各境界に別の「信頼できない語り手」がいる（L0 境界では L1 自身が語り手）。コストは境界あたり bash 数行・context O(1)。
- **対立#4（resume/timeout の程度）**: 決着＝「**台帳ベース部分 resume（LangGraph 型手動チェックポイントの適応）を完成形とし、決定論リプレイ級は仕様外と宣言**」（F11）。resume 時の再構成は**記憶からではなく台帳＋git から**行う（事象X の上流＝resume 真空への直接対処）。resume 続行は必ずユーザーゲートを通す（無言 auto-resume 禁止——事象X は resume 直後に起きた）。timeout は決定論ウォッチドッグ不可（前回 D-02）を受け、(a) 台帳 timestamp＋ハートビート mtime による**手動外形診断手順の文書化**（19分迷走→1分の台帳チェックへの変換）と、(b) バックグラウンド起動時代は L0 が非ブロックで居られる事実（F5）を活かした「ユーザーへのストール報告」で代替。自動 kill は持たない（残存限界）。

**段4: M7（破壊的ゲート格下げ）の解——「選択的早期 return」プロトコル**

F9 の格下げは「L1 はユーザーと対話できない」制約由来。exp-03 の HITL 分析が示すとおりブロッキング一時停止は不可だが、**「完了させずに制御を L0 に返す」は可能**（pir2 の EXPLORATION_NEEDED と同型）。そこで decision 系を**可逆性で二分**する:
- 可逆な選択（命名・実装方式等）→ 従来どおり保守的デフォルト＋DEFERRED_USER_DECISIONS（非ブロッキング委譲）。
- **不可逆な操作（destructive-change-check.md のフラグ a-e 該当）→ L1 は続行せず `STATUS: ABORTED_PENDING_DECISION` で早期 return**。L0 がユーザーゲートを開いて承認後、承認内容を注入して再起動。
さらに Phase 1（epic-planner）でサブタスク単位の破壊的分類を事前に行い、Phase 1.5 の DAG 承認に「破壊的サブタスクの事前明示承認」を含める。→ 事前承認済み範囲内なら L1 は 5.7 を通過でき、早期 return は「計画時に予見できなかった破壊的操作」だけに限定される（誤 ABORT の頻度を構造的に抑える）。可逆性という客観基準で二分するため、判断の恣意性が入らない。

**段5: 以上を1本のフローに統合**

段1〜4の決着を、既存 epic SKILL.md のステップ構造（exp-01 で確定した行番号アンカー）に写像し、Phase 0/1/1.5/2/3＋境界契約の完成形仕様として次章に記述する。

---

## 完成形ワークフロー設計仕様（本体）

### §0. アーキテクチャ総括 — 3層と信頼モデル

```
L0: epic 本体（メイン Claude）      … ユーザー対話の一極・DAG 進行・境界検証・台帳
L1: ネスト pir2 ランナー（fresh）    … /pir2 全13ステップの自律オーケストレーション（信頼しない語り手）
L2: explorer/planner/implementer/… … pir2 配下の専門サブ（信頼しない語り手）
共有 ground truth: 同一 working tree の git ＋ {RUN_DIR}/{EPIC_RUN_DIR} のファイル群
```

**信頼モデル**: 各層の return は claim。検証は「claim が越境する境界」ごとに、その境界の受け手が**ローカルの ground truth（git / test -f / hook が書いた metrics ファイル）を引いて**決定論照合する。LLM 判断は検証経路に挟まない。検証3層構成（exp-03 #7 の適応）:

| 層 | 担い手 | 捕捉する誤り |
|---|---|---|
| 決定論 | git 集合照合・artifact 存在・tool_use floor（hook） | 行為の捏造（phantom claim）・ゾンビ成功 |
| LLM 判定 | reviewer（L2）・Phase 3 境界レビュー（L0） | 結論の質・結合整合 |
| 人間 | Phase 1.5 ゲート・失敗時ゲート・DEFERRED 集約 | 方針・不可逆判断 |

### §1. L0↔L1↔L2 境界契約（本設計の背骨）

#### 1-1. 起動契約（L0→L1）— epic SKILL.md 3-0（83-87行）を置換

起動プロンプトに以下を**必須項目**として明示（現状の「SKILL.md を Read して従え」だけの記述を置換。F1 のギャップ解消）:

1. `SUBTASK_ID`（Ti）・タスク記述・完了条件（epic-plan.md 由来）
2. `EPIC_RUN_DIR` と、サブ RUN_DIR 命名規約（`run-dir-base.md` SSOT に従う。`cut -c1-40` 統一 = C4 非再導入）
3. **`HANDOFF_PATH` 上書き**: `{サブRUN_DIR}/handoff.md` を使うこと（プロジェクト単位デフォルト禁止。F10 の競合の構造的排除 = M9）
4. 先行サブタスクの**検証済み**成果: RUN_DIR パス＋検証 PASS 済み変更ファイルリスト（L1 の explorer が拾う手がかり）
5. **return 契約**（下記 1-2 の必須見出し。「返り値冒頭に必ずこの見出し群を出力せよ」）
6. **ゲートポリシー**: 可逆判断→保守的デフォルト＋deferred-decisions.md 記録（既存 3-4）／破壊的フラグ a-e 該当かつ Phase1.5 事前承認範囲外→**完了させず `STATUS: ABORTED_PENDING_DECISION` で即 return**（M7）
7. ループ上限の確認（pir2 既存 max3 の再掲）と、再実行時は「前回試行の部分差分が working tree に残存している。explorer による現状把握から始めよ」の注記（非冪等性の明示プロトコル化。exp-03 §4）

#### 1-2. return 契約（L1→L0）— 機械 grep 可能な必須リテラル見出し（M1）

pir2 ステップ12 の最終サマリーは既にほぼ全フィールドを含む（F1）ため、実質は**フォーマットの固定化**（exp-03 #5「リテラルキーワード契約の必須見出し化」）:

```
### EPIC_TELEMETRY
- SUBTASK_ID: T3
- STATUS: COMPLETED | ABORTED_PENDING_DECISION | FAILED
- FINAL_PHASE: explore|plan|implement|review|test|retro|complete
- VERDICTS: review=PASS|FAIL|N/A, test=PASS|FAIL|N/A
- LOOPS: INNER=n, OUTER=n, REPLAN=n
- CLAIMED_FILES: <改行区切りリスト or "none">
- ARTIFACTS: <サブ RUN_DIR 内の主要成果物パス（純分析タスク用）>
- RUN_DIR: <絶対パス>
### DEFERRED_USER_DECISIONS
<リスト or "なし">
```

**M1 の正直なスコープ**（exp-01 の警告を確定的に扱わない）: return テレメトリは「完了したが内容が偽/矛盾」（事象Y型・事象X型の事後検知）に効く。**L1 が return しないフリーズには原理的に効かない**——フリーズ検知は台帳 timestamp＋ハートビート mtime の外形診断（§8）が担う。

#### 1-3. L0 検証パイプライン（L1 return 受領直後）— epic SKILL.md 3-2（93-95行）に新設（M2/M12）

受領のたびに以下を**この順で**実行（全て決定論・context O(1)）:

1. **契約存在チェック**: 必須見出しを grep。欠落→サブ RUN_DIR の成果物ファイル（walkthrough/summary/next-steps.md）を直接 Read して再構成を試みる（artifact system が第二の情報源。プラットフォームの return 切り詰めに対する耐性）。再構成不能→失敗パスへ。契約違反は台帳に記録（G1 の較正データ）。
2. **git 集合照合（C経路・最重要）**: 起動前に保存した `pre-{Ti}.list`（`git diff --name-only`＋untracked）と現在の `post-{Ti}.list` の差 `delta` を計算し:
   - `CLAIMED_FILES ⊆ post`（各 claimed ファイルが実際に dirty）… 違反＝**PHANTOM_CLAIM（捏造シグネチャ・hard fail）**
   - `delta ⊆ CLAIMED_FILES`… 違反＝**UNDECLARED_CHANGE（warn。formatter 副作用等がありうるため非ブロッキングで台帳記録＋ノード報告に含める。ただし他ノードの宣言書込集合と交差する場合のみブロッキングゲート化）**
   - CLAIMED_FILES=none かつ delta 非空 → UNDECLARED。none かつタスクが編集想定 → PHANTOM 扱い（`NO_OP_JUSTIFIED` トークン宣言時は免除）
3. **artifact 存在チェック**: ARTIFACTS の各パスを `test -f`（純分析サブタスクでも検証が空洞化しない）
4. **floor チェック（B経路・hook 稼働時のみ）**: `{cwd}/.ai-pir-runs/subagent-metrics.jsonl`（hook が追記。§7）から該当 agent_id 行を読み、役割別 floor と突合
5. **STATUS 不変条件（M12）**: `STATUS=COMPLETED` ⇒ `review=PASS ∧ test∈{PASS,N/A}` でなければ done 扱いしない（「reviewed 未達なら done にしない」）
6. **台帳追記（M3/M9）**: VERIFY 結果を epic-runs.md に1行イベントとして追記（§8 スキーマ）

**失敗パス**: PHANTOM_CLAIM / floor 違反 / STATUS 不整合 → **再実行は1回まで**、起動プロンプトに検証レポートを逐語注入（「あなたの前回 return は検証と不一致: …」）。原因が特定されている（不一致そのものが原因）ためブラインドリトライ禁止と非衝突。2回目も失敗 → `NODE_FAILED` として台帳記録し、**ユーザーゲート**: (a) 手動調査 / (b) 当該ノードをスキップし依存下流をブロック（独立ノードは続行可） / (c) epic 中止。補償が話題になる場合は `git diff` の全 hunk をユーザーに提示して判断を仰ぐ（**自動 restore は絶対にしない**。CLAUDE.md git ルール遵守＝人間ゲート付き補償、exp-03 Saga 適応）。

#### 1-4. L2→L1 境界 — pir2 SKILL.md 新ステップ「6-3: 決定論的完了検証」（共通層・M2 の本丸）

**epic 専用ではなく pir2 共通層に置く**（観測された失敗2件は epic 外の素の pir2 で起きた——計器は共通層にないと当の失敗を捕まえられない。前回 position の最高レバレッジ判断を継承）。仕様:

- 挿入位置: pir2 SKILL.md ステップ 6-1（implementer 完了）と 7（reviewer 起動）の間（exp-01 問2 確定アンカー）。
- 内容: pir2 本体が implementer 起動前に pre-set を記録し、完了報告後に `implementation-{NN}.md` の変更ファイルリストと git delta を 1-3 節 2. と同一規則で照合。
- PHANTOM_CLAIM → implementer 再実行1回（不一致理由を注入）。再失敗 → reviewer を起動**せず**ユーザーへ（捏造の上にレビューを積まない。事象Xの「implementer claim と reviewer verdict の矛盾に解決経路なし→迷走」の連鎖を入口で切断）。
- 既存の shard/sequential 統合確認（`implementation-delegation.md` 57-65/103-110 行）を「デフォルト actor にも一般化した」と位置づけ、同 reference から相互参照（新規発明でなく既存先例の一般化＝既存パターン整合）。

### §2. Phase 0 — 初期化・resume 判定・ベースライン記録

（現行 SKILL.md の初期化ステップ相当を拡張。実挿入行は実装時に確認——exp-01 は 3-0 以降のみ行番号確定）

1. `EPIC_RUN_DIR` 確定（`run-dir-base.md` SSOT・`cut -c1-40`）。
2. **resume 判定（M9）**: 既存 EPIC_RUN_DIR に未完了台帳があれば、**記憶でなく台帳＋git で**状態を再構成: 各 Ti の台帳 status と git 実状態（claimed files が dirty か）を突合 → 再構成結果と再開プラン（done-verified はスキップ／running は不明扱いでサブ RUN_DIR の next-steps.md を読んで再実行 or 継続を提案）を**ユーザーに提示して承認を得てから**再開。無言 auto-resume 禁止（事象X の再発防止線）。
3. **ベースライン記録**: `git rev-parse HEAD`＋`git status --porcelain` を `{EPIC_RUN_DIR}/state/baseline.txt` に保存。dirty 開始なら台帳に明記（M2 集合算術の前提）。
4. **計器レベル判定**: settings.json に SubagentStop hook が設定済みかを確認し、台帳に `INSTRUMENTS: FULL | GIT_ONLY` を記録（hook 未導入でも C経路＋artifact 検証で成立する**グレースフルデグラデーション**）。

### §3. Phase 1 — epic-planner（分割・DAG）への追加要件（epic-planner.md へ）

epic-planner の出力（分割レポート）に以下を必須列として追加:

1. **サブタスク数 hard-cap**（M4 配線。初期値は仮置き≤5、値は G2 で較正——値の根拠が無いことを明記）
2. **DAG 形状制約（M10）**: tree または線形のみ。fan-in（合流）ノードが必要な分割になった場合は自動採用せず `USER_DECISION_REQUIRED` としてフラグ（merge 意味論は未実装のため）
3. **推定書込集合（M11）**: 各 Ti が触るファイル領域の見積り。交差可能性あり→依存辺として直列化（既存の「暗黙依存」直列化の入力を明文化）。fan-out 解禁後は非交差宣言が並列の必要条件になる
4. **破壊的分類（M7）**: 各 Ti を destructive-change-check.md のフラグ a-e で事前分類
5. **完了条件の型**: 各 Ti に「編集想定（CLAIMED_FILES 必須）or 分析想定（ARTIFACTS 必須）」を指定（検証の空洞化防止）

### §4. Phase 1.5 — 分割確認ゲート（既存 2.5 / 69-77行 を拡張）

既存（plan-choice-gate 準拠・ブロッキング・L0 専任）に以下を追加提示:

1. **破壊的サブタスクの事前明示承認**（M7 の前半。ここで承認された範囲は L1 が 5.7 を通過できる。範囲外の破壊的操作だけが早期 return になる）
2. **並列化プラン**: 直列（既定）か、opt-in 条件（§段3 対立#2 の5条件）を満たす場合のみ幅≤2 の並列提案
3. **統合検証コマンド**（Phase 3 の決定論バックストップ用）: プロジェクトのビルド/テストコマンドをユーザーに確認し台帳へ記録（epic は汎用スキルでありコマンドをハードコードできないため、ここで確定するのが唯一の決定論的な置き場）
4. timeout 挙動: 対話セッションでユーザー入力待ちは自然にブロック＝timeout-block は本設計では自明に充足。無人運転は非サポートと明記（AWS 定石の適用範囲の正直な限定）

### §5. Phase 2 — DAG 実行ループ（3-0〜3-5 の完成形）

ノードごとに（既定は直列・DAG 順）:

- **2a. 起動前**: 台帳に `NODE_START`（Ti, timestamp, HEAD, pre_dirty 数）を追記し、`state/pre-{Ti}.list` を保存
- **2b. 起動**: §1-1 の起動契約で L1 を Agent 起動（実行モードはプラットフォーム既定に任せる。強制同期 env は採用しない——§段3 の codex 干渉根拠）
- **2c. return 受領**: §1-3 検証パイプライン実行 → `NODE_DONE`（verified）/ `NODE_FAILED` / `NODE_ABORTED`
- **2d. ABORTED_PENDING_DECISION 受領時**: L0 がユーザーゲートを開き、承認内容を注入して同ノードを再起動（これは失敗でなく設計どおりの往復。台帳に DECISION イベント記録）。**A-lite（inline フォールバック、C1 是正の実定義)**: 深さバジェット超過時、または L1 が契約を履行できない場合、L0 が当該1ノードに限り pir2 SKILL.md を直接実行する。ユーザーに宣言してから移行し、台帳に `FALLBACK_INLINE` を記録
- **2e. deferred 集約＋矛盾検出**（exp-03 #10 の適応）: ノード完了ごとに DEFERRED_USER_DECISIONS を集約し、**依存下流の起動前に**蓄積 deferred 間の同一ファイル/同一トピック矛盾を照合（矛盾あり→下流起動前にユーザーゲート）
- **2f. fan-out（end-state・opt-in 時のみ）**: 幅≤2。バックグラウンド起動で L0 は非ブロックを保ち、サブ RUN_DIR の next-steps.md mtime をハートビートとして観測。**並列時の git 検証は集合算術が壊れる**（両 L1 が同時に tree を汚すため delta の帰属が不定）→ 帰属規則を「`delta ∩ 宣言書込集合(Ti) = CLAIMED(Ti)`、全宣言集合外の delta はアラート」に切替（書込非交差が並列の前提だからこそ成立。副産物として M11 のランタイム検知が M2 の自然な拡張で手に入る）

### §6. Phase 3 — 統合検証・集約報告・retro（ステップ4 / 113-115行 を拡張）

1. **決定論バックストップ**: Phase 1.5 で確定した統合検証コマンドを実行（全サブの結合後に1回。exp-03 #7 のギャップ充填）。未確定なら「LLM 目視 diff レビューのみ＝劣化モード」と台帳に明記
2. 既存の LLM 結合レビュー（境界インターフェース・命名・未接続）は継続（3層構成の第2層として正当）
3. DEFERRED_USER_DECISIONS の最終一括報告＋矛盾検出結果
4. **メトリクス収集の実装**（F12 のギャップ充填）: experimental.md の epic 実験セクションに定義済みの各メトリクスを、台帳イベント＋subagent-metrics.jsonl から機械集計して記録（Metrics 定義と Implementation の接続）
5. retrospector 起動: `PROJECT_MEMORY_DIR` を渡し、ループ系 param は `N/A` 明示（前回 C5 最小案の継承。無理な写像をしない）

### §7. hooks / settings.json 仕様（M2 インフラ・共通層）

**新規**: `.claude/lib/subagent-verify-hook.sh`（`lib/` 配置＝link.sh の symlink 対象→ **`cd -P` 必須**、CLAUDE.md 編集注意の遵守）＋ settings.json に `SubagentStop` エントリ追加。

- **Stage A（log-only・先行導入)**: `agent_transcript_path` を jq で解析し tool_use 数・duration を算出、`{cwd}/.ai-pir-runs/subagent-metrics.jsonl` に `{ts, agent_id, agent_type, tool_uses, duration_s}` を追記するのみ。判定しない。fail-open（jq 不在/transcript 不読 → exit 0）・`~/.claude/logs/` にデバッグ退避（F13 の既存パターン踏襲）
- **Stage B（block モード・JSONL 実構造検証後に昇格)**: 役割別 floor 表と突合し、違反時のみ `{"decision":"block","reason":"tool_uses=0 で完了主張。実際にツールで作業せよ。作業不能なら理由と NO_WORK_POSSIBLE を宣言せよ"}` を返してサブ本人に再指示（親 context 到達前に足止め＝F4 の decision 制御）。`stop_hook_active` による one-shot guard で 1詰まり1回に制限（parse-failure-continue-hook の loop guard 先例踏襲＝ブラインドリトライ禁止整合）
- **floor 表（初期値・G2 で較正）**:

| agent_type（matcher） | floor | 根拠 |
|---|---|---|
| explorer | tool_uses ≥ 2（うち Read/Glob/Grep ≥1） | 調査ゼロで探索レポートは書けない（事象Y直撃） |
| implementer | Edit/Write ≥ 1（NO_OP_JUSTIFIED 宣言時は免除） | 編集ゼロの完了主張＝phantom |
| tester | Bash ≥ 1 | 実行ゼロの検証は成立しない |
| reviewer | Read ≥ 1 | コードを読まないレビュー禁止 |
| general-purpose（L1）・未登録型 | floor なし（logging のみ） | 推論系エージェントの正常0を誤検知しない |

- **A経路（PostToolUse matcher=Agent）**: フォアグラウンド実行時に `totalToolUseCount` 等をクロスチェックとして同 jsonl に追記する**任意の補完**。グローバル同期化 env は設定しない（codex background 要件と衝突・§段3）

### §8. 観測性 — 台帳スキーマと OTel

**epic-runs.md（M3/M9 統合台帳・単一 SSOT）**: 人間可読かつ grep 可能な「1イベント1行・固定カラム」形式（jsonl 併走はさせない——二重管理の SSOT 違反回避）:

```
| 2026-07-03T19:30:12 | NODE_START | T2 | head=abc1234 pre_dirty=3 |
| 2026-07-03T19:48:02 | NODE_RETURN | T2 | status=COMPLETED verdicts=review:PASS,test:PASS loops=1/1/0 |
| 2026-07-03T19:48:05 | VERIFY | T2 | PASS claimed=4 delta=4 |
```

イベント語彙: `EPIC_START / RESUME_RECONSTRUCTED / PLAN_DONE / GATE_APPROVED / NODE_START / NODE_RETURN / VERIFY / NODE_DONE / NODE_FAILED / NODE_ABORTED / DECISION / DEFER / FALLBACK_INLINE / PHASE3_START / INTEGRATION / EPIC_END`。

**フリーズ外形診断手順**（references に文書化）: 台帳の最終 NODE_START からの経過と、当該サブ RUN_DIR の next-steps.md mtime を見る——2分で「どのノードのどの phase で止まったか」まで絞れる（19分迷走の再演防止。自動 kill はできない＝手順の限界も併記）。

**OTel（任意層）**: `CLAUDE_CODE_ENABLE_TELEMETRY=1`＋`CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1` で `agent_id`/`parent_agent_id` span が得られる（F11）。**台帳が SSOT・OTel は補完**（どの M も OTel に依存させない）。採用具体化時は tech-validator 委譲（exp-03 の推奨に従う）。

### §9. 4対立の決着まとめ

| # | 対立 | 決着 | 根拠 / 客観トリガ |
|---|------|------|------|
| 1 | Option A vs B | **B を恒久採用。A は per-node A-lite フォールバックに降格して生存（C1 是正を兼ねる）** | F2（A のコストは N 比例の構造コスト）＋機序（A は捏造の発生条件=context 圧を増やす）＋F3/F4（B の検証可能性実証）。**トリガ**: G1 で契約不履行が是正1回を挟んで連続2回→A-lite 常用化をユーザー上程 |
| 2 | fan-out 既定 OFF vs ≤2-3 opt-in | **試験段階=幅1直列既定。幅≤2 opt-in は5条件 AND で解禁**（§段3） | F6（直列でもハング可能性は残る＝安全神話の否定、争点は診断可能性）。M2 主経路を SubagentStop にすることでフォアグラウンド要件との干渉を解消。`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` 全域設定は codex background 必須ルールと衝突するため不採用 |
| 3 | summary-up vs evidence-up | **第三の解「claims-up＋evidence-local-pull」で解消** | P2（全層が同一 working tree 共有＝git は層をまたぐ ground truth）。証拠は context を上らず各境界で引く。検証は L2→L1（pir2 6-3）と L1→L0（epic 3-2）の二重、各境界に独立の語り手がいるため冗長でない |
| 4 | resume/timeout の程度 | **台帳ベース部分 resume＋ユーザーゲート付き再開を完成形と宣言。決定論リプレイ・自動 timeout kill は仕様外** | F11（プラットフォーム構造制約）。resume 再構成は台帳＋git のみから（記憶禁止）。timeout は外形診断手順の文書化で代替 |

### §10. SSOT アンカー表＋実現可能性評価

| 機構 | 着地点（名指し） | 新規/継承/再利用 | 実現可能性 |
|---|---|---|---|
| M1 return 契約 | epic SKILL.md **3-0**（83-87行置換）＋新規 `.claude/skills/epic/references/l1-contract.md`（起動/return 契約と検証パイプラインの SSOT。pir2 の references/ 慣習に整合） | 新規（フォーマット固定。pir2 ステップ12 が既にフィールドを持つため実質は明文化） | **可能**（プロンプトレベル。切り詰めリスクは artifact 再構成で緩和） |
| M2 git 集合照合 | epic SKILL.md **3-2**（93-95行に検証パイプライン新設）＋ pir2 SKILL.md **6-1→7 間に新ステップ 6-3**＋`implementation-delegation.md` 統合確認の一般化として相互参照 | 継承の一般化（shard 統合確認の先例あり=F7） | **完全に可能**（F3。hook 不要・純 bash） |
| M2 floor（hook） | `.claude/lib/subagent-verify-hook.sh`（新規・cd -P 必須）＋ `.claude/settings.json` hooks.SubagentStop | 新規（本リポ初の SubagentStop=F13。既存 hook パターン転用） | **条件付き**（B経路: transcript JSONL 実構造の1サンプル検証が前提=F4。A経路: フォアグラウンド限定=F5、かつ全域同期化は codex ルールと衝突するため補完のみ） |
| M3/M9 台帳 | epic SKILL.md **3-5**（105-107行をイベント台帳スキーマに置換。旧「Ti↔RUN_DIR のみ」記述は残さず置換=dead text 温存禁止） | 新規スキーマ（run-dir 慣習継承） | **可能**（自明） |
| M9 handoff 隔離 | epic SKILL.md **3-0** 起動契約に HANDOFF_PATH 上書き | 継承の適応（pir-handoff.md のプロジェクト単一制約=F10 への対処） | **可能**（プロンプトレベル。L1 が遵守するかは G1 で確認） |
| M7 破壊的事前分類＋早期 return | `epic-planner.md`（分類列）＋ epic SKILL.md **2.5**（事前承認）＋ **3-0**（早期 return 指示）＋ return 契約 STATUS | 新規（destructive-change-check.md のフラグ体系を再利用） | **可能**（EXPLORATION_NEEDED と同型の既存機構） |
| M4 cap 配線 | `epic-planner.md`（サブタスク数）＋ epic SKILL.md Phase 2（再実行1回/ノード・全体 replan 上限） | 継承（pir2 max3 / deepthink hard-cap と同型） | **可能**（値の較正は G2） |
| M5/M11 直列既定＋書込集合 | epic SKILL.md **3-1**（89-91行: 直列既定と opt-in 5条件）＋ `epic-planner.md`（書込集合列） | 新規（fan-out-gate.md 慣習と接続） | **可能** |
| M10 tree 制約 | `epic-planner.md`（fan-in→USER_DECISION_REQUIRED） | 新規（運用回避） | **可能** |
| M12 done 不変条件 | epic SKILL.md **3-2** 検証パイプライン手順5 | 新規 | **可能** |
| Phase3 決定論バックストップ | epic SKILL.md **2.5**（コマンド確認）＋**ステップ4**（113-115行に実行追加） | 新規（exp-03 #7 適応） | **可能**（コマンドはユーザー供給。無ければ劣化モード明記） |
| メトリクス収集 | epic SKILL.md Phase 3 ＋ `references/experimental.md` epic セクション（収集マッピング追記） | 継承（定義済みメトリクスへの実装接続=F12） | **可能** |
| OTel | 環境変数のみ（スキル変更不要）。採用時 tech-validator | 任意・補完 | **条件付き**（beta。台帳 SSOT に非依存） |

### §11. 段階的移行パス（依存順・「まず何を作るか」）

前回の "instrumentation-now"（【今直す必須】）が W0〜W3、今回の end-state が W4〜W5 に接続する1本のロードマップ:

| 順 | 作業 | 内容 | 依存 |
|---|---|---|---|
| **W0** | citation/文書衛生 | C1（A-lite を §5-2d 仕様で実定義）・C2（pir2-explorer-nesting 正名）・C3（executions 0 明記維持）・C4（cut -c1-40 / sanitized_cwd） | なし |
| **W1** | **pir2 6-3（共通層 git 照合）** | §1-4。**最初に作る**——最小・共通層・観測された事象X クラスを全 pir2 実行で直撃する最高レバレッジ。プラットフォームリスクゼロ | なし |
| **W2** | epic 境界契約一式 | 3-0/3-2/3-5 置換・l1-contract.md・planner 追加要件・2.5 拡張・直列既定・cap 配線・HANDOFF 上書き・最小 resume 読み戻し | W1（同一検証パターン） |
| **W3** | hook Stage A（log-only） | subagent-verify-hook.sh＋settings.json＋**transcript JSONL 実構造の1サンプル確認** | なし（W1/W2 と並行可） |
| **G1** | **1-unit epic dry-run**（executions 0→1） | 観測対象: ①L1 の契約遵守（対立#1トリガ評価）②Agent 同期/非同期の実挙動 ③hook データ妥当性 ④HANDOFF 上書き遵守 | W2（W3 望ましい） |
| **W4** | hook Stage B（block＋floor） | G1 データと JSONL 検証を経て昇格。floor 初期値設定 | G1 |
| **G2** | 実タスク線形 epic（2-3ノード・additive-only） | cap/floor 較正・experimental.md メトリクス収集・完走確率とゲート発火率の実測 | G1 PASS |
| **W5** | end-state 解禁群 | fan-out ≤2 opt-in（5条件 AND）・fan-in merge（実需要が出たら設計=YAGNI）・resume 強化・OTel（tech-validator 経由）・PostToolUse 補完 | G2 ×2 クリーン |

### §12. 「完璧」の正直な境界づけ

**最強の YAGNI 反論（steelman）**: 「executions 0 の機構に完成形設計を書くのは、まさに前回自分が退けた『机上の失敗モード列挙』の再演だ。設計が厚いほど実験は遅れ、ゲートを足すほど完走確率 (1-p)^N は落ちる。正直な手は bare で1回回すことであり、この文書自体が過剰設計の症状ではないか。」

**応答**: (1) 本設計の end-state は大半が**構築物でなく決定トリガの宣言**——今すぐ作るのは W0〜W3（ファイル編集4系統＋log-only hook 1本）だけで、重い物（fan-out・merge・floor 値・OTel）は全て観測ゲート（G1/G2）の背後にある。設計の厚さと構築の厚さを分離した。(2) 完走確率の懸念に対して: W0〜W3 は**ハッピーパスにブロッキングゲートを1つも足さない**（検証は不一致時のみ作用・台帳は非ブロック・直列既定はゲート数を減らす向き。M7 の早期 return だけが新しい中断点だが、Phase 1.5 事前承認で「予見できなかった不可逆操作」だけに絞ってある）。検証ゲートは完走確率を下げるのではなく、**沈黙の破損を可視の失敗に変換する**——実験の目的が観測である以上、これは失敗率の増加ではなく検出率の増加。(3) bare で回して事象X型が再演した場合、前回実証済みのとおり診断不能で学びゼロ（19分迷走）——計器なしの1回は「1回」に数えられない。

**除去できない残存限界（設計はここで止まる、と明示する）**:

1. **#44783 級のハングは親の内側から検知不能**。フォアグラウンドなら L0 ごとブロック。バックグラウンド既定（2.1.199）はL0 の応答性を保つが、検知はハートビート mtime の**手動**確認まで。自動 kill・自動 timeout は本環境に決定論的時計が無く不可。
2. **durable resume（決定論リプレイ）・Saga 自動補償・ブロッキング HITL は構造的に不可**（F11）。resume は台帳ベース部分復元＋人間ゲート、補償は diff 全 hunk 提示＋ユーザー判断まで。
3. **決定論検証が縛れるのは「行為の捏造」まで**。ファイル副作用ゼロの分析タスクで「3ファイル読んで結論を捏造」は floor も git も通過する。結論の質は LLM 判定層（reviewer）と人間層の責務であり、そこに決定論の保証はない。
4. **集合算術の盲点**: 先行ノードで既に dirty のファイルを後続が「触った」と虚偽申告するケースは name-only では検出不能（内容ハッシュ突合は較正フェーズの拡張候補、今は入れない）。
5. **契約はプロンプト強制**であり文法保証（strict schema）は Agent return に存在しない（exp-03 #4 不可）。欠落時の artifact 再構成が保険だが、それも L1 が書いたファイルに依存する。
6. hook は fail-open 設計（誤ブロックでワークフロー全体を殺さないため）。よってこれは**事故に対する計器であり、攻撃に対する防御ではない**。

### §13. トレードオフ台帳（採った側＋理由）

| # | トレードオフ | 採った側 | 理由 |
|---|---|---|---|
| 1 | context 隔離（B）vs 制御純度（A） | **B** | A は捏造の発生機序（context 圧）を悪化させる向き。制御純度の懸念は「L1 を信頼しない境界検証」で外側から充足（§段2） |
| 2 | フォアグラウンド決定論（PostToolUse メトリクス）vs バックグラウンド耐性 | **B経路（SubagentStop）主経路・全域同期化 env 不採用** | env はセッション全体に効き、CLAUDE.md の「codex は background Agent 経由必須」を破壊するクロス SSOT 違反。B経路は実行モード非依存で同等情報を得られる（実装1段追加のコストを受容） |
| 3 | 直列の診断明瞭性 vs 並列の wall-clock | **直列既定（実験段階）** | 実験の生産物は速度でなく解釈可能な観測。並列は5条件 AND の opt-in として温存（看板機能を殺さない） |
| 4 | ゲート忠実度（5.7 のブロッキング維持）vs 自律性 | **可逆性で二分**（可逆=deferred 継続・不可逆=早期 return） | 全ゲートをブロッキング化すると N×5 のゲート地獄、全 deferred 化すると不可逆操作の事後承認（M7 の欠陥）。可逆性は恣意性のない客観境界 |
| 5 | 検証の二重化（L1 と L0 が各々 git 照合）vs 単一点検証 | **二重化** | 各境界に独立の「信頼できない語り手」がいる（L0 境界の語り手は L1 自身）。コストは境界あたり bash 数行・O(1) |
| 6 | ファイル台帳 vs OTel トレース | **台帳が SSOT・OTel は任意補完** | 外部インフラ・beta 機能にコア機構を依存させない。二重管理は台帳→OTel の一方向補完に限定 |

### §14. CLAUDE.md 整合表

| 規定 | 本設計の扱い |
|---|---|
| 制御責務の所在（loop counter SSOT・観測可能性） | **意図的 carve-out として明示**: L1 の制御責務は「再帰オーケストレーション」であり、成立条件＝境界計器（M1 契約＋M2 検証＋M3 台帳）の稼働。この条件文を CLAUDE.md epic 節と experimental.md に明記（M6）。ループカウンタはスコープ単位 SSOT（L1 内カウンタは L1 の fresh context に閉じ、L0 はノードレベルのカウンタのみ保持）——cross-subtask 汚染が構造的に不可能な形 |
| ツール結果捏造の絶対禁止 | 本設計はこの規定の**機構化そのもの**（claim vs ground truth の決定論照合）。設計自体も「M1 は freeze に効かない」等の限界を捏造せず明示 |
| ブラインドリトライ禁止（2回で止める） | 検証 FAIL 再実行は**1回まで＋原因（不一致内容）を逐語注入**。hook block は stop_hook_active guard で1詰まり1回。2回目失敗は必ずユーザーへ |
| 探索委譲（広域探索は explorer へ） | L0 の検証は既知パスへの `git diff --name-only`/`test -f` のみ＝広域探索でなく決定論チェック（ピンポイント例外の範疇）。設計実装時のコードベース調査は従来どおり explorer 委譲 |
| dead code / 後方互換温存禁止 | 3-5 の旧記述は**置換**（併記温存しない）。A-lite は「深さ超過時 inline フォールバック」として CLAUDE.md epic 節が既に要求する機構の実定義であり dead code ではない。fan-in merge は需要が出るまで**作らない**（予約実装をしない） |
| git restore のユーザー明示指示なし実行禁止 | 補償は diff 全 hunk 提示＋ユーザー判断のみ（自動 restore なし） |

### §15. M1–M12 トレーサビリティ＋C1–C4 非再導入

| M | 本設計での着地（silently drop なし） |
|---|---|
| M1 | §1-2 return 契約（3-0 置換・l1-contract.md）。freeze 非対応の正直なスコープ明示つき |
| M2 | §1-3 L0 検証パイプライン＋§1-4 pir2 6-3＋§7 hook（C経路必須・B経路条件付き・A経路補完） |
| M3 | §8 イベント台帳（3-5 置換）。粒度の限界（L0 が書けるのは境界2点、内部 phase は M1 の事後報告）を明示 |
| M4 | §3-1（サブタスク cap）＋§5（ノード再実行1回・全体 replan 上限）。値は G2 較正 |
| M5 | §段3 対立#2 決着（直列既定・5条件 opt-in・Bash 制約は幅≤2＋書込非交差＋ハートビートで代替） |
| M6 | §14 carve-out（条件文つき正当化を CLAUDE.md epic 節＋experimental.md に明記） |
| M7 | §段4 選択的早期 return＋§3-4/§4-1 事前分類・事前承認（5.7 格下げ=F9 の解消） |
| M8 | W0（C1=A-lite 実定義・C2・C3・C4）。本文書自体が C1–C4 を非再導入（下記） |
| M9 | §2-2 resume 再構成（台帳＋git・人間ゲート）＋§1-1-3 HANDOFF 隔離＋§8 台帳 |
| M10 | §3-2 tree/線形制約＋fan-in は USER_DECISION_REQUIRED（merge は W5 で需要駆動） |
| M11 | §3-3 書込集合宣言＋直列化。fan-out 解禁後は §5-2f の帰属規則がランタイム検知を兼ねる |
| M12 | §1-3 手順5 STATUS 不変条件＋§5 失敗パス（半完成ノードの明示状態・下流ブロック） |

**C1–C4 非再導入の自己点検**: C1=「inline フォールバック」を未定義語のまま使わず A-lite として実仕様化（§5-2d）。C2=実験名は pir2-explorer-nesting 表記のみ使用。C3=本文書は epic の運用実績を一切主張しない（executions 0 を明記）。C4=run-dir 命名は `run-dir-base.md` SSOT・`cut -c1-40` を明記。

---

### 反証・対立仮説の検討

- **反論1（最強・YAGNI）**: §12 で steelman 済み。要旨: 設計の厚さ≠構築の厚さ、ハッピーパスに新ブロッキングゲートなし、計器なしの1回は観測として無価値（19分迷走の実証）。**結論は耐える**。ただし譲歩を1つ明示: W2 の epic 編集量は小さくないため、「W1（pir2 6-3）だけ先に入れて素の pir2 で数日運用し、epic 編集前に 6-3 の偽陽性率を見る」順序も許容範囲（W1→W2 の依存はその余地を残して切ってある）。
- **反論2（A 先行論の再来）**: 「L1 の契約遵守自体が未実証なのに B を恒久と呼ぶのは早い」——正当。だから対立#1 の決着には**反証条件つきトリガ**（G1 連続2回契約不履行→ユーザー上程）を内蔵し、「恒久」は「トリガが発火しない限り」の条件付き恒久である。無条件断定はしていない。
- **反論3（検証の偽陽性が実験を殺す）**: UNDECLARED_CHANGE を hard fail にすると formatter/lockfile 副作用で頻発し完走不能になりうる——採用済みの応答: PHANTOM_CLAIM（捏造シグネチャ）だけを hard fail とし、UNDECLARED は warn＋他ノード宣言集合との交差時のみブロック、という**非対称設計**にした（前回「行数照合を退け集合照合に転化」した偽陽性排除方針の継承・強化）。
- **反論4（hook はどうせ fail-open で骨抜き）**: fail-open は意図的（誤ブロックで全ワークフロー停止の方が高くつく）。hook が死んでも C経路（git 照合）は L0/L1 のスキル手順として独立に走る——多層のうち1層の失陥で全体が落ちない構成にしてある。ただし「スキル手順としての検証」は LLM が手順を飛ばすリスクを残す（next-steps-queue の checkbox に検証ステップを含めることで手順飛ばしを観測可能にする、が現状の上限）。**この層の残余リスクは除去できない**と認める。
- **対立仮説（そもそも epic 不要説）**: 「N 回 /pir2 を手動で回せば epic は要らない」——それが正しいとしたら本設計は無価値。応答: 手動 N 回は依存注入（先行成果の後続への手渡し）・deferred 集約・統合検証を全て人間が担うことを意味し、epic の価値仮説はまさにそこの自動化。executions 0 の現状ではこの仮説を**棄却できない**——だからこそ G1/G2 は「epic が手動 N 回に対して優位か」を測る実験であり、本設計はその実験を診断可能にする計器群。epic 廃止判断が出ても W1（pir2 6-3）と hook は素の pir2 の資産として残る（投資の大半が epic 不採用時にも回収可能な配置にした）。

### 二次・三次の含意と境界条件

**含意（設計が正しいとき派生する帰結）**:
- hook floor は全スキルに効く（epic 限定でない）→ 事象Y 級のゾンビ成功が deepthink/research 含む全サブエージェント運用で検知可能になる（共通層配置の配当）。逆に言えば floor 表の誤設定は全スキルに波及——未登録型 floor なしの既定が安全弁。
- 並列解禁後、§5-2f の帰属規則が M11 ランタイム検知を無償で提供（M2 の拡張として）。
- 台帳＋metrics.jsonl により retrospector/メタ分析が初めて実データを持つ（experimental.md の Adoption/Rejection Criteria が判定可能になる）。
- `.ai-pir-runs/` 配下への jsonl 追記は gitignore 済み領域でコミット汚染なし。ただし無制限成長するため、G2 以降にローテーション規約が要る（軽微）。

**境界（成り立たなくなる条件）**:
- P2（同一 working tree）が崩れる環境——worktree 分離を導入した瞬間、git を共有 ground truth とする M2 の集合算術は再設計になる（worktree 分離を W5 でも既定にしない理由）。
- 非 git プロジェクト／git 外の副作用（DB・外部 API）が主のタスク——C経路は空洞化し、ARTIFACTS 検証と floor だけが残る。epic の題材選定制約として明記すべき。
- 無人運転（P4 崩れ）——全ユーザーゲートが永久ブロック。本設計は対話セッション前提であり、無人化は別設計。
- プラットフォーム側の仕様変更（SubagentStop スキーマ変更・background 既定の再変更）——B経路は SubagentStop のライフサイクル自体に紐づくため比較的頑健だが、hook 依存部は常にプラットフォームリスクを負う（C経路が hook 非依存で残ることが保険）。

### rubric への寄与（現時点）

| rubric 基準 | 寄与/未達 | 根拠 |
|---|---|---|
| 1 フェーズ単位仕様 | 寄与 | §0〜§8: Phase 0/1/1.5/2/3＋境界契約（起動/return/検証パイプライン/6-3）を実行順に記述 |
| 2 4対立の決着 | 寄与 | §9 決着表: #1 B恒久＋反証トリガ / #2 直列既定＋5条件 opt-in / #3 claims-up＋local-pull で解消 / #4 台帳部分 resume 宣言 |
| 3 SSOT アンカー＋実現可能性 | 寄与 | §10: 行番号つき挿入点・新規/継承判定・可能/条件付き/不可 を F1〜F13 に基づき評価 |
| 4 段階的移行パス | 寄与 | §11: W0〜W5/G1〜G2 依存順、「まず W1（pir2 6-3）」明示、前回 instrumentation-now と end-state を1本に接続 |
| 5 「完璧」の境界づけ | 寄与 | §12: YAGNI steelman＋応答、残存限界6件（#44783 検知不能・durable 系不可・結論捏造は決定論外 等） |
| 6 トレードオフ具体 | 寄与 | §13: 6件、各々採った側＋理由 |
| 7 CLAUDE.md 整合 | 寄与 | §14: 6規定を個別照合、carve-out（M6）は条件文つきで明示 |
| 8 トレーサビリティ | 寄与 | §15: M1–M12 全対応表＋C1–C4 非再導入の自己点検 |

### 事実と推測の仕分け

- **事実（context/探索に出典あり）**: F1〜F13 の全項目（各表に出典明記）。挿入点の行番号（exp-01）。hook スキーマ verbatim（exp-02）。参照アーキの可否棚卸し（exp-03）。
- **推論（本 deliberator の解釈）**: 「A は捏造発生条件を悪化させる」という機序論（事象X 機序からの外挿・n=1）。可逆性による deferred/早期 return の二分基準。PHANTOM/UNDECLARED の非対称設計。floor 初期値・cap 初期値（全て仮置き・G2 較正前提）。「W1 が最高レバレッジ」という順序判断。バックグラウンド時代のハートビート観測可能性（**未実証**——G1 の観測対象に含めた）。`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` が codex background Agent 運用を破壊するという干渉推論（env のセッション全域性=事実、codex への波及=強い推論だが実機未確認）。
- **未検証のまま設計が依存している点**: transcript JSONL 実構造（W3 に検証ステップとして内蔵）。L1 の契約遵守能力＝P5（G1 に反証条件として内蔵）。Agent 呼び出しの同期/非同期実挙動（G1 観測対象）。

### 現時点の確信度と残る不確実性

- **確信度: 中〜高**
  - 高: C経路（git 集合照合）の実現可能性と設計（F3 直結）。挿入点アンカー（exp-01 実ファイル確定）。対立#3 の解消論理（P2 は環境の構造的事実）。residual limits の列挙（F11 直結）。
  - 中: 対立#1 の「B 恒久」判断（P5 未実証——ただし反証トリガ内蔵で判断自体は頑健）。hook B経路（JSONL 構造未検証）。対立#2 の5条件の妥当性（ハートビート観測は未実証）。floor/cap の初期値（全て仮置き）。
  - 低: バックグラウンド起動時代の並列 fan-out 実挙動（G1/W5 でしか埋まらない）。
- **残る不確実性**: 事象X が epic の L1 ネスト内でも再発するか（前回から持ち越し・G1/G2 でのみ観測可能）。L1 が HANDOFF_PATH 上書き等のプロンプト指示をどこまで忠実に守るか（契約全般のプロンプト強制の限界）。

### 追加探索が必要な論点（該当分のみ・いずれも移行パスに内蔵済み）

1. **transcript JSONL の実構造**（`~/.claude/projects/<sanitized>/*/subagents/*.jsonl` を1件 jq で確認）——W3 の前提。確認できれば hook Stage B の jq 式が書ける。
2. **Agent ネスト起動の同期/非同期実挙動とハートビート観測可能性**——G1 dry-run で観測（机上では埋まらない）。
3. **`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` の作用範囲**（サブエージェント種別ごとか全域か）——不採用判断の根拠を確定させたい場合のみ（現設計は不採用のため優先度低）。
4. **epic SKILL.md の Phase 0 相当（初期化ステップ）の実記述**——exp-01 は 3-0 以降のみ行番号確定。§2 の挿入位置確定は実装時 Read で足りる（explorer 再起動までは不要）。
