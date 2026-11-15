## 背景ブリーフ（context）: /epic 完成形ワークフロー設計

本 run は前回 deepthink（`20260703-175327-deepthink`）の続き。前回は「executions 0 の実験を回す最小の計器」で止めた。今回は**理想の完成形＋移行パス**を設計する。

### 引き継ぎ土台（前回 deepthink の結論。詳細は `.ai-pir-runs/20260703-175327-deepthink/position-1.md`）

- **中核命題**: 観測された失敗2件（事象X=resume 直後の implementer 完了報告**捏造**→reviewer 全FAIL→19分迷走 / 事象Y=サブエージェントの**ゾンビ成功** tool_uses:0）は epic のネスト機構を通っていない。要るのは「堅牢化」でなく「計器（instrumentation）」。委譲型オーケストレータはサブの完了報告を claim として扱い、**self-report でなく決定論的外形検証**を境界に置く二層機構（テレメトリ return＋独立 git/floor 検証）が最高レバレッジ。
- **改善点 M1–M12（要約）**: M1 L1境界テレメトリ return / M2 L0 決定論的 git 突合＋役割別 tool_use floor / M3 epic-runs.md に Phase+timestamp / M4 ループ・サブタスク数 hard-cap / M5 並列 fan-out の #44783 緩和 / M6 L1 制御責務 vs CLAUDE.md の解消/正当化 / M7 破壊的変更の事前ゲート＋timeout-block / M8 citation是正 C1-C7 / M9 resume 台帳 / M10 DAG fan-in 対応 / M11 共有ステート競合の保守直列化 / M12 サブ失敗回復パス。
- **4件の未解決対立**: #1 L1 制御責務を Option A(L0直接統率=純粋解消) か Option B(L1維持＋テレメトリ正当化) か / #2 fan-out 既定 OFF か ≤2-3 opt-in か / #3 捏造検証を L0 集約すると context 爆発（summary-up vs evidence-up）/ #4 resume/timeout の程度。

### 確定的な事実（今回探索・出典あり）

**実装アンカー（exp-01, ローカル実ファイル）**
- **L1（ネスト pir2 ランナー）は fresh-context の Agent 呼び出し＝「per-subtask コンテキストリセット境界」として機能している**。ファイル経由受け渡し＋要約のみ返す telephone-game 回避が pir2/epic 共通。→ これは Option B の核心価値（捨てると context 隔離を失う）。
- **挿入点確定**: M1/M3 → epic SKILL.md ステップ **3-0**（L1 起動プロンプトに return 契約）/ **3-5**（epic-runs.md 記録）。M2 → epic **3-2**（L1 返り値受領直後に L0 検証）＋ pir2 SKILL.md の **ステップ6→7 境界**（implementer→reviewer 間に決定論ゲート新設）。M9 → pir2 の continuation-gate / next-steps-queue / handoff を run-dir スコープで継承。
- **Option A の実コスト**: L0 が pir2 を直接駆動するなら **約23ステップ＋最大5種のユーザーブロッキングゲート＋6種のループカウンタ**をサブタスク数ぶん単一 context で並行管理。L1 の「コンテキストリセット境界」喪失が核心コスト。出典: 実ファイル。

**プラットフォーム実現可能性（exp-02, 一次ソース・claude 2.1.199 実機）**
- **M2 の hook 依存部分＝条件付き可能**: `SubagentStop` は `agent_transcript_path`（サブ transcript 絶対パス）を返し、hook が `jq` で tool_uses/duration/status を決定論算出できる。加えて `PostToolUse`（matcher=Agent）の `tool_response` に **`totalToolUseCount`/`totalDurationMs`/`totalTokens`/`status` が構造化データで乗る**（**フォアグラウンド実行時のみ**。v2.1.198+ は既定バックグラウンド化するため `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` 等が前提）。出典: `code.claude.com/docs/en/hooks`。
- **M2 の git-diff 部分＝完全に可能**（hook も LLM 判断も不要、純 bash の集合比較）。
- **#44783（並列 fan-out ハング）は公式 CLOSED/NOT_PLANNED**（stale bot 自動クローズ、Anthropic 修正なし）。ただし**本リポの PIR² は既に並列 fan-out（reviewer 5観点・ui-ux・epic 独立サブタスク）を採用済み＝このリスクは既に負っている**。M2 固有ではない。
- 注意: `totalToolUseCount` 系の feature request issue は NOT_PLANNED だが**実体は docs に実装済みとして記載**。issue ステータスで「機能なし」と早合点しない。

**参照アーキテクチャ（exp-03, 外部一次16ソース）**
- **Claude Code はネイティブ OpenTelemetry（beta）を持ち、`agent_id`/`parent_agent_id` 属性で L0→L1→L2 の親子関係をそのままトレース計装できる**（当初「計装手段なし」の仮定は誤りと判明）。→ M3 観測性がトレース基盤に乗る。
- **durable resume（決定論リプレイ）/ Saga 補償 / 真のブロッキング HITL 一時停止は Agent ツールの構造的制約で本環境では不可**。→「完璧」の外枠（残存限界）。
- 設計語彙: typed contract（構造化 return）/ deterministic verification gate（trust-but-verify）/ resume protocol（台帳ベース復元）/ compensation。適用可否は「そのまま/要適応/本環境不可」で棚卸し済み。

### 不確実・出典が弱い情報
- **Agent ネスト起動が同期ブロッキングか非同期か**は exp-01 でコード上確定できず（推測・要 dry-run）。M1/M3 の「フリーズ検知への寄与可否」判断に直結。
- `agent_transcript_path` の JSONL 実構造は未確認（M2 の jq 解析設計時に要確認）。
- OTel beta の実運用化は tech-validator 委譲推奨（exp-03）。

### 探索で見えた対立・論点（設計判断に効く）
- **対立#1（Option A/B）**: exp-01 が A の実コスト（context-reset 境界喪失＝23ステップ×N の単一 context 管理）を定量化、exp-02 が B のテレメトリ実現可能性を確認 → **B 有利に傾く**。ただし L1 の自律オーケストレーション実証（dry-run）は未達で完全決着は保留。
- **対立#2（fan-out）**: #44783 は closed/not-planned かつ既にリポが並列を採用済み → 「並列そのものを禁止」は過剰かもしれない。一方で M2 のフォアグラウンド要件（`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS`）は並列運用と干渉しうる → **「並列 fan-out」と「決定論検証のフォアグラウンド要件」のトレードオフ**が新たに浮上。
- **"完璧" の境界**: durable resume/Saga/blocking HITL が本環境不可 → 完成形設計は「決定論リプレイ級の resume」を諦め「台帳ベースの部分復元」に留める必要（honest な残存限界）。

### まだ埋まっていない空白
- L1 が SKILL.md 全文を自律オーケストレーションできるかの実証（1-unit epic dry-run、executions 0）。
- Agent 呼び出しの blocking 特性・`agent_transcript_path` 実構造・OTel beta の実効性。
