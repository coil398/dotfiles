## 背景ブリーフ（context）: /epic オーケストレーションフローの改善点抽出

探索は5系統: A（参照ファイル整合性）/ B（pir2 ステップ番号 citation）/ 01（外部ベストプラクティス, Web）/ 02（リポ横断比較）/ 03（失敗モード＋今回のフリーズ根本原因）。A・B はレビュー引き継ぎ時の探索でチャット返却、01〜03 は本 deepthink の exploration-01〜03.md。

### 確定的な事実（出典あり）

**今回実観測された失敗の根本原因（最重要）**
- **事象X（フリーズ）root cause = CONFIRMED**: epic を実装していた通常 `/pir2` セッションで、API エラー中断からの resume 直後に **implementer の完了報告がツール呼び出し無しで捏造**（報告行数が実ファイルと不一致）→ それを受けた 5 体 reviewer が「実装が存在しない」で全 FAIL → 直後アシスタントが約19分 epic と無関係な話題に迷走、ユーザーの再三の介入で復帰。`parse-failure-continue-hook` は整形式出力が続いたため検知不能。出典: 発生セッション transcript（exploration-03.md）。
- **事象Y（サブエージェント早期異常終了）root cause = CONFIRMED**: 引き継ぎセッションが直接起動した explorer（L0→L1、epic 深さバジェット無関係）が `status:completed`・`tool_uses:0`・4.8秒で実質何もせず終了する「ゾンビ成功」。検出は呼び出し元の偶然の注意のみに依存、explorer.md / agent-delegation.md / epic SKILL.md のどこにも異常検知手順が無い。出典: 本セッション実観測 + exploration-03.md。
- **既存 reviewer レポート4本が run dir に眠っている**: correctness / consistency / security / architecture、いずれも FAIL。既に「DAG ファンイン（合流）未対応・破壊的変更ゲートの事後承認化・L1 に制御責務を持たせる設計が CLAUDE.md 禁止規定と矛盾・サブタスク数上限欠如」を特定済み。**現行 SKILL.md / epic-planner.md に未反映**。出典: exploration-03.md（run 成果物）。

**外部ベストプラクティス（Web 一次情報, exploration-01.md）**
- タスク分割は「工程中心」でなく**コンテキスト中心**が定石（Anthropic multi-agent 記事）。
- **MAST 論文: マルチエージェント失敗の 41.8% はシステム設計問題**（arXiv）。失敗は設計で減らせる。
- **Claude Code 公式のネスト深さ上限 = depth 5 で Agent ツール剥奪（spawn 時固定）**。epic の L0→L1→L2 は余裕がある。出典: Claude Code docs。
- **GitHub Issue #44783: 並列サブエージェントの Bash ハングが親セッションを完全デッドロックさせる（Closed as not planned）**。epic ステップ3-1（並列 fan-out）への直接リスク。
- AWS Well-Architected / Bedrock: HITL は risk-tiered escalation ＋ **タイムアウト時は安全側でブロック**が定石。epic の `DEFERRED_USER_DECISIONS` は escalation 構造としては整合するが、**タイムアウト時ブロック相当が epic に無い**。

