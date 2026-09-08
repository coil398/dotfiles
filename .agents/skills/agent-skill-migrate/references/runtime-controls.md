# サブエージェントの履歴・待機・配布の移行確認

この資料は移行を担当する親が読む。通常の実装・評価担当へ毎回読ませる専門資料ではない。対象runtimeの版、設定の所有元、実際の起動インターフェースを確認してから適用する。

## 原則と設定の所在

親は子の目的、対象と版、必要な背景、確定事項と仮説・未確定事項、変更可能範囲、制約、完了条件、専門資料の実体パスを渡す。子へ親の会話を全量・部分量ともコピーしない。資料を参照しても解決しない不足は親が補う。専門手順はSkill/referenceから読み、親の会話や毎回の専門本文の転記で代用しない。

同じ子が自分の作業履歴を使って継続すること、親自身の長期作業を再開すること、利用者が明示的に別チャットへ分岐することは、新しい子への親履歴継承とは別である。これらの機能や保存済み履歴を一括削除しない。

現在のdotfilesでは、Codex設定の正本は`.codex/config.base.toml`、起動方針は`.codex/codex-native-supplement.md`、Cursorの選択方針は共有`AGENTS.md`にある。対象repoの移行では所有元を確認し、同じ数値・モデル表を各Skillや個人HOMEへ新しく複製しない。

## Codex：要求と強制を区別する

- 履歴なしの要求は、すべての新規V2 `spawn_agent`で`fork_turns="none"`を明示する形へ揃える。「通常は」「モデル変更時だけ」「必要なら部分履歴」という例外は残さない。既存のV1だけを扱う場合はその公開引数を確認し、V2の引数を移植しない。
- Codex 0.153.4のV2では、`fork_turns`は起動引数で、省略時に`all`を選ぶ。確認した`MultiAgentV2ConfigToml`には履歴継承を禁止する設定項目がない。したがって、上の運用要求は強制設定の実現を意味しない。[C1][C2]
- `fork_turns`、`fork_context`、`default_fork_turns`等を、未対応の設定表へ推測で追加しない。`usage_hint_text`などに文章を入れる方法も、起動引数を強制する機能とは区別する。独自PreToolUse書換hook、proxy、独自ビルドを移行に追加しない。
- 「全履歴forkなら必ず親モデルに固定される」と一般化しない。履歴、モデル・effort、実効権限は別々に、その版のhandlerと観測で確認する。履歴なしでも通常指示と権限が消えるわけではない。[C2]
- 今後の版でネイティブの強制設定が追加されていた場合は、存在するキーだけでなく、明示的な`all`・部分履歴を拒否または補正する挙動まで確認する。単に省略時の値を変える設定を「禁止」と呼ばない。利用者が許可した範囲でのみ導入する。

## Codex：待機は既存の設定で保持する

`features.multi_agent_v2`の`enabled`、`min_wait_timeout_ms`、`default_wait_timeout_ms`、`max_wait_timeout_ms`は、対応する版と有効backendを確認して扱う。既に承認された所有元の値を保ち、生成後も一致するか確認する。値を本文へ固定して他repoへ配らない。[C1][C3]

待機設定の検査では、下限・既定値・上限の順序、単位がmsであること、版の許容範囲を確認する。V2の下限は短い指定を補正するが、V1や別ツールのpollには適用されない。完了・重要な連絡・追加入力で早期に戻ることと、通知なしで停止した子の発見が遅れる可能性を区別する。[C3]

これらは親の`wait_agent`の期限であり、子の実行全体を終了させる期限ではない。`job_max_runtime_seconds`を実行上限として復活させない。0.153.4の該当フィールドはno-opである。子の実行期限が別途要求された場合は、既存runnerで本当に対応する範囲とnativeでの未対応を分け、新しいrunnerを自動追加しない。[C4]

## Codex：コンテキストと自動圧縮

`model_context_window`、`model_auto_compact_token_limit`、`model_auto_compact_token_limit_scope`は、設定ファイルのトップレベルに置く。dotfilesでは`.codex/config.base.toml`を数値の正本とし、既存の生成・配布で引き継ぐ。`[agents]`や`[features.context_management]`の中へ移したり、各Skill・別repoへ数値を複製したりしない。現在の計測範囲は`total`で、初期prefixを除く`body_after_prefix`へ移行時に変更しない。[C5]

`features.context_management.experimental_mode`の有効化は、上記の文脈枠・圧縮基準とは別である。承認済みの有効設定を保持する。設定がtrueでも、実行版・認証方式・プラン・backendの条件を満たさなければ新方式の実稼働は確認できない。未対応の接続へ移行する際は、その制約を明記する。[C7]

子は親のeffective configから開始するため、履歴なしの起動でも文脈枠と圧縮基準を引き継ぎ得る。モデルごとの上限で制限されることを確認し、親だけの設定と説明しない。子の最大枠を増やしても直ちにその量の入力が発生するわけではないが、長い子の実行では入力増加やモデル固有の価格条件に注意する。[C6][C8]

