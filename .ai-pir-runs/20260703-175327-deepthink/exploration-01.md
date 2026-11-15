## 探索レポート: LLMエージェントの多階層/ネスト・オーケストレーションフロー — 設計ベストプラクティスと既知の失敗モード（外部一次情報調査）

### 調査の性質

本探索は codebase 探索ではなく **外部一次情報調査** である。ただし対象読者（`/epic` のような大規模タスク分割オーケストレーターを設計している人）の実際の設計と照合するため、参考として `.claude/agents/epic-planner.md` と `.claude/skills/epic/SKILL.md` を Read した。以下ではまず外部知見を 6 観点で整理し、各項目末尾に「`/epic` への当たり（推測含む）」を明示する。

---

### 関連ファイル一覧（ローカル・文脈把握用）

| ファイルパス | 役割・内容 | 変更の必要性 |
|------------|-----------|------------|
| `/Users/kawasetakumi/dotfiles/.claude/agents/epic-planner.md` | エピック分割専任エージェント定義。DAG 生成・暗黙依存（共有リソース競合）の直列化ルールを持つ | 参照のみ |
| `/Users/kawasetakumi/dotfiles/.claude/skills/epic/SKILL.md` | `/epic` 本体。L0→L1→L2 の3階層ネスト、深さバジェット運用（L2頭打ち＋inline fallback）、ユーザーゲートの bubble-up（`DEFERRED_USER_DECISIONS`）、`epic-runs.md` によるトレーサビリティが既に設計済み | 参照のみ |

---

## 1. DAG / サブタスク分割オーケストレーション

### 確定的な事実（出典あり）

- **Anthropic のマルチエージェント研究システム（orchestrator-worker パターン）**: lead agent がクエリを分析・戦略策定し、3〜5体のサブエージェントを**並列**生成する。各サブエージェントには "an objective, an output format, guidance on the tools and sources to use, and clear task boundaries" が必須。指示が簡潔すぎると（例:「半導体不足を調査」）複数サブエージェントが重複調査するか領域に穴が空く。タスク複雑度に応じた努力配分の目安をプロンプトに明記: 単純な事実確認=1エージェント×3〜10ツール呼び出し、直接比較=2〜4サブエージェント×10〜15呼び出し、複雑な調査=10体超。並列化（サブエージェント並列生成＋各サブエージェント内でのツール3並列）で複雑クエリのリサーチ時間を最大90%短縮。
  出典: [How we built our multi-agent research system \| Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)

- **タスク分割の粒度は「コンテキスト中心」であって「問題（工程）中心」ではない**: 「計画→実装→テスト→レビュー」のような工程別分割は最大の失敗パターンとされる。原文引用: "Dividing by type of work (one agent writes features, another writes tests, a third reviews code) creates constant coordination overhead." / "Each handoff loses context. The test-writing agent lacks knowledge of why certain implementation decisions were made." / "The subagents spent more tokens on coordination than on actual work." 逆に推奨されるのは「コンテキスト境界での分割」("Dividing by context boundaries means an agent handling a feature should also handle its tests, because it already possesses the necessary context.")。核心原則: **"Work should only be split when context can be truly isolated."** 唯一例外的にうまくいくのが**検証専任サブエージェント**（Verification subagent）パターンで、"Verification requires minimal context transfer by nature, so a verifier can blackbox-test a system without needing the full history." ただし「早期勝利問題」（テスト不十分でも合格判定してしまう）を避けるため、"You MUST run the complete test suite before marking as passed" のような明示指示が必須。
  出典: [When to use multi-agent systems (and when not to) \| Claude by Anthropic](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them)