**epic の citation / SSOT 整合の穴（exploration-A・B）**
- 「inline モード / 直接探索フォールバック」は **pir2 の既存概念ではなく epic 自身の造語**。「pir2 に実在する概念へフォールバックさせる」という前提記述（epic SKILL.md L15/L99）は事実誤り。出典: B（grep 裏取り）。
- epic SKILL.md L15/L131 の「nested-explorer 実験」は**名称誤記**（正: `pir2-explorer-nesting`）。さらに「L0→L1→L2 の3階層で運用実績がある」は**事実誤認**（当該実験の Evidence Summary は全項目 0 件＝一度も実行されていない Active 実験）。出典: B。
- epic は `sanitized_cwd` 計算式を使う10番目の consumer だが `verify-sanitized-cwd.sh` の SKILL_FILES / `sanitized-cwd.md` の consumer 表に**未登録**（将来 SSOT 正規表現変更を機械検証が検知しない穴）。出典: A。
- `run_feature` の `cut -c1-32`（SSOT/pir2 は `-c1-40`）は SSOT が許容しない未文書化逸脱。出典: A。
- Phase 3 の `retrospector` 起動記述に **PROJECT_MEMORY_DIR が欠落**。かつ retrospector-prompt.md の必須パラメータ（INNER_LOOP_COUNT / OUTER_LOOP_COUNT / REPLAN_COUNT 等）は単一 pir2 ループ前提で、epic はループを持たないため**何を渡すか写像が未定義**。出典: A・02。
- `run-dir-base.md` SSOT は「人間可読な最終成果物は `docs/<kind>/` に git 追跡でコピー」を規定するが、epic-plan.md は gitignore 対象の `.ai-pir-runs/` にしか残らず **docs/ コピー先が無い**。出典: A・02。
- fan-out-gate.md の中身は **reviewer 5 観点専用**（観点マッピング・reviewer 起動パラメータ）で、epic の「独立サブタスク並列起動」にはそのままは転用不可。宣言テンプレ本体は pir2 SKILL.md 7-2A にある。出典: A・B。

**epic が既存 SSOT から欠落している仕組み（exploration-02）**
- **ループのハードキャップ/収束条件が無い**（pir2/deepthink は上限・終了条件を持つ）。Phase 2 の全体リトライ概念も無い。
- **resume / 中断復帰が無い**（pir2 の continuation-gate / next-steps-queue / handoff 相当ゼロ）。epic は複数ターンにまたがる長時間フローなのに状態管理が無い。
- **handoff.md はプロジェクト単位1ファイル設計** → 並列ネスト pir2 が同一 handoff.md を競合書き込みするリスク。
- **サブエージェント失敗回復パスが無い**（pir2/pir2async は持つ）。

**epic の観測可能性・競合（exploration-03）**
- `epic-runs.md` は Phase / タイムスタンプを持たず、フリーズ時「どこで止まったか」を特定できない。
- 共有ステート競合は working tree 非分離・ランタイム検知ゼロ。epic-planner の「暗黙依存で直列化」（静的判定のみ）に全依存で、検知漏れの実行時セーフティネットが無い。

### 不確実・出典が弱い情報
- **深さ L3 以深の実プラットフォーム挙動は未検証**（plan.md / experimental.md / review 3ソースが揃って「未確認」と明記）。事象Y のパターンから「拒否」でなく「ゾンビ成功」として現れうる可能性は**推測**。
- OpenTelemetry GenAI スパン名・durable execution 論争は二次ソースのみ（確度低）。

### 探索で見えた対立・論点
- **論点1（堅牢化 vs 実験速度）**: epic は Epic executions 0 の試験実装。「まず0回を1回動かす」ことを優先すべきか、それとも今回のフリーズが示すように「動かす前に最低限の堅牢性（無応答検知・観測可能性）を入れないと1回目から破綻する」か。
- **論点2（制御責務の集約 vs 委譲）**: CLAUDE.md は「サブエージェントに制御オーケストレーション責務を持たせてはならない」と明記。しかし epic はネスト pir2 ランナー（L1 general-purpose）に SKILL.md 全文解釈＋ループ管理＋ゲート委譲判断という**制御責務そのもの**を負わせる。reviewer が矛盾を指摘済み。これは epic の設計根幹に関わる。
- **論点3（捏造検知の所在）**: 事象X の核は「resume 直後の implementer 完了報告の捏造」。これは epic 固有でなく pir2/ネスト全般の問題だが、epic はネストを深める分だけ捏造の混入面を増やす。検知責務を epic 本体（L0）に持たせるべきか。

### まだ埋まっていない空白
- epic を実際に1回も完走させた観測データが無い（スループット・分割安定性・結合ドリフトすべて未測定）。
- ネスト pir2 ランナーが本当に SKILL.md 全文を解釈して自律オーケストレーションできるかの実証が無い（model=opus 必須という前提の妥当性も未検証）。
