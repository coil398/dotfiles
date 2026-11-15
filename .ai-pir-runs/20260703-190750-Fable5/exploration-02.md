# 探索レポート: M2（サブエージェントの外形検証によるゾンビ成功・捏造検知）のプラットフォーム的実現可能性

## 結論（先出し）

| 検証対象 | 実現可能性 | 根拠の要点 |
|---|---|---|
| **A. `tool_uses`/`duration`/`status` を hook 経由で決定論的に取得** | **条件付き可能** | `SubagentStop` は生の値（`tool_uses` 数や `duration`）を**直接**は返さないが、`agent_transcript_path`（サブエージェント自身の transcript JSONL への絶対パス）を返す。hook スクリプトが `jq`/`grep` でこの JSONL を解析すれば `tool_uses` 件数・`duration`（先頭/末尾タイムスタンプ差）を**純 bash で決定論的に算出**できる。加えて `PostToolUse`（matcher=`Agent`）の `tool_response` には `totalToolUseCount` / `totalDurationMs` / `totalTokens` / `status`（`"completed"`/`"async_launched"`）が**そのまま**入っているが、これは**フォアグラウンド（同期）実行時のみ**。v2.1.198 以降サブエージェントは既定でバックグラウンド実行になり、その場合 `tool_response` に usage フィールドが乗らない。`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` で強制同期化すれば解消する |
| **B. 役割別 floor との突合をオーケストレーター LLM の判断抜きで強制** | **可能** | `SubagentStop` hook は `decision:"block"` を返すと**サブエージェント自身を継続させ** `reason` を次の指示として渡せる（親には戻らない）。matcher にはサブエージェントの `agent_type`（= `.claude/agents/<name>.md` の `name`）をそのまま指定できるため、役割別 floor 値を hook 設定側にハードコードして matcher で振り分けられる。オーケストレーター（親 LLM）の自己申告判断を介さず、bash 側で完結する |
| **C. implementer 申告ファイル集合 vs 実 `git diff --name-only`** | **完全に可能（hook 不要）** | これは hook にも LLM 判断にも依存しない。`SubagentStop` の `last_assistant_message` から申告ファイルリストを固定フォーマットで抽出し、`git diff --name-only`（または `git status --porcelain`）の実行結果と bash の集合比較で突合できる。LLM の「判断」を挟まず機械的に一致/不一致を出せる |
| **D. 並列 fan-out ハング（GitHub #44783）** | **未解決（公式に closed as not planned）** | 2026-04 起票、2026-06-03 に "inactive" 理由で stale-bot が自動クローズ。Anthropic からの修正コメント・ワークアラウンド提示は皆無。本 dotfiles の PIR² は既に reviewer 5観点並列・ui-ux-reviewer 並列・epic の独立サブタスク並列 fan-out を採用しており、この既知ハングリスクを**既に負っている**（M2 導入で新たに背負うリスクではない）。ただし M2 を並列 fan-out 経路に適用する場合、1体がハングすると hook 自体が永久に発火せず、オーケストレーターはブロックされ続ける（ゾンビ"成功"ではなく完全ストールになるので破壊力は異なるが、可用性リスクとして別途認識すべき） |

**総合判定**: M2 の hook 依存部分は「今すぐ本気で直す」に値する**プラットフォーム的に実現可能**な設計である。ただし「hook が計測値を渡してくれる」という素朴な期待（トークンで観測された `tool_uses`/`duration_ms` フィールド）は **SubagentStop には存在しない** ため、実装は「hook が生 transcript を渡す → hook スクリプト自身が jq で集計する」という一段階の追加実装が必須になる。単純な「hook の JSON を読むだけ」では実現しない。

---

## 1. `SubagentStop` hook の入力スキーマ（一次ソース検証済み・verbatim）

