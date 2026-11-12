# harness別の仕様

`scripts/harness-run.py` が各harnessへ渡す引数、認証、model指定、read-only、usageの定義を示す。版は pi 1.5.2、omp 18.18.8、opencode 1.18.21、dsh 0.2.2-rc.1。「実測」は実機で確認した値、「未確認」は実行していない項目。

## 共通

- すべて子processのenvから `OPENAI_API_KEY` を外す。provider `openai` は `pi`/`omp`/`dsh` で拒否する（従量課金の経路）。
- effortは `low|medium|high|xhigh|max`。
- usageは正規化して返す: `input_uncached`（cacheを含まない）、`cache_read`、`cache_write`、`output`（reasoning込み）、`reasoning`（取れる場合のみ。outputの内訳）、`total_input`（3種の合計）、`requests`。Codex runnerの `input` はcache込みなので、比較するときは `total_input` を使う。
- 各harnessの `cost` は推定値かsubscriptionの実課金と無関係な値なので返さない。

## Pi（`pi`）

| 項目 | 内容 |
|---|---|
| argv | `pi --provider <p> --model <id> --thinking <e> --session-dir <work>/harness-<ID>-sessions --tools <list> --mode json [-nc -ns --no-mcp -ne -na] @<prompt> "Follow the attached task file."`（cwdで起動、stdinは `/dev/null`） |
| model | `openai-codex/<id>`。`--model` だけでproviderを省くと従量課金の `openai` に解決されうるため、runnerは必ず `--provider` を付ける。実測で動作したのは `gpt-6-luna` |
| 認証 | `pi auth login openai-codex --no-browser`。確認は `pi auth check --provider <p> --json`（exit 0=ready、1=not_ready、2=invalid） |
| read-only | `--tools read,grep,find,ls`（実測: bash/writeはtool定義に無く、呼ぶと `Tool ... not found`）。書込みあり: `read,bash,edit,write,grep,find,ls` |
| 失敗判定 | json modeは応答の失敗でもexit 0になる。最後のassistant `message_end` の `stopReason == stop` で成功判定する |
| usage | assistantの `message_end.message.usage` を合計（`input` はcache除外）。`message_update` のusageは0のまま |
| 限界 | OS sandboxなし。cwd外の読取は防げない。`--minimal-context` なしだとcwd祖先のAGENTS.md等を読む |

## Oh my Pi（`omp`）

| 項目 | 内容 |
|---|---|
| argv | `omp -p --mode json --no-session --model <p/id> --thinking <e> --no-title --no-lsp --tools <list> --cwd <cwd> [--no-skills --no-rules --no-context-files --no-extensions --config <overlay>] @<prompt>`（stdinは `/dev/null`。閉じないと起動で止まる） |
| overlay | `disabledProviders: [claude, claude-plugins, codex, cursor, gemini, opencode, windsurf, github]`。Claude plugin由来のMCP接続を止める（`--minimal-context` のみ） |
| model | `openai-codex/<id>`。`gpt-6-luna`、`gpt-6-astra`、`gpt-6.1-sol` は解決を確認（実測、ログイン前）。`gpt-6.1-terra` は同梱catalogに無い |
| 認証 | `omp login openai-codex`（Piとは別のauth store。Piのtokenは流用しない）。確認は `omp token <p>` のexit code（0=登録あり。出力は捨てる） |
| read-only | `--tools read,grep,glob,find`（実測、fake serverで送信toolsを確認）。書込みあり: `read,bash,edit,write,grep,glob,find` |
| usage | assistantの `message_end.message.usage`。`input` はcache除外。`reasoningTokens` はoutputの内訳 |
| 注意 | Codexサブスクでの生成は `gpt-6-luna`・`gpt-6.1-sol` で実測。`--minimal-context` なしでは1回の実行で補助LLMリクエストが100件超出る（fake serverで実測）ため、通常は `--minimal-context` を付ける |

## OpenCode（`opencode`）

| 項目 | 内容 |
|---|---|
| argv | `opencode run --pure --dir <cwd> --title harness-<ID> --agent <ro\|build> -m <p/id> --variant <e> --format json`、promptはstdin。envに `OPENCODE_DISABLE_AUTOUPDATE=1`、`OPENCODE_DISABLE_SHARE=1` |
| `--minimal-context` | `OPENCODE_DISABLE_PROJECT_CONFIG`、`OPENCODE_DISABLE_CLAUDE_CODE`、`OPENCODE_DISABLE_EXTERNAL_SKILLS` を1にし、`XDG_CONFIG_HOME` を作業dir配下へ向ける（global config・plugin・agent・MCPを読まない） |
| model | OAuth時の `openai/` 一覧は `gpt-6.1-sol`、`gpt-6.1-terra`、`gpt-5.6-*` など。`gpt-6-luna`/`gpt-6-astra` は組込みcatalogに無く、そのままでは `ProviderModelNotFoundError` になる。runnerはこの2つの場合に、`provider.openai.models` へ宣言した一時config（`OPENCODE_CONFIG`、作業dir配下）を渡す。この経路でChatGPT OAuthのまま両modelの呼出しを実測（`OPENAI_API_KEY` なし、各1回 `Reply with exactly: OK` が `OK`）。user configは変更しない |
| 認証 | `opencode providers login`。起動前に有効性を確認する手段がなく、失効（`Token refresh failed`、401、`authentication_error`、`api_key_expired`）は `auth_not_ready` にする。provider `openai` はauth.jsonの `openai.type` が `oauth` でなければ起動前に拒否する（API keyだと従量課金になる。値は読まない）。dataは既定のXDG_DATA_HOME（sessionがそこへ書かれる） |
| read-only | `OPENCODE_CONFIG_CONTENT` で `*` をdenyし read/grep/glob/list だけallowするagent `harness-ro-<ID>` を渡し（readは `*.env`・`*.env.*` をdeny、`*.env.example` はallow）、`XDG_CONFIG_HOME` を隔離し `OPENCODE_DISABLE_PROJECT_CONFIG=1` を設定する（project configがpermissionを再定義してbash/editを戻せるため）。bashのパターンallowlistはredirectで迂回できるため使わない。`--agent plan` はread-onlyではない |
| usage | `step_finish` の `part.tokens`（stepごとの差分。`input` はcache除外）。`output` と `reasoning` は別計上なので、runnerは `output = output + reasoning` に正規化する |
| 注意 | stdinを閉じたpipeのままにすると止まる（runnerはprompt fileを渡す）。`--variant` は未実測 |