圧縮基準の値と実際の切替地点は区別する。新方式の状態保存用bufferや実効上限によって切替時点が変わるため、基準の数値ぴったりで必ず圧縮するとは説明しない。生成後のトップレベル値・scope・既存の実験設定を照合し、新規セッションで文脈枠とnotes/historyの実動作を別に確認する。文脈拡張を使用量削減の保証と扱わない。[C7][C9]

## Cursor：独立コンテキストと待機方法

通常のTaskは新しいコンテキストを使い、親が必要な情報を渡す。会話Fork・Side chatを子の代わりに使って履歴を持ち込まない。Codexの`fork_turns`やV2待機キーをCursorへ追加しない。[X1]

子の結果が次の処理の前提で、親に別の有用な作業がなければForegroundを使う。独立した並列作業・親の別作業・Fable panel・非同期recallはBackgroundを維持する。`is_background: false`を全定義へ複製して、必要な並列実行を直列化しない。既存の明示Background指定は用途を確認してから変更する。[X1]

Foreground / Backgroundの選択方針は、Cursor内部で待機中のモデル呼出が完全になくなる保証ではない。完了通知を使い、同じ状態・ログの短周期再読込、変化のない連絡、終了済みの子の重複起動を避ける。

## 原本・生成・配布の確認

1. 原本と現在有効な設定の所有範囲を確定し、認証、承認、親モデル、通常子、実験機能の無関係な変更をしない。別repoの移行だけでV2を新規有効化しない。
2. native supplement、既存Skillの呼出し例、移行Skill、関連文書から、親履歴継承を許す規則と誤った強制済みの説明を除く。履歴forkと同じ子の継続を取り違えない。
3. 対象端末で既存の生成・配布処理を使う。dotfilesでは`bash etc/link.sh --codex-cursor-only`。Cursorの入口だけでなく参照する共有packageの到達先も確認する。ローカルの生成configやhook trust hashをGitへ持ち込まない。
4. 関連する既存試験を選ぶ。dotfilesの設定生成は`bash etc/test-codex-config.sh`、Codex native同期hookは`uv run --python 3.13 python etc/test-codex-native-sync-hook.py`。後者は同期対象の選別試験であり、履歴禁止の試験ではない。
5. 新規セッションで実効設定・有効backend・実際の起動引数・完了通知を確認する。生成ファイルの存在や一回の成功を全実機経路の保証にしない。ログ取得のためだけの高額な負荷試験は増やさない。

使用量は親子別の有効モデル、ターン数、入力・キャッシュ・出力、待機だけの反復を分けて扱う。キャッシュ入力も総入力に含まれ得るため二重加算せず、forkされた過去イベントや累積カウンタを毎行の追加消費として合算しない。API料金の試算を、そのままProの使用枠へ換算しない。

## 完了報告

報告は「原本・生成物の修正とpush」「対象端末への配布」「実効動作」「runtime未対応」を分ける。履歴継承のネイティブ強制が必要なのに未対応なら、その項目を未達として残す。無関係な変更まで止めないが、全体を無条件にPASS・完了とはしない。既存の報告書を使い、新しい常設の監査台帳は作らない。

## 確認元

- [C1: Codex 0.153.4 設定型](https://github.com/openai/codex/blob/rust-v0.153.4/codex-rs/features/src/feature_configs.rs)
- [C2: Codex 0.153.4 V2 spawn](https://github.com/openai/codex/blob/rust-v0.153.4/codex-rs/core/src/tools/handlers/multi_agents_v2/spawn.rs)
- [C3: Codex 0.153.4 V2 wait](https://github.com/openai/codex/blob/rust-v0.153.4/codex-rs/core/src/tools/handlers/multi_agents_v2/wait.rs)
- [C4: Codex 0.153.4 config](https://github.com/openai/codex/blob/rust-v0.153.4/codex-rs/config/src/config_toml.rs)
- [C5: Codex Configuration Reference](https://developers.openai.com/codex/config-reference)
- [C6: Codex 0.153.4 model overrides](https://github.com/openai/codex/blob/rust-v0.153.4/codex-rs/models-manager/src/model_info.rs)
- [C7: Codex 0.153.4 context activation](https://github.com/openai/codex/blob/rust-v0.153.4/codex-rs/core/src/session/token_budget.rs)
- [C8: Codex 0.153.4 child config](https://github.com/openai/codex/blob/rust-v0.153.4/codex-rs/core/src/tools/handlers/multi_agents_common.rs)
- [C9: Codex 0.153.4 context thresholds](https://github.com/openai/codex/blob/rust-v0.153.4/codex-rs/core/src/session/context_window.rs)
- [X1: Cursor Subagents](https://cursor.com/docs/subagents)

版依存の記述は、移行先の実行版を確かめてから用いる。古い資料の記述だけで、新しい版にも同じ制約があると断定しない。