`https://code.claude.com/docs/en/hooks` の実際にレンダリングされた JSX ソース（`WebFetch` の要約ではなく、`curl` で取得した生 HTML から JSX props 文字列を直接抽出して検証）から復元した exact スキーマ:

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../abc123.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "SubagentStop",
  "stop_hook_active": false,
  "agent_id": "def456",
  "agent_type": "Explore",
  "agent_transcript_path": "~/.claude/projects/.../abc123/subagents/agent-def456.jsonl",
  "last_assistant_message": "Analysis complete. Found 3 potential issues...",
  "background_tasks": [],
  "session_crons": []
}
```

ドキュメント本文の該当記述（verbatim、日本語訳付き）:

> "In addition to the common input fields, `SubagentStop` hooks receive `stop_hook_active`, `agent_id`, `agent_type`, `agent_transcript_path`, and `last_assistant_message`. The `agent_type` field is the value used for matcher filtering. The `transcript_path` is the main session's transcript, while `agent_transcript_path` is the subagent's own transcript stored in a nested `subagents/` folder. The `last_assistant_message` field contains the text content of the subagent's final response, so hooks can access it without parsing the transcript file."
>
> （訳: common input fields に加え、`SubagentStop` hook は `stop_hook_active` / `agent_id` / `agent_type` / `agent_transcript_path` / `last_assistant_message` を受け取る。`agent_type` は matcher フィルタリングに使う値そのもの。`transcript_path` はメインセッションの transcript、`agent_transcript_path` はサブエージェント自身の transcript（`subagents/` サブフォルダ配下）。`last_assistant_message` にはサブエージェントの最終応答のテキストが直接入っており、transcript ファイルをパースしなくてもアクセスできる）

> "`background_tasks` and `session_crons` arrays... available in Claude Code v2.1.145 or later. Both arrays are scoped to the parent session, not the subagent."

**明示的に無い項目**: `tool_uses` 件数、`duration`、`status`。ドキュメントのどこにも SubagentStop 用のこれらのフィールドは列挙されていない（`grep` で `"tool_uses"` は当該ページ内 0 件ヒット）。

**decision control（SubagentStop 固有）**:

> "SubagentStop hooks use the same decision control format as Stop hooks... Returning `decision: "block"` with a `reason` **keeps the subagent running** and delivers `reason` to the subagent **as its next instruction**. To inject context into the parent session after a subagent returns, use a `PostToolUse` hook on the `Agent` tool instead."

これは M2 にとって重要な性質: floor 未達を検知した場合、`decision:"block"` を返せば**親に戻る前にサブエージェント自身へ「もっと調査しろ」と再指示できる**（ゾンビ成功が親の context に到達する前に足止めできる）。

### 1-1. サブエージェント定義ファイル側でも hook を宣言可能（matcher = 役割名）

`https://code.claude.com/docs/en/sub-agents` より:

> "Configure hooks in `settings.json` that respond to subagent lifecycle events in the main session."
>
> | Event | Matcher input | When it fires |
> |---|---|---|
> | `SubagentStart` | Agent type name | When a subagent begins execution |
> | `SubagentStop` | Agent type name | When a subagent completes |
>
> "The matcher value is the agent's frontmatter `name` for project-level and user-level subagents... A hyphenated matcher like `db-agent` matches exactly on Claude Code v2.1.195 or later. On earlier versions it is evaluated as an unanchored regular expression."

つまり `.claude/agents/explorer.md` / `implementer.md` / `reviewer.md` の `name:` frontmatter がそのまま matcher 値になる。役割別 floor（例: explorer は tool_uses ≥ N、implementer は git diff 非空必須）を **matcher ごとに個別 hook エントリとして `settings.json` に静的定義**できる。インストール済みバージョンは `2.1.199` のため hyphenated exact-match 挙動（v2.1.195+）も有効。

---

## 2. `PostToolUse`（matcher=`Agent`）の `tool_response` スキーマ（一次ソース検証済み・verbatim）

同じく `code.claude.com/docs/en/hooks` の実 JSX から復元した Agent ツールの `tool_response`（フォアグラウンド完了時）のフィールドテーブル:

| Field | Type | Example | Description |
|---|---|---|---|
| `status` | string | `"completed"` | `"completed"` for foreground subagents, `"async_launched"` for background subagents. As of v2.1.198, subagents run in the background by default, so an omitted `run_in_background` also produces `"async_launched"` |
| `agentId` | string | `"a4d2c8f1e0b3a297"` | Identifier for the subagent run |
| `content` | array | `[{"type":"text","text":"Found 12 endpoints..."}]` | The subagent's final text blocks |
| `resolvedModel` | string | `"claude-sonnet-4-5"` | Model the subagent ran on（v2.1.174+） |
| `totalTokens` | number | `12450` | Total tokens billed across the subagent's turns |
| `totalDurationMs` | number | `48211` | Wall-clock duration of the subagent run |
| `totalToolUseCount` | number | `7` | **Count of tool calls the subagent made** |
| `usage` | object | `{"input_tokens": 8320, ...}` | `input_tokens` / `output_tokens` / `cache_creation_input_tokens` / `cache_read_input_tokens` |

これはまさに本セッションで観測された `tool_uses`/`duration_ms` 相当のフィールドが、**構造化データとして** `PostToolUse` の `tool_response` に乗っていることの一次ソース確認である。`tool_input.subagent_type`（例: `"Explore"`）も同じペイロードに同居しているため、**単一の `PostToolUse(matcher="Agent")` hook** で「どの役割か」と「実測 tool_uses/duration/status」を同時に読める。

### 2-1. ただし v2.1.198 以降は既定でバックグラウンド実行 → 素の状態では発火しない

> "For background subagents, the tool returns immediately after launching, so `tool_response` carries no usage fields. It has `status: "async_launched"`, `agentId`, `description`, `prompt`, `outputFile`, and `resolvedModel`."

GitHub 公式リリースノート（`gh api repos/anthropics/claude-code/releases` で直接取得、verbatim）v2.1.198:

> "Subagents now run in the background by default, so Claude keeps working while they run and is notified when they finish (previously a gradual rollout)"

`code.claude.com/docs/en/sub-agents` 該当節（verbatim）:

> "As of v2.1.198, subagents run in the background by default. **Claude runs a subagent in the foreground when it needs the result before continuing.** The default changes where a subagent runs, not what it's allowed to do... To disable all background task functionality, set the `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` environment variable to `1`."

つまり:
1. オーケストレーター（親 Claude）が「結果がすぐ要る」と**自己判断**すればフォアグラウンド実行になり `tool_response` にメトリクスが乗る（PIR² は各フェーズが直列依存なので、自然にこの判断がされやすい設計ではあるが、モデルの自己判断に依存するため**決定論的ではない**）
2. 決定論的に強制したい場合は `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`（環境変数、セッション全体に効く）で全サブエージェント spawn を同期化できる。`.claude/settings.json` の `"env"` キーに設定済みの前例が本リポにある（`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS: "1"`。同じ仕組みで `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` も追加可能）
3. 個別呼び出し単位では `run_in_background: false` を Agent ツールの `tool_input` に明示することでも同期化できる（`sub-agents` doc: "removes the `run_in_background` parameter from the `Agent` tool" という記述から、通常時はこのパラメータ自体が実在することが読み取れる）

**設計上の含意**: M2 を A 経路（PostToolUse の `tool_response` メトリクス）で実装するなら、PIR² 実行時は `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` を前提条件にする必要がある（さもないと既定で `async_launched` になり検証不能）。B 経路（SubagentStop + `agent_transcript_path` の自前パース）はこの制約を受けない（後述）。

---

## 3. git diff 側の決定論的成立性（hook 不要）

`SubagentStop` の `last_assistant_message` フィールドは「サブエージェントの最終応答テキストそのもの」を **transcript をパースせずに直接** 保持している。implementer が固定フォーマット（例: `## 変更ファイル\n- path/a\n- path/b`）で申告する運用にすれば、hook スクリプトは:

1. `last_assistant_message` から申告ファイルリストを正規表現/`grep` で抽出
2. `cwd` で `git diff --name-only`（または `git status --porcelain`）を実行
3. 両集合を bash の `comm`/`diff` で突合
4. 不一致なら `decision:"block"` + `reason` で implementer に「申告と実差分が食い違う」と即時フィードバック

これは LLM 判断を一切挟まない機械比較であり、**hook のメタデータ取得可否とは独立に、現行 Claude Code のバージョンや将来の仕様変更に関係なく成立する**。M2 のこの半分は「今すぐ実現可能」の確度が最も高い部分。

---

## 4. 並列 fan-out ハング（GitHub #44783）の現在ステータス

`gh issue view 44783 --repo anthropics/claude-code --json state,stateReason,closedAt,comments` で直接取得（要約や third-party ミラーではなく GitHub API 生データ）:

| 項目 | 値 |
|---|---|
| `state` | `CLOSED` |
| `stateReason` | `NOT_PLANNED` |
| `createdAt` | 2026-04-07 |
| `closedAt` | 2026-06-03 |
| クローズ理由 | `github-actions` bot による自動クローズ（"Closing for now — inactive for too long"）。**Anthropic 側からの修正コメント・ワークアラウンド提示・原因説明は issue 内に一切無い** |

コメント欄の実データからの要点:
- 2つの並列サブエージェントの片方の Bash（`curl`）呼び出しがハングし、もう片方が正常完了しても**結果が親に届かず親セッションが恒久ブロック**する（数時間〜7時間超）
- 別ユーザーが Linux で `Glob` ツールでも同型の再現を報告（Bash/curl 固有ではなく「ツール実行結果が親に届かない」という IPC 層の一般的な欠陥と推定されている）
- 別ユーザー（Windows）は**単一**サブエージェントの `Task()` でも再現、かつ MCP サーバー未設定環境でも再現 → 並列・MCP 依存ではなく `parent↔subagent` の結果受け渡しチャネル自体の脆弱性と結論
- コミュニティ側ワークアラウンド（ファイルシステム経由の完了検知、タスクの細切れ化）はあるが、いずれも「Anthropic 側のランタイム修正待ち」の bandage と明言されている

**本リポへの含意**: `.claude/pir2-protocol.md` に既に「reviewer の5観点ハイブリッド並列」「ui-ux-reviewer の追加起動（同一メッセージ内で並列）」「epic の独立サブタスク並列 fan-out」が明記されており、本 dotfiles の PIR² 系スキルは**既にこのハングリスクを構造的に負っている**。M2 導入がこのリスクを新規に発生させるわけではないが、M2 の hook（SubagentStop/PostToolUse）を並列 fan-out 経路に適用する場合、ハングした 1 体の hook は永久に発火しないため、「ゾンビ成功の検知」ではなく「オーケストレーターの恒久ストール」という**別種の失敗モード**に転化する点は設計上明記しておくべき（M2 の feasibility とは別軸のリスクだが、隣接して評価されるべき事実）。

---

## 5. 既存 hook 実装からの示唆（本リポジトリ内の実データ）

`.claude/settings.json`（`/Users/kawasetakumi/dotfiles/.claude/settings.json`）の hooks 設定:

```json
"hooks": {
  "PreToolUse": [ /* matcher: "Bash", if: "Bash(git commit *)" 等 */ ],
  "PostToolUse": [ /* matcher: "Edit|Write|MultiEdit" → sync-opencode-hook.sh 等 */ ],
  "SessionStart": [ /* check-updates.sh */ ],
  "Stop": [ /* parse-failure-continue-hook.sh */ ]
}
```

**`SubagentStop` の設定例は本リポには現存しない**（`grep -r "SubagentStop" .claude/` で 0 件、`settings.json` にもキーなし）。つまり M2 は本リポにとって「初めて `SubagentStop`/`PostToolUse(matcher=Agent)` を使う」実装になる。ただし既存の `Stop` hook（`parse-failure-continue-hook.sh`）が確立している設計パターンはそのまま転用できる:

- stdin から JSON 全体を `input="$(cat)"` で受け取り、`grep -Eo` または `jq` でフィールド抽出（`foreign-project-name-guard.sh` は `jq -r '.tool_input.command // ""'` パターンを使用）
- ログを `$HOME/.claude/logs/<hook-name>.log` に退避（デバッグ・matcher 調整用の実データ確保）
- 判定不能な場合は必ず allow 側に倒す（`transcript_path` が読めない等 → `exit 0`）フェイルセーフ
- ブロック意図は `printf '{"decision":"block","reason":"..."}\n'` で JSON を stdout に出す形式（`exit 0` と併用。`exit 2` は別経路として `foreign-project-name-guard.sh` が使用 — stderr にメッセージを書いて exit 2 する PreToolUse 向けパターンも存在）

`.claude/hooks/foreign-project-name-guard.sh` は `jq` に依存しており、`jq` 未インストール環境では動かない設計（`sync-opencode-hook.sh` は `command -v jq` チェックで早期 return する防御あり）。M2 の hook を実装する場合も `jq` 依存の有無をどちらかに統一し、未インストール時のフェイルセーフ（allow 側に倒す）を踏襲すべき。

---

## 6. バージョン依存性のまとめ

| 機能 | 最低バージョン | インストール済みバージョンでの可否 |
|---|---|---|
| `SubagentStop` の `agent_transcript_path`/`last_assistant_message` | 明記の version gate なし（ドキュメント内に他機能では `v2.1.145 or later` 等の明示注記があるが、この2フィールドには注記が無い＝より古くからの基盤機能と推定） | 使用可 |
| `SubagentStop` の `background_tasks`/`session_crons` | v2.1.145+ | 使用可（`2.1.199` インストール済み、`claude --version` で実機確認） |
| `PostToolUse(Agent)` の `resolvedModel` | v2.1.174+ | 使用可 |
| サブエージェント既定バックグラウンド化 | v2.1.198+ | **該当**（インストール済み `2.1.199` は既にこの挙動下にある → M2 実装時は `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` 等の対策が前提条件） |
| hyphenated matcher の exact-match | v2.1.195+ | 使用可 |

`claude --version` 実行結果: `2.1.199 (Claude Code)`（本セッションで直接実行して確認、推測ではない）。

---

## 7. 参照した外部ソース

| ソース種別 | URL | 確認した内容 |
|---|---|---|
| 公式 doc（hooks リファレンス） | https://code.claude.com/docs/en/hooks | `SubagentStop`/`PostToolUse`/`Stop` 等の入力スキーマ全件。`curl` で生 HTML を取得し JSX props 文字列を直接パースして verbatim 抽出（WebFetch 要約の伝言ゲームを避け一次情報を直接検証） |
| 公式 doc（sub-agents） | https://code.claude.com/docs/en/sub-agents | フォアグラウンド/バックグラウンド実行の切り替え仕様、`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS`、`run_in_background` パラメータ、サブエージェント frontmatter hooks、`SubagentStart`/`SubagentStop` の matcher 仕様 |
| GitHub API（issue 生データ） | https://github.com/anthropics/claude-code/issues/44783 | 並列 fan-out ハングの現ステータス（`CLOSED`/`NOT_PLANNED`/stale bot 自動クローズ）、コメント全文 |
| GitHub API（issue 生データ） | https://github.com/anthropics/claude-code/issues/21837 | 「Task tool response に構造化メトリクスを」の feature request、`CLOSED`/`DUPLICATE`（→ #11320 の重複） |
| GitHub API（issue 生データ） | https://github.com/anthropics/claude-code/issues/11320 | 上記の重複先本体。`CLOSED`/`NOT_PLANNED`（2026-02-02）。Anthropic は本件を明示的に「対応しない」と判断済み — ただしこれは「テキスト応答に加えて構造化メトリクス欄を作る」というAPI改善要求全般の話であり、本調査で確認した `PostToolUse.tool_response.totalToolUseCount` 等は**この issue とは無関係に既に実装済み**（doc に明記されている）。つまり「feature request としては not planned」だが「実体としては既に一部実装されている」というねじれがある点は評価上重要 |
| GitHub API（releases） | https://github.com/anthropics/claude-code/releases（`gh api repos/anthropics/claude-code/releases`） | v2.1.198 リリースノート verbatim（"Subagents now run in the background by default..."） |

