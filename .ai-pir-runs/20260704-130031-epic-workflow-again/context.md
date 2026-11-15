## 背景ブリーフ（context）: epic ワークフローの実行 readiness と次の一手

探索3系統: 01（epic 逐語＋実行可能性ギャップ・全文は `exploration-01.md`）/ 02（移行パス現在位置・dry-run 可否）/ 03（初回 run 安全性・L1 自律性）。

### 確定的な事実（出典あり）

**移行パス上の現在位置（exp-02）**
- W0（citation 衛生）・W1（pir2 6-3）は commit `a10aa8e` 済み・レビュー PASS。**同一コミットで「素の」epic 基盤（`epic/SKILL.md`＋`epic-planner.md`、Fable5 設計より前の版）も追加**されている。**W2（epic 境界契約：L1 テレメトリ return・L0 検証パイプライン・台帳）・W3（hook Stage A）は未着手**（`SubagentStop` hook・関連スクリプトの不在を実ファイルで確認）。
- 設計上 W1 の次は W3→G1 dry-run だが、**G1 の観測4項目の仕分け**: ②Agent 同期/非同期＝W2 非依存で完全観測可 / ①L1 契約遵守＝契約不在で「素の P5 挙動」の劣化版のみ / ③hook データ・④HANDOFF 上書き遵守＝契約/hook 不在で**原理的に観測不可**。
- **中心結論（exp-02）**: 技術的には現行 epic をそのまま dry-run 可能。だが Fable5 設計の「G1」（特に対立#1 の U1 判定トリガ評価）は「契約」という観測対象が無いと成立しない。**W2 なし dry-run は設計 G1 の代替でなく「P5＋②のみ見る予備観測」**。

**L1 自律性＝未実証（確定事実・exp-03）**
- epic は general-purpose サブに pir2 SKILL.md（約560〜579行）を Read させ、その中の explorer/planner/implementer/reviewer/tester の起動・ループ管理・VERDICT 集約・ユーザーゲート委譲まで自律実行させる設計。この「サブが長い SKILL.md を解釈して多段オーケストレーションを完遂する」実証は**リポ内に無い**（`pir2-explorer-nesting`・`epic-orchestrator-nested-pir2` の Evidence Summary は全項目 0）。過去2本の deepthink も「P5 未実証」と明言。**未実証は確定**。
- 外部: 「**LLMs Get Lost in Multi-Turn Conversation**」論文＝長い手順書を多ターンで解釈する L1 の instruction-following 劣化に直結。MAST（マルチエージェント失敗の多くはシステム設計）＝ただし「41.8%」数値は独立確認できず要再確認。rollout 定石＝段階的・観測付き・小さく始める。

**初回 run の安全性（exp-03）**
- 本セッションの実失敗3件（(a) 捏造フリーズ (b) explorer ゾンビ成功 tool_uses:0/4.8秒 (c) implementer 05 の parse エラー早期終了）は transcript で一次確認。**いずれも epic のネスト機構を通らず発生**＝epic 固有の確率悪化ではない。ただし epic は L0 から検知が1層遠い（L1 境界テレメトリ未実装）固有の追加リスク。
- 深さ: L0(0)→L1(1)→L2(2)→L3(3) で上限 5 に**余裕2階層**（L2 打ち止め設計はやや過剰保守）。並列 fan-out の組合せ挙動・hook のネスト階層発火は未検証。

**現行 epic の実行可能性ギャップ（exp-01・新規発見含む）**
- **HANDOFF_PATH が単一固定パス** `${PROJECT_ROOT}/.ai-pir-runs/handoff.md` → **並列 fan-out で複数ネスト pir2 が同一 handoff.md を競合 Write/削除**（Fable5 §1-1-③ は L1 起動時に `{サブRUN_DIR}/handoff.md` へ上書きせよと設計したが W2 で未実装）。
- **並列サブタスクは同一 git 作業ツリーを共有** → 6-3/reviewer/tester の git diff 判定が**相互汚染**（どのサブの変更か区別不能）。
- `general-purpose` サブが CLAUDE.md を継承するかは**未検証**（継承しないと L1 がプロジェクト規約なしで pir2 を回す）。
- 6-3（W1・コミット済み）は epic 経由のネスト pir2 内で発火するか: epic の L1 が pir2 SKILL.md を Read → その pir2 の 6-1/6-3 は**手順としては含まれる**が、L1 が実際に実行するかは P5（L1 自律性）に依存。

### 探索で見えた対立・論点（deliberation の焦点）
- **論点A（次の一手）**: (i) 素の dry-run を今やる（P5＝L1 自律性を最小コストで直接検証・W2 の投資判断を gate する）か、(ii) W2 を先に作る（設計 G1 を成立させてから回す）か、(iii) 保留。P5 が未実証な以上、W2（L1 が動く前提の契約 plumbing）を先に作るのは「動くか不明なランナー用の配管」の先行投資では。
- **論点B（並列を初回に出すか）**: HANDOFF 競合・共有ツリー汚染・#44783 は**すべて並列 fan-out 時のみ発現**。初回を**完全直列**にすればこれらは発現しない → 初回安全構成の分水嶺。
- **論点C（素の dry-run の観測価値）**: exp-02 は「設計 G1 の代替にならない予備観測」と評価。だが P5（L1 が pir2 を回せるか）は epic 全体の load-bearing 仮定で、これを潰さない限り W2 も無意味 → 素の dry-run の情報価値は「予備」でなく「gate」では、という対立。

### まだ埋まっていない空白
- general-purpose の CLAUDE.md 継承有無（Claude Code 公式仕様の裏取り未）。
- 素の epic を1回回したときの L1 の実挙動（executions 0）。

### 詳細資料（epic SKILL.md 核心の逐語抜粋。全文は exploration-01.md）

L1 起動方式（epic SKILL.md ステップ 3-0）:
> 各サブタスクを `Agent` ツールで `subagent_type=general-purpose` として **`model=opus`** で起動し、プロンプトで「あなたはこのサブタスクの PIR² オーケストレーターです。`~/.claude/skills/${SUBTASK_SKILL}/SKILL.md` を Read し、その手順に従ってサブタスク `<Ti タスク記述>` を最後まで実行してください」と指示。**model=opus は必須**（弱いモデルでは SKILL.md の複雑な条件分岐・ループ制御が破綻）。

Phase 1.5（分割確認ゲート・L0 専任・Auto mode でも必須）/ Phase 2（3-1 独立集合は並列 fan-out、3-2 依存は直列、3-3 深さ L2 頭打ち・超過時は L1 直接探索へ縮退、3-4 ユーザーゲート bubble-up、3-5 epic-runs.md 追記）/ Phase 3（統合確認＋メタ retro）。共有ステート競合は epic-planner が「暗黙依存」で直列化。