## DeepSeek Harness（`dsh`）

| 項目 | 内容 |
|---|---|
| argv | `npx -y @deepseek-ai/dsh --profile headless --patch <routes> --patch <model overlay> --permission-mode <read-only\|workspace-write> --approval-policy never [--add-dir <git common dir>] --json -`、promptはstdin |
| model・effort | CLIフラグがないため、runnerが `agent-default-model` のoverlay（`provider`、`model`、`reasoningEffort`）を作業dirへ書き `--patch` で渡す。DeepSeek modelのeffortは `low→low, medium→high, high→high, xhigh→max, max→max` に写す。`--dsh-patch` が当該modelの `reasoningEfforts` を宣言している場合は、写した値以下で宣言された最大のlevelへ丸める（例: `ollama-cloud` は low/high のみなので xhigh・max は high）。結果は `effort_applied` に記録する |
| 認証 | 通常のrouteは `apiKeyEnv` の環境変数を使い、起動前の有無確認はしない。`openai-codex` は `credentials` pluginを有効化し、`llm-pi-ai` routeを登録して既定の `~/.dsh` にあるサインインを使う。`OPENAI_API_KEY` は子processへ渡さない。`MISSING_CREDENTIAL`/`AUTH`/401応答を `auth_not_ready` にする |
| 隔離 | `openai-codex` 以外は `DSH_HOME` を作業dir配下（session保存先）に設定する。全routeで `DSH_TELEMETRY_MODE=DISABLED` を設定する。`--minimal-context` は `DSH_AGENTS_HOME` も隔離する。user profile（`~/.dsh/profiles`）は変更しない |
| read-only | `--permission-mode read-only --approval-policy never`（sandboxで強制。受理は実測、書込み拒否の動作は未確認） |
| usage | `status` イベントの `phase=step_end` の `usage`（`inputTokens` はcache除外、outputはreasoning込み）。usageを報告しないstepは数えない |
| 成功判定 | exit 0 かつ `final.reason.kind == completed`。`final` 後もprocessが終了しない場合、10秒後にprocess groupを停止し、`final` の内容で判定する |
| 実測 | `opencode-go`、`ollama-cloud`、`commandcode`（GOATプランのkey、model id `deepseek/deepseek-v4.1-flash`）の各routeで `deepseek-v4.1-flash` の完走とusageを確認 |
| キーの供給 | キーをzshの対話起動時だけ読み込む環境では、非対話のBashから起動すると環境変数が無く `auth_not_ready` になる。その場合は `zsh -ic '<runner command>'` で起動し、runnerへ環境変数として渡す |

### providerの指定

`--model <route>/<model id>` の `<route>` が `llm-pi-ai` のroute名になる。`opencode-go` は `--dsh-patch` なしでrunnerが `OPENCODE_GO_API_KEY` のrouteを生成する。それ以外は [assets/dsh/](../assets/dsh/) の例を `--dsh-patch` で渡す。

| route | model id | patch | 環境変数 |
|---|---|---|---|
| `opencode-go` | `deepseek-v4.1-flash` | 不要（`assets/dsh/opencode-go.yml` は例） | `OPENCODE_GO_API_KEY` |
| `ollama-cloud` | `deepseek-v4.1-flash` | `assets/dsh/ollama-cloud.yml` | `OLLAMA_API_KEY` |
| `commandcode` | `deepseek/deepseek-v4.1-flash` | `assets/dsh/commandcode.yml` | `COMMANDCODE_API_KEY` |
| `openai-codex` | `openai-codex/<id>` | 自動生成 | dshのcredentials pluginと `llm-pi-ai` routeを有効にし、既定の `~/.dsh` にあるサインインを使う |

patchの `config` は行単位で丸ごと置換される。

## process管理

- runnerは子harnessを別のprocess group（`start_new_session`）で起動し、`--timeout` で `SIGTERM`、10秒後に `SIGKILL` をgroupへ送る。timeoutのlogはkill前に書く。
- runnerがSIGTERM/SIGINT/SIGHUPを受けたときも子のgroupを止める。Linuxでは子に `PR_SET_PDEATHSIG=SIGKILL` を設定し、runnerがSIGKILLされても直接の子は止まる。SIGTERMを無視する孫processはSIGKILLされたrunnerの後に残りうるため、外から止める側はSIGTERMを先に送る（benchはそうする）。
- dshは `final` event後に10秒以内に終了しない場合、runnerがprocess groupを停止する。runの結果は `final` eventで判定する。
- `--timeout` はharness起動後の待機に適用する。起動前の認証確認（`pi auth check`/`omp token`、各60秒）はその外。
- 実測した遅延: システム全体のメモリ枯渇（swap満杯、OOM kill）中は、runnerの待機と子harnessのどちらも止まり、timeoutが設定より遅れて発火する。bench中にこの状態になると試行が外側timeoutに達しうる。