---

## 8. 補足情報・注意点

- **「ねじれ」の指摘**: issue #11320/#21837（"Task tool 実行メタデータの公開" feature request）は Anthropic により明示的に `NOT_PLANNED` とされているが、実際の hooks doc / sub-agents doc には `totalToolUseCount`/`totalDurationMs`/`totalTokens`/`status` が **`PostToolUse` の `tool_response` として現に文書化・実装済み**である。これは「issue 番号ベースで `not planned` だから機能も無い」と早合点してはいけないことを示す好例。本調査は issue の状態だけでなく、hooks 公式 doc を直接 `curl` して JSX ソースの verbatim を確認する二段階検証を行ったことで、このねじれを検出できた
- **`tool_uses` という完全一致のキー名は存在しない**: ユーザーが観測した表示上の「N tool uses」は UI 表示文言であり、プログラム側のキー名は `totalToolUseCount`（`PostToolUse.tool_response`）である。「hook 経由で `tool_uses` という名前のフィールドを読む」という実装は失敗する。実装時は `totalToolUseCount` を使うこと
- **SubagentStop 経路（B）の方が PostToolUse 経路（A）より頑健**: A はバックグラウンド既定化（v2.1.198+）の影響を直接受けるが、B（`agent_transcript_path` の自前パース）は同期/非同期の実行モードに関わらずサブエージェント自身が終了すれば必ず発火する（`Stop` が `SubagentStop` に変換される、というサブエージェントのライフカーブそのものに紐づくため）。M2 の主経路は B を推奨し、A は「フォアグラウンド強制時の補完的なクロスチェック」として位置づけるのが堅牢
- **`agent_transcript_path` の JSONL パース自体の実装コスト**: `tool_use` ブロックのカウントには `jq` で `.message.content[] | select(.type=="tool_use")` 相当の走査が必要（Claude Code の transcript JSONL の実データ構造は本調査では直接確認していない＝推測。前段の探索やこのあとの実装検討で実際の JSONL を 1 件 `cat`/`jq` して構造を確認するステップが必要）。duration は先頭行と末尾行の `timestamp` フィールド差分で計算できると推定されるが、これも実データでの構造確認が未実施であることは明記しておく（**推測であり検証済み事実ではない**）

---

## 9. 呼び出し元への依頼

- 本調査は「hook がメタデータを渡せるか」という一次情報確認に特化した。**実際の transcript JSONL（`agent_transcript_path` が指すファイル）のフィールド構造**（`tool_use` ブロックの正確なパス、`timestamp` フィールドの有無・形式）は未検証（推測に留まる）。deepthink の後続フェーズで実装設計まで踏み込む場合、別 explorer（または同一セッション内で）実際の `~/.claude/projects/<sanitized>/*/subagents/*.jsonl` を 1 件サンプルとして構造確認することを推奨する
- `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` を PIR² 系スキル実行時に設定する副作用（並列 fan-out 前提の reviewer 5観点並列・epic 独立サブタスク並列が「全部同期直列」に倒れコスト/レイテンシが増える可能性）は、M2 設計の trade-off として熟考フェーズで評価すべき論点。本 explorer はこの trade-off の是非判断はスコープ外とし、事実（背反関係の存在）のみを報告する
- ライブラリ選定判断は本調査には発生していない（Claude Code 自体の仕様確認のみ）ため tech-validator 起動は不要