- **5つの調整パターンとその選択指針**（Anthropic）: Generator-Verifier（反復ループ、収束しないリスクあり）／Orchestrator-Subagent（階層構造、"The orchestrator becomes an information bottleneck" という既知の弱点）／Agent Teams（ワーカーが自律的に複数サイクル生存、ただし "If one teammate's work affects another's, neither is aware" ＝共有リソース競合に弱い）／Message Bus（イベント駆動、"understanding what happened requires careful logging" でデバッグが困難）／Shared State（共有DB読み書き、"Without explicit coordination, agents may duplicate work" と収束しない reactive loop のリスク）。**推奨**: "we recommend starting with orchestrator-subagent. It handles the widest range of problems with the least coordination overhead"。限界が見えたら段階的により複雑なパターンへ移行する。
  出典: [Multi-agent coordination patterns: Five approaches and when to use them \| Claude by Anthropic](https://claude.com/blog/multi-agent-coordination-patterns)

- **MAST（Multi-Agent System Failure Taxonomy）論文**: 7つの主要マルチエージェントフレームワーク横断で1,600件超のトレースを収集し、150件のトレースを人手で分析（アノテータ間一致度 κ=0.88）。**失敗の41.8%はシステム設計問題（仕様の誤解・曖昧な役割定義・分割の質の低さ・重複した役割・終了条件の欠如）、36.94%はエージェント間不整合（協調破綻）、21.30%はタスク検証の弱さ**。14個の失敗モードを定義（例: ステップ繰り返し17.14%、推論と行動の不一致13.98%、明確化要求の失敗11.65%、タスク仕様違反10.98%等）。結論として「多くの失敗はモデル性能ではなくシステム設計の質に起因する」。
  出典: [Why Do Multi-Agent LLM Systems Fail? (arXiv:2503.13657)](https://arxiv.org/abs/2503.13657) / [HTML版](https://arxiv.org/html/2503.13657v2)

- **OpenAI Agents SDK の2大パターン**: Manager パターン（中央マネージャーが専門サブエージェントを「ツールとして」呼び出し会話の主導権を保持）と Handoff パターン（ピアエージェント間で会話の主導権自体を委譲する分散型、"the full message history is transferred" し、triage agent が構造化サマリー＝カテゴリ・優先度等をメタデータとして付与できる）。粒度指針: "Have specialized agents that excel in one task, rather than having a general purpose agent that is expected to be good at anything"。オーケストレーション方式の選択: "orchestrating via code makes tasks more deterministic and predictable, in terms of speed, cost and performance" 対 "Allowing the LLM to make decisions" （柔軟だが低予測性）。
  出典: [Agent orchestration - OpenAI Agents SDK](https://openai.github.io/openai-agents-python/multi_agent/) / [Handoffs - OpenAI Agents SDK](https://openai.github.io/openai-agents-python/handoffs/)

- **CrewAI 階層プロセス**: `manager_agent` は `agents` リストに含めてはならず、プールの外側で動作する。マネージャーが目標を読み、サブタスクに分解し、ワーカーへディスパッチし、出力を統合する（"The manager allocates tasks to agents based on their capabilities, reviews outputs, and assesses task completion."）。ハードコードされたフローなしにタスクを動的にエージェントへ再割り当て・差し戻し要求できる。
  出典: [Processes - CrewAI](https://docs.crewai.com/en/concepts/processes)

- **Google ADK の Workflow Agent（決定論的コントローラ）**: `SequentialAgent`（直列・組み立てライン式・デバッグ容易）／`ParallelAgent`（独立サブタスクの同時実行）／`LoopAgent`（`max_iterations` か `exit_loop` ツール呼び出しまで繰り返す）を、自律推論の `LlmAgent` と使い分ける設計。
  出典: [Technical Overview - Agent Development Kit (ADK)](https://google.github.io/adk-docs/get-started/about/) / [Developer's guide to multi-agent patterns in ADK](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)

- **LangGraph の階層スーパーバイザー**: `create_supervisor()` でスーパーバイザーがさらに複数のサブスーパーバイザーを管理する多段階層を構築可能。レイヤーごとに責務を分離することで「新ドメイン追加時に既存レイヤーへ影響を与えない」「各レイヤーを独立にテスト・改善できる」という利点が明記されている。
  出典: [langgraph_supervisor \| LangChain Reference](https://reference.langchain.com/python/langgraph-supervisor) / [Build a personal assistant with subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents-personal-assistant)

### 不確実・出典が弱い情報

- 「共有リソース競合を "暗黙の依存" として DAG の辺に張り直列化する」という具体的な処方は、Anthropic Agent Teams パターンの弱点記述（"If one teammate's work affects another's, neither is aware"）から**演繹的に導かれる対策**であり、外部一次情報がこの解決策自体を明示的に処方している箇所は見つからなかった。

### 論争点

- LLM 駆動オーケストレーション（柔軟・自律） vs コード駆動オーケストレーション（決定論的・予測可能）のどちらを既定にすべきかは OpenAI 自身が「トレードオフ」として両論併記しており、単一の正解として提示されていない。

### `/epic` への当たり

- `epic-planner.md` の「共有リソース競合は暗黙依存として辺を張り直列化する」設計は、Anthropic の Agent Teams パターンの既知の弱点（並行ワーカー間の相互影響が不可視）に対する妥当な先回り対策として整合する。
- `/epic` の分割単位は「1 サブタスク＝1 pir2（1 サブシステム/1 フィーチャー相当）」であり、これは Anthropic の「コンテキスト中心分割」（feature とそのテストは同じ agent が持つべき）と整合的である。ただし epic-planner.md 自体が「実装ステップは書かない、WHAT のみ」と定めているため、各サブ pir2 内部（planner→implementer→reviewer→tester のフェーズ分割）が「工程中心分割」の形を取っている点は、MAST論文・Anthropic記事が名指しした最大の失敗パターン（工程別分割によるハンドオフ毎のコンテキスト損失）と**構造的に似ている**。ただし pir2 は同一セッション内でメイン Claude がオーケストレーターとして explorer→planner→implementer→reviewer→tester の**全フェーズを見渡す**（ファイル経由 handoff だが、統括者は文脈を保持し続ける）設計であり、Anthropic が問題視した「エージェント間で完全に隔離されたコンテキストの工程分割」とは異なる（統括者＝スキル本体がコンテキストのハブとして機能する点で Orchestrator-Subagent パターンに近い）。この差異は推測に基づく評価であり、確定的な当てはめではない。

---

## 2. ネスト深さ・コンテキスト予算・伝言ゲーム問題

### 確定的な事実（出典あり）

- **Claude Code 公式のネスト深さ仕様**: "Depth is counted as the number of subagent levels below the main conversation, regardless of whether each level runs in the foreground or background. A subagent at depth five doesn't receive the Agent tool and can't spawn further. The limit is fixed and not configurable." サブエージェントのネスト起動自体は v2.1.172 以降でサポート。さらに "As of Claude Code v2.1.187, a background subagent's depth is fixed when it is first spawned, and resuming it later doesn't change that depth."（浅い文脈から resume しても、深さ制限で止められていた追加階層のスポーンは解禁されない）。
  出典: [Create custom subagents - Claude Code Docs](https://code.claude.com/docs/en/sub-agents)（"Spawn nested subagents" セクション）

- **各サブエージェントは新規・独立のコンテキストウィンドウで開始**: "Each subagent starts with a fresh, isolated context window. It doesn't see your conversation history, the skills you've already invoked, or the files Claude has already read." 親は委譲メッセージを合成して渡すのみ。並列サブエージェントの警告: "Running many subagents that each return detailed results can consume significant context."
  出典: 同上

- **伝言ゲーム対策としての外部ストレージ経由**: Anthropic のリサーチシステムでは "Subagent output to a filesystem to minimize the 'game of telephone.'" サブエージェント出力を会話履歴でコピーするのではなくファイルシステムに永続化し、情報損失とトークンオーバーヘッドを削減する。また lead agent はコンテキストが200,000トークンを超えるとtruncateされるため、"saving its plan to Memory to persist the context" という設計。
  出典: [How we built our multi-agent research system \| Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)

- **トークンコスト実測値**: "agents typically use about 4× more tokens than chat interactions, and multi-agent systems use about 15× more tokens than chats"。あるBrowseComp評価では "Token usage by itself explains 80% of the variance"（モデルの質向上の効果がトークン予算2倍化の効果を上回った）。
  出典: 同上

- **Lost in the Middle（Liu et al., arXiv:2307.03172）**: 複数文書QA・key-value検索タスクで、関連情報の位置がコンテキストの先頭・末尾にある場合に精度が最も高く、中間に配置されると精度が30%超劣化するU字カーブが確認された。GPT-3.5-Turbo, GPT-4, Claude 1.3, LongChat-13B, MPT-30B, Cohere Command の6モデルファミリーで再現。結論: "current language models do not robustly make use of information in long input contexts."
  出典: [arXiv:2307.03172](https://arxiv.org/abs/2307.03172)

- **Chroma "Context Rot" 研究（2025）**: GPT-4.1/o3/GPT-4o系、Claude Opus 4/Sonnet 4/3.7/3.5/Haiku 3.5、Gemini 2.5 Pro/Flash・2.0 Flash、Qwen3-235B/32B/8B の計18モデルを検証し、**全モデルが入力長増加に伴い性能劣化する**ことを確認。劣化要因: (1) needle-question 類似度が低いほど劣化が加速、(2) distractor（妨害情報）は1個でもベースラインより性能低下、4個追加で複合劣化（Claude系は不確実時の棄却が多く、GPT系は幻覚率が高いというモデル差も観測）、(3) haystack構造は直感に反して「文をランダム配置した方が高性能」な場合がある。Repeated Words実験では約5000語付近で生成されていない単語が出現する等の破綻が観測された。LongMemEval評価では焦点を絞ったプロンプト（~300トークン）と完全プロンプト（~113,000トークン）で顕著な性能差が確認された。
  出典: [Context Rot: How Increasing Input Tokens Impacts LLM Performance \| Chroma](https://www.trychroma.com/research/context-rot)

### 不確実・出典が弱い情報

- 「200Kトークンウィンドウのモデルが約50Kトークン付近で顕著に劣化し始める」という具体的な閾値は、検索結果のスニペット（morphllm.com 等の二次ソース）で言及されていたが、Chroma の一次ページを直接 WebFetch した際にはこの具体的な数値を再確認できなかった。この閾値は**二次ソース由来の未検証情報**として扱うこと。

### `/epic` への当たり

- `/epic` の L0→L1→L2 の3階層設計は、Claude Code の公式深さ上限（depth 5 でAgentツール剥奪）に対して十分な余裕（2階層のみ消費）を持つ。深さの数え方が「foreground/background を問わない」ことも確認済みなので、L1 ランナーを background で起動しても深さ計算は変わらない。
- SKILL.md ステップ3-3の「L2で頭打ち・L3が必要ならinlineフォールバック」という運用は、公式仕様の "resuming a subagent from a shallower context doesn't let it spawn additional levels" と整合的な保守的設計である。
- `epic-runs.md`（Ti → サブRUN_DIRの対応記録）は、Anthropic の "subagent output to a filesystem to minimize the game of telephone" と同型のパターンであり、外部一次情報のベストプラクティスと合致する。
- 一方で、`/epic` の各サブ pir2 に渡す「先行成果物のパス・変更ファイル一覧・git diff確認指示」の**注入内容の詳細度**が、Anthropic が強調する "each subagent needs an objective, an output format, guidance on the tools and sources to use, and clear task boundaries" の水準を満たしているかは、今回の外部調査だけでは判定できない（SKILL.md 記載はやや簡潔）。この評価は推測であり、必要なら別途実際のプロンプト内容の精査が要る。

---

## 3. 信頼性・無応答/タイムアウト・リトライ

### 確定的な事実（出典あり）

- **Claude Code 自身の既知バグ（GitHub Issue #44783、Closed as not planned）**: 親セッションがサブエージェント（Agent/Taskツール）の実行ハングによって完全に応答不能になるデッドロックが報告されている。再現手順は「2つのサブエージェントを並列（フォアグラウンド）起動→一方のBashツール呼び出し（例: curlのAPIハング）が無限にハング→親セッションが両方の返却を待ち続ける」。ログでは、片方のサブエージェントは完了しているのに結果が親に配信されず、ユーザーのフォローアップメッセージも enqueue されたまま dequeue されない状態が7時間以上継続、最終的に手動でセッションプロセスを強制終了するまで回復しなかった。タイムアウト機構・ウォッチドッグ・サーキットブレーカー・Escキーによる割り込みのいずれも機能しなかった。Issue のステータスは "stale" ラベル付きで "Closed as not planned"、メンテナからの明示的コメントは確認できなかった。
  出典: [Parent session deadlocks when subagent tool execution hangs — no timeout or recovery · Issue #44783 · anthropics/claude-code](https://github.com/anthropics/claude-code/issues/44783)

- **Claude Code の API エラー処理（v2.1.199以降の部分的な緩和）**: フォアグラウンドのサブエージェントがレート制限・サーバーエラー等のAPIエラーで打ち切られた場合、既に出力があれば "the Agent tool returns that partial output with a note that the subagent was cut off and didn't finish its task"。バックグラウンドの場合は "the subagent is marked failed, and the message Claude receives... names the API error and includes the subagent's last output"。ただしこれは **API呼び出しレベルのエラー**への対策であり、Issue #44783 が指摘する「ツール呼び出し（Bash等）自体が無限にハングする」ケースとは別物（後者への対策は明示的に存在しない）。
  出典: [Create custom subagents - Claude Code Docs](https://code.claude.com/docs/en/sub-agents)（"API errors in subagents" セクション）

- **Anthropic のエラー処理哲学**: "Without effective mitigations, minor system failures can be catastrophic for agents. When errors occur, we can't just restart from the beginning: restarts are expensive and frustrating for users. Instead, we built systems that can resume from where the agent was when the errors occurred." ツール失敗時は強制リスタートではなく "letting the agent know when a tool is failing and letting it adapt works surprisingly well"（決定論的セーフガードとモデルの適応性を組み合わせる）。ツール記述の欠陥を検出・自動改善する「tool-testing agent」導入で40%のタスク完了時間短縮を達成。
  出典: [How we built our multi-agent research system \| Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)

### 不確実・出典が弱い情報（practitioner blog レベル、ベンダー公式ではない）

- サーキットブレーカーの Closed/Open/Half-Open 状態管理、DEGRADED状態、グラフ状態内での共有 `failed_services` リストによるルーティング回避、並列エージェント間の retry storm（個別 backoff がグローバルでないため同時に死んだサービスを叩き続ける問題）、ハード・イテレーション上限／トークン・コスト予算のハード制限／no-progress detection といった実務パターンは、複数の practitioner blog（Medium, LifeTideshub, naitive.cloud 等）で言及されているが、**ベンダー公式ドキュメントでの明文化は確認できなかった**。ツール層でのエラー分類（一時的エラーのみリトライ対象にスコープする）という考え方も同様に二次ソースレベル。
  出典（参考・二次ソース）: [Resilience Circuit Breakers for Agentic AI](https://medium.com/@michael.hannecke/resilience-circuit-breakers-for-agentic-ai-cc7075101486), [Multi-Agent Error Recovery Patterns](https://blog.naitive.cloud/error-recovery-multi-agent-systems-key-patterns/), [Detecting AI Agent Failure Modes in Production](https://latitude.so/blog/ai-agent-failure-detection-guide)

### `/epic` への当たり（重要度: 高）

- **これは `/epic` 設計における最重要の懸念点である**。`/epic` ステップ3-1「独立サブタスクの並列fan-out」は「同一メッセージ内で複数 `Agent` 起動」を明示的に指示しており、これは GitHub Issue #44783 の再現条件（並列フォアグラウンドAgent起動）と構造的に一致する。もし並列起動されたネスト pir2 のいずれか1体が、その配下の implementer/tester フェーズで Bash コマンド（例: dev server起動待ち、外部APIへのcurl、無限ループするテスト実行）を実行してハングした場合、epic 本体のメイン会話全体がデッドロックし、ユーザーの追加メッセージも処理されなくなるリスクがある。この Issue は "Closed as not planned" であるため、**Anthropic側での修正は期待できず、`/epic` 側のプロンプト設計・運用でしか緩和できない**。
- 具体的な緩和策候補（本探索からの示唆であり実装提案ではない）: (a) ネスト pir2 ランナーおよびその配下の implementer/tester に対し、長時間ブロッキングしうる Bash コマンド（サーバー起動待ち・外部通信・無限ループしうるテスト）を避け `run_in_background` + ポーリングへ誘導する既存 CLAUDE.md の dev-server 運用方針を、epic 経由のネスト pir2 にも明示的に継承させる、(b) 並列 fan-out の起動体数を絞る、(c) 万一のデッドロックに備えた「ユーザーへの想定復旧手順（セッション再起動）」を epic の運用ドキュメントに明記する。これらは推測に基づく提案であり、採否はユーザー判断が必要。

---

## 4. チェックポイント/再開（resume）

### 確定的な事実（出典あり）

- **LangGraph の durable execution 公式仕様**: "Durable execution is a technique in which a process or workflow saves its progress at key points, allowing it to pause and later resume exactly where it left off." Checkpointer（例: PostgresSaver, SqliteSaver）は "every superstep" でグラフ状態のスナップショットを永続化し、同じ `thread_id` で `graph.invoke()` を呼び出すことで中断箇所から再開できる。ベストプラクティスとして「非決定的操作（乱数生成等）や副作用のある操作（ファイル書き込み・API呼び出し）は task 内にラップし、resume 時に再実行せず永続化層から結果を取得する」ことが明記されている。
  出典: [Durable execution - Docs by LangChain](https://docs.langchain.com/oss/python/langgraph/durable-execution)

- **LangGraph の human-in-the-loop も同一永続化層に依存**: `interrupt()` はノード内でグラフを一時停止し呼び出し元にペイロードを返す関数で、グラフ状態は永続化層に保存されるため安全に一時停止・再開できる。再開は `Command(resume=user_input)` で行う。この機構を使うには `thread_id` の指定が必須。
  出典: [Human-in-the-loop - Docs by LangChain](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)

- **Claude Code のサブエージェント・トランスクリプト永続化**: 各サブエージェントのトランスクリプトは `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl` に独立して永続化される。メイン会話が compaction されてもサブエージェントのトランスクリプトは影響を受けない。セッションを再起動した後も同一セッションを resume すればサブエージェントを resume できる（`SendMessage` ツールで agent ID/name 宛に送信）。トランスクリプトは既定 `cleanupPeriodDays`（既定30日）で自動クリーンアップされる。
  出典: [Create custom subagents - Claude Code Docs](https://code.claude.com/docs/en/sub-agents)（"Resume subagents" セクション）

- **Anthropic のリサーチシステムにおける「計画の永続化」**: lead agent はコンテキストが200,000トークンを超えるとtruncateされるリスクがあるため、研究計画を外部Memoryへ即座に保存し、コンテキスト溢れ時にも計画を喪失しない設計にしている。
  出典: [How we built our multi-agent research system \| Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)

### 論争点

- LangGraph・CrewAI・Google ADK 等の「チェックポイント永続化」を「真の durable execution」と呼ぶことに異議を唱えるベンダー系ブログ記事（Temporal競合製品ベンダーの Diagrid 社ブログ "Why Checkpoints Aren't Durable Execution"）が検索結果に見つかったが、**今回はページ本文を直接 WebFetch で検証しておらず、検索スニペットレベルの情報にとどまる**。チェックポイント方式（状態スナップショット＋thread_id再開）と Temporal 型の真の durable execution（決定論的リプレイ保証）の違いは実務上の論争点として存在することは把握できたが、具体的な主張内容の裏取りは未完了。
  出典（未検証・参考のみ）: [Why Checkpoints Aren't Durable Execution: LangGraph](https://www.diagrid.io/blog/checkpoints-are-not-durable-execution-why-langgraph-crewai-google-adk-and-others-fall-short-for-production-agent-workflows)

### `/epic` への当たり

- `/epic` は `EPIC_RUN_DIR` 配下に `epic-plan.md` / `epic-runs.md` / 各サブ `deferred-decisions.md` をファイルとして永続化する設計であり、これは LangGraph の checkpointer が担う「進捗の永続化」と機能的に類似する（ただし LangGraph のような自動スナップショット＋`thread_id`再開の仕組みではなく、明示的なファイル書き出しによる手動運用に近い）。
- SKILL.md を読んだ限り、`/epic` 自体に「エピック実行が中断された場合に `EPIC_RUN_DIR` から自動的にどこから再開するか」を判定するロジックの記載は見当たらなかった（未確認・スコープ外）。Claude Code のサブエージェント・トランスクリプトが `sessionId` に紐づいて独立永続化される仕様（上記）を踏まえると、**同一 Claude Code セッションを resume すれば個々のネスト pir2 サブエージェントの続きは技術的に可能**と考えられるが、これは公式ドキュメントの一般的仕様からの推測であり、`/epic` がこの機構をどこまで活用する設計になっているかは SKILL.md からは確認できなかった。この点は EXPLORATION_NEEDED として扱うのが妥当。

---

## 5. ヒューマン・イン・ザ・ループのゲート集約（deferred decisions / conservative default）

### 確定的な事実（出典あり）

- **AWS Well-Architected Framework「Agentic AI Lens」公式ベストプラクティス AGENTSEC04-BP02（Human-in-the-loop for critical decisions）**: "Routing every agent action through human review produces rubber-stamp approvals. Routing none produces unbounded autonomy. Risk-tiered approval pauses agents only for the decisions where human judgment actually changes the outcome." 具体的な階層: 読み取り専用操作は自律実行、低リスクの書き込みは単一レビュアー承認、金融取引・データ削除・外部通信等の高リスク操作はより厳格な承認（単一/複数レビュアー/帯域外）。**リスク分類器はLLMに依存させず決定論的ロジック（ポリシーエンジン・ルールベース）を権威とする**べきとされる。理由: "Risk classification itself can't rely on an LLM exposed to the same untrusted content as the request being evaluated, because adversarial content could influence the classifier into marking the request as low-risk."（LLM分類器はプロンプトインジェクションで低リスクと誤判定されうる）。既知アンチパターン: "Providing reviewers with insufficient context (the proposed action only, without the reasoning chain, data sources, or potential consequences), turning review into a formality." "Implementing approval workflows without timeout policies or escalation paths, so agent execution stalls indefinitely when reviewers are unavailable." タイムアウト発生時の既定フォールバックは「安全側＝操作をブロックする」。承認決定はレビュアーID・タイムスタンプ・決定内容・エスカレーションイベントを含めて監査ログ化する。
  出典: [AGENTSEC04-BP02 Human-in-the-loop for critical decisions - AWS Well-Architected Agentic AI Lens](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentsec04-bp02.html)

- **AWS Bedrock の Return of Control（ROC）パターン**: サブエージェント（collaborator agent）が人間に直接聞けない構造のとき、関数呼び出し自体を呼び出し元アプリケーションに返却し、アプリケーション側が「ユーザーに提示する／検証する／パラメータを修正する／拒否する」を決定する。ROC はアクショングループ単位で設定し、そのグループの全アクションに適用される。ユーザー確認（User confirmation）パターンはよりシンプルに関数名とパラメータを yes/no 形式で呼び出しアプリに返す。
  出典: [Use multi-agent collaboration with Amazon Bedrock Agents](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-multi-agent-collaboration.html) / AGENTSEC04-BP02 内の参照リンク（[Amazon Bedrock Agents return of control](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-returncontrol.html)）

- **Claude Code 公式仕様: エージェント発のメッセージはユーザー承認の代替にならない**: "As of v2.1.198, a subagent treats messages from the agent that launched it as normal task direction, including mid-task course corrections, and acts on them within its own permission settings. Two limits still hold regardless of who sent the message: no message from any agent counts as your approval for a pending permission prompt, and no agent message can change a subagent's permission settings, CLAUDE.md, or configuration. Only the permission system or your own messages can grant approval."
  出典: [Create custom subagents - Claude Code Docs](https://code.claude.com/docs/en/sub-agents)

### 不確実・出典が弱い情報

- 「エージェントが自身のパラメータ範囲外の状況に遭遇した際、最悪の選択は推測すること。正しい対応はエスカレーションであり、判断に必要な文脈を添えて人間に状況を提示すること」という定式化は、複数の practitioner blog（Galileo, ClarityArc等）で類似の表現が見られたが、AWS公式ドキュメントほどの一次性はない。ただし内容自体は AWS Well-Architected の公式記述（リスク階層化・エスカレーション）と方向性が一致する。

### `/epic` への当たり

- `/epic` の「ネスト pir2 ランナーは pir2 内部のユーザー確認ゲートに到達したら**保守的デフォルト**を選び、`deferred-decisions.md` に記録し `DEFERRED_USER_DECISIONS` として epic 本体に bubble-up する」という設計は、AWS Well-Architected の risk-tiered escalation（軽微なものは自律処理／本質的にブロッキングなものは人間判断へ）および Bedrock の ROC パターン（サブエージェントが直接ユーザーに聞けない場合は呼び出し元＝上位オーケストレーターに判断を委ねる）と**構造的に極めて近い**。
- また Claude Code 自体が「エージェント発メッセージは承認の代替にならない」という制約を持つため、`/epic` が「ユーザー対話は epic 本体に集約する」と明記している設計は、この Claude Code の一次仕様と整合する必然的帰結である（ネスト pir2 がユーザーに承認を求めたくても Claude Code の仕組み上できないため、epic 本体に上げるほかない）。
- 一点、AWS 公式ガイドが強調する「タイムアウトポリシーとエスカレーションパス」（レビュアー不在時の安全側フォールバック＝操作をブロック）に相当する仕組みは、`/epic` の SKILL.md からは明示的に確認できなかった。`DEFERRED_USER_DECISIONS` は「軽微なものは Phase 3 サマリーで一括報告」とあるが、これは**遅延報告**であり AWS の言う「タイムアウト時に安全側へブロックする」設計とは異なる（epic は基本的に承認を待たずに保守的デフォルトで進行を続ける設計であり、これは意図的なトレードオフと考えられる）。この差異自体は良し悪しの評価ではなく、外部プラクティスとの構造差異として記録する。

---

## 6. 観測可能性（observability）

### 確定的な事実（出典あり）

- **Anthropic: フルトレーシングの必要性**: "Adding full production tracing let us diagnose why agents failed and fix issues systematically."　エージェントの動的な意思決定・非決定性のため、従来のstep-by-stepデバッグ手法は "routinely fall short"。個々の会話内容を監視せず、エージェントの意思決定パターンとインタラクション構造のみを高レベルで監視することでプライバシーを保ちながら根本原因診断と共通失敗パターンの発見を実現している。小規模サンプル（20クエリ程度）での即時評価サイクルによりプロンプト変更の効果を素早く可視化する。
  出典: [How we built our multi-agent research system \| Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)

- **Claude Code のサブエージェント・ツリー可視化**: プロンプト入力欄下のサブエージェントパネルが全ツリーを表示し、各行に子孫数 `(+N)` を表示、ある行を開くとそのサブエージェントの兄弟・直接の子・mainまでのパスが表示される（v2.1.193以降）。
  出典: [Create custom subagents - Claude Code Docs](https://code.claude.com/docs/en/sub-agents)

- **OpenTelemetry GenAI Semantic Conventions（草案段階）**: エージェントのライフサイクルスパンとして `create_agent` / `invoke_agent`、ツール実行として `execute_tool` が新設され、必須のduration メトリック `gen_ai.client.operation.duration`、推奨のトークン使用量メトリック `gen_ai.client.token.usage` が定義されている。コンテンツキャプチャについては「記録しない／スパンに直接記録する／外部保存して参照のみ記録する」の3パターンが示され、プライバシー・保持ポリシー・コスト管理の観点から3番目（外部保存＋参照）が本番運用でスケールする唯一の選択肢だとされる。**ただし2026年4月時点でGenAI/MCPのセマンティック規約は "Development" ステータス（Stable未達）** であり、標準として未成熟である点に注意。
  出典（規約本体は移設されてページ内容を直接検証できなかったため、複数の二次ソースの記述内容が収束していることで確認）: [OpenTelemetry GenAI semantic conventions（現行リポジトリ案内）](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/) 、参考: [How OpenTelemetry Traces LLM Calls, Agent Reasoning, and MCP Tools](https://greptime.com/blogs/2026-05-09-opentelemetry-genai-semantic-conventions)

### 不確実・出典が弱い情報

- OpenTelemetry の具体的なスパン名・属性リストは、一次仕様ページ自体が移設中でWebFetch2回とも本文取得に失敗したため、**複数の二次ソース（ブログ）が一致して報告している内容**として記載した。仕様ページの verbatim 確認はできていない点を明記する。

### `/epic` への当たり

- `epic-runs.md`（Ti → サブRUN_DIR対応の記録）は、Anthropic が言う「個々の会話内容を監視せず高レベルの意思決定パターン・構造のみ追跡する」観測可能性の考え方と、OpenTelemetryが推奨する「コンテンツは外部保存＋参照のみ記録」パターンの両方に、ファイルベースの簡易版として合致する。
- Claude Code のサブエージェント・ツリー可視化UI（`(+N)` 表示等）は `/epic` の3階層ネスト構造（L0→L1→L2）をトレースする上でネイティブに機能するはずであり、`/epic` 側で追加のトレーシング実装をしなくても、Claude Code 本体のUIが基礎的な観測可能性を提供している点は把握しておく価値がある。
- 一方で、Anthropic が強調する「小規模サンプルでの即時評価サイクル」（プロンプト変更の効果を素早く測る）に相当する仕組みは `/epic` の SKILL.md には見当たらず、`retrospector` によるメタ振り返り（Phase 3 実行後の事後分析）のみが定義されている。事前の低コスト検証サイクルという観点は `/epic` の現行設計にはギャップとして存在しうるが、これは試験実装段階の `/epic` に対する評価であり、確定的な欠陥指摘ではなく観察に留める。

---

## 参照した外部ソース

| ソース種別 | URL | 確認した内容 |
|-----------|-----|------------|
| Anthropic公式エンジニアリング記事 | https://www.anthropic.com/engineering/multi-agent-research-system | orchestrator-workerパターン、タスク粒度、伝言ゲーム対策、トークンコスト、エラー処理哲学、観測可能性 |
| Anthropic公式ブログ | https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them | マルチエージェントを使うべき/避けるべき場面、コンテキスト中心分割 vs 工程中心分割、検証サブエージェントパターン |
| Anthropic公式ブログ | https://claude.com/blog/multi-agent-coordination-patterns | 5つの調整パターン（Generator-Verifier, Orchestrator-Subagent, Agent Teams, Message Bus, Shared State）とトレードオフ |
| Claude Code公式ドキュメント | https://code.claude.com/docs/en/sub-agents | ネスト深さ上限(5)・深さ算出方式・コンテキスト分離・トランスクリプト永続化・resume・APIエラー処理・エージェント発メッセージの承認代替不可 |
| GitHub Issue（一次情報・実バグ報告） | https://github.com/anthropics/claude-code/issues/44783 | 並列サブエージェントのBashハングによる親セッションの完全デッドロック（Closed as not planned） |
| arXiv論文 | https://arxiv.org/abs/2307.03172 | Lost in the Middle: 長コンテキストのU字劣化パターン |
| arXiv論文 | https://arxiv.org/abs/2503.13657 、https://arxiv.org/html/2503.13657v2 | MAST: マルチエージェント失敗の3カテゴリ・14失敗モードの定量分析 |
| Chroma公式研究ページ | https://www.trychroma.com/research/context-rot | 18モデル横断の「Context Rot」実験、distractor/needle-question類似度/haystack構造の影響 |
| OpenAI公式ドキュメント | https://openai.github.io/openai-agents-python/multi_agent/ | Manager/Handoffパターン、粒度指針、コード駆動 vs LLM駆動オーケストレーション |
| OpenAI公式ドキュメント | https://openai.github.io/openai-agents-python/handoffs/ | Handoffの会話履歴引き継ぎ、構造化メタデータ付与 |
| CrewAI公式ドキュメント | https://docs.crewai.com/en/concepts/processes | 階層プロセスのmanager_agent設計 |
| Google公式ドキュメント | https://google.github.io/adk-docs/get-started/about/ | Sequential/Parallel/LoopAgentの決定論的ワークフローエージェント |
| Google公式ブログ | https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/ | ADKマルチエージェントパターンガイド |
| LangChain公式ドキュメント | https://reference.langchain.com/python/langgraph-supervisor | 多段階層スーパーバイザー(create_supervisor) |
| LangChain公式ドキュメント | https://docs.langchain.com/oss/python/langchain/multi-agent/subagents-personal-assistant | レイヤー分離の利点 |
| LangChain公式ドキュメント | https://docs.langchain.com/oss/python/langgraph/durable-execution | checkpointer・thread_id・resume・非決定操作のtaskラップ |
| LangChain公式ドキュメント | https://docs.langchain.com/oss/python/langchain/human-in-the-loop | interrupt()・Command(resume=...)によるHITL一時停止/再開 |
| AWS公式Well-Architected | https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentsec04-bp02.html | リスク階層化承認・決定論的リスク分類器・タイムアウト/エスカレーション・監査ログ |
| AWS公式ドキュメント | https://docs.aws.amazon.com/bedrock/latest/userguide/agents-multi-agent-collaboration.html | supervisor-collaboratorモデル、役割重複の最小化 |
| （二次ソース・未検証） | https://www.diagrid.io/blog/checkpoints-are-not-durable-execution-why-langgraph-crewai-google-adk-and-others-fall-short-for-production-agent-workflows | チェックポイント≠真のdurable executionという論争（本文未検証） |
| （二次ソース） | https://greptime.com/blogs/2026-05-09-opentelemetry-genai-semantic-conventions | OpenTelemetry GenAIスパン名・メトリックの記述（一次仕様ページ移設のため裏取り不完全） |

---

## 補足情報（リスク・空白・視覚情報との整合について）

- 本調査に「ユーザー提供の視覚的一次情報（スクリーンショット等）」は含まれていないため、視覚情報との自己整合チェックは非該当。
- 本調査は「○○は存在しない」型の断定を行っていない（外部情報の収集が主目的であり、コードベース内の機能有無を判定するタスクではないため、explorer.md の「存在しない結論チェックリスト」は直接適用対象外。ただし `/epic` に「チェックポイント/再開の明示ロジックが見当たらなかった」という記述は行っており、これは SKILL.md 1ファイルの通読のみに基づく限定的な観察であることを明記する）。
- **未解決の空白（EXPLORATION_NEEDED 相当）**:
  1. `/epic` が実際に「中断されたエピックの再開」をどう扱うか（Claude Code のセッション・サブエージェントresume機構をどこまで活用する設計か）は `.claude/skills/epic/SKILL.md` の通読のみでは確認できなかった。必要なら `~/.claude/skills/pir2/references/experimental.md` の `epic-orchestrator-nested-pir2` 実験セクションを別途確認すると判断材料が増える可能性がある（本探索のスコープ外につき未実施）。
  2. GitHub Issue #44783 が "Closed as not planned" になった正確な経緯（メンテナ判断の詳細）はコメント欄が確認できなかったため不明。issue本文とラベルのみが情報源。
  3. OpenTelemetry GenAI Semantic Conventions の一次仕様ページは調査時点で移設中につき本文を直接検証できず、スパン名・属性は二次ソースの収束情報に基づく（確度は中程度）。
  4. Diagrid社ブログが主張する「チェックポイントは真のdurable executionではない」論争の具体的根拠は本文未検証（検索スニペットのみ）。

## 呼び出し元への依頼

- 本探索は「/epic のようなネスト起動オーケストレーション」全般を対象とした外部知見収集であり、ライブラリ選定判断は行っていない（該当なし）。
- 上記「未解決の空白」の 1. について、`/epic` の resume/checkpoint 設計の実態をさらに深掘りしたい場合は、別途 `~/.claude/skills/pir2/references/experimental.md` の該当セクションを読む explorer をもう1体、または本熟考（deepthink）の後続フェーズで直接 Read することを推奨する。
- GitHub Issue #44783（並列サブエージェントのハングによる親セッションデッドロック）は、`/epic` のステップ3-1「独立サブタスクの並列fan-out」設計に対する具体的リスクとして、後続の熟考フェーズ（deliberator）で重点的に扱う価値が高いと判断する。
