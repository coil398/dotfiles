# Codex app-server runner

実行scriptは [`scripts/codex-run.py`](../scripts/codex-run.py) です。呼び出し元は一意な `RUN_ID` と絶対pathを渡して1回起動し、scriptが出力するJSON要約を受け取ります。modelとeffortは呼び出し元が選び、scriptは形式だけを検証します。

## 入力

`--prompt-file` と `--prompt` のどちらか一方を必ず指定します。

| 引数 | 条件 |
| --- | --- |
| `--prompt-file PATH` または `--prompt TEXT` | 非空の指示本文。runnerは先頭に委譲実装者向けの固定前置きを付け、実装・相談とも子を起動しないこと、recallしないこと、自分の変更の確認は完了まで実行すること、親が監視する長時間の処理は起動を確認したら返り監視しないこと、大きなログを必要行に絞ることを指示します。既定はfileを `--prompt-file` で渡し、runnerが保存するprompt artifactはPOSIXではmode `0600` です。`--prompt` は秘密を含まない短い問いに限ります |
| `--cwd PATH` | 必須、既存directoryの絶対path。helperへ渡す前にcanonical化 |
| `--model NAME` | 必須、`[A-Za-z0-9._-]+` |
| `--effort NAME` | 必須、`[a-z]+` |
| `--sandbox read-only` | 任意。省略時はCodexのuser configを使う |
| `--work-dir PATH` | 必須の絶対path。存在しなければ作成 |
| `--run-id ID` | 必須、一意な `[A-Za-z0-9._-]+` |
| `--session-file PATH` | 任意の絶対path。同じ `SESSION_FILE` は前の文脈が必要な同一jobの継続にだけ使います。無関係な別依頼は新しいthreadで開始します。新規sessionではfileと`.meta`の両方が未作成、resumeでは双方が既存 |

runner経由のCodexは `--disable multi_agent` で起動するため、子を起動できません。

`WORK_DIR` と `SESSION_FILE` の親pathは先にcanonicalizeします。存在する各componentがdirectoryであることを確認し、対象directoryはmode `0700` で作成します。既存session fileとmetadataはregular non-symlink fileである必要があります。artifact pathとsummaryのpathにはcanonical pathを使います。

例:

```bash
python3 /absolute/path/.agents/skills/codex/scripts/codex-run.py \
  --prompt-file /absolute/path/prompt.md \
  --cwd /absolute/path/repository \
  --model gpt-6-luna \
  --effort medium \
  --sandbox read-only \
  --work-dir /absolute/path/codex-jobs \
  --run-id review-001
```

`WORK_DIR` はrunnerが作成します。`RUN_ID` は並列実行や再実行で再利用しません。prompt、CWD、sandbox、scope、model、effortをscriptが変更することはありません。

## 起動と完了

1. Scriptは入力を検証し、CWDをcanonical化します。Codexは `~/AppData/Roaming/npm/codex.cmd` がfileとして存在する場合に優先し、それ以外は `shutil.which("codex")` を使います。後者の結果が相対pathまたは現在の作業directory配下なら拒否します。
2. `WORK_DIR` 内の同じ `RUN_ID` の成果物が1つでもあれば起動を拒否します。`SESSION_FILE` と `${SESSION_FILE}.meta` を全canonical run artifactと照合し、一致する場合も起動前に拒否します。既存fileやsymlinkを上書き・削除しません。
3. Promptとstderrのfileをexclusive作成し、同じscriptの監督workerを親shellから切り離して起動します。POSIXでは新しいsession、Windowsではdetached process groupを使います。
4. 監督workerが既存の `codex-app-run.py` helperを別process/sessionで起動し、helperが完了するまで待ちます。Helperは `CODEX_DELEGATED_BY_RUNNER=1` と `JEV_HOOKS_MODE=off` を Codex app-server processへ渡し、`codex app-server --disable multi_agent --disable multi_agent_v2` で起動してrunner経由のCodexから子の起動toolを外します（ユーザーが直接起動するCodexの `~/.codex/config.toml` は変えません）。Codexはrunnerの委譲実装者として動作し、子を起動しません。通常の子process環境継承により hook command にも `JEV_HOOKS_MODE=off` が渡ります。HelperのJSON-RPC protocolとapproval refusal behaviorはこのrunnerから変更しません。
5. Helperが終了した後に監督workerが `codex-<RUN_ID>-done` をexclusive作成し、1行の `EXIT=<整数>` を記録します。Helper内部のmarkerは別pathです。公開markerが有効な場合だけ、その整数を現在runの完了値として扱います。
6. 親scriptは最大10800秒までblockingでmarkerを待ちます。marker後はevents・state・stderr・最終応答を読み、stdoutへJSONを1行出力します。supervisorがmarkerなしで終了した場合と待機期限に達した場合は、Codex/helperをkill・restartせず、未完了statusを返します。

Scriptはblockingです。親shellがscriptを終了しても切り離した監督workerとhelperは継続し、helper終了後にworkerが公開 `DONE_FILE` を書きます。待機期限の後も実行中のworker/helperは継続し、後で公開markerを書くことがあります。Scriptに自動retry、model/effort変更、privilege escalation、approval bypass、外部送信はありません。

## 成果物

すべて `WORK_DIR` 直下で、fileを新規作成します。新しい `RUN_ID` ごとに分離します。

| File | 内容 |
| --- | --- |
| `codex-<RUN_ID>-prompt.md` | helperへ渡したprompt本文 |
| `codex-<RUN_ID>-last.md` | app-serverが返した最終応答本文 |
| `codex-<RUN_ID>-events.jsonl` | helperが保存したapp-server events |
| `codex-<RUN_ID>-err.txt` | helperと監督workerのstderr |
| `codex-<RUN_ID>-run.log` | INFO相当の固定eventと`key=value`で記録する実行中tail用ログ。作成・追記できない場合は補助artifactとして欠損をstderrとsummaryに記録し、他の必須artifactを作成できれば実行を続ける |
| `codex-<RUN_ID>-done` | wrapper公開完了marker。開始済みjobの完了後に `EXIT=<整数>` の1行 |
| `codex-<RUN_ID>-helper-done` | helper内部の完了marker |
| `codex-<RUN_ID>-state.txt` | helperが記録する開始・終了時刻、elapsed、要求値とsource、thread既定値、turn実測値とsource・取得理由、要求値との一致状態、rollout探索path/pattern、turn状態、件数、signal、token snapshot、run.logの利用可否 |
| `codex-<RUN_ID>-pid` | helper process ID |

`SESSION_FILE` を指定すると、新規turnの結果にかかわらず、helper終了後にeventsからthread IDが得られた場合はそのIDを1行で保存し、`${SESSION_FILE}.meta` に `CWD=<canonical path>` と `SANDBOX=<値>` を保存します。保存失敗はhelperが失敗していた場合はその終了値を保持し、helperが成功していた場合はrunner startup error `125` にします。両方を同じdirectoryの一時fileからatomicに公開します。続行では既存の2 fileがregular non-symlink fileであること、session本文がthread IDの1行であること、metadataのCWDとsandboxが一致することを確認します。継続時はsession fileを変更しません。session pathが一部だけ存在する場合やCWD/sandboxが一致しない場合は起動しません。同じ `SESSION_FILE` を使うjobは同時に1つだけです。前のjobの `DONE_FILE` を確認してから続行します。前の文脈を引き継がない別依頼には別の `SESSION_FILE` を使うか、session継続を指定しません。

## JSON要約

stdoutの1行JSONには次を含めます。

- `EXIT` と `thread_id`
- `REQUESTED_MODEL` / `REQUESTED_EFFORT` / `REQUESTED_SANDBOX`
- `REQUESTED_MODEL_SOURCE` / `REQUESTED_EFFORT_SOURCE` / `REQUESTED_SANDBOX_SOURCE`
- `OBSERVED_MODEL` / `OBSERVED_EFFORT` と各`_SOURCE` / `_REASON` / kebab表記の `OBSERVED_SANDBOX` / `OBSERVED_CWD`
- `THREAD_DEFAULT_MODEL` / `THREAD_DEFAULT_EFFORT` と各source/reason。thread start/resume responseにある既定値として、実際のturn値とは分けて扱う
- `MODEL_MATCH_STATUS` / `EFFORT_MATCH_STATUS`。requested値とobserved値を比較し、`match` / `mismatch` / `unavailable` で示す。`warnings`には不一致の項目を含める
- `run`。timezone付き開始・終了時刻、elapsed、最後の短いagent message要約、turn状態、commandExecution数と失敗数、heartbeat数、現在token snapshot、受信signalとsender PIDの可用性、rollout探索根拠
- `activity`。runner thread eventsから数えた子起動数とsleep数、rolloutの重複排除済み `token_usage_record` 数、各recordの `usage.input_tokens` の平均と有効sample数。usage recordが得られない値は `unavailable` とし、子・sleep件数はrunner threadの範囲です。子の起動が1以上、またはsleepが3回以上のとき `warnings` に `child_launch` / `sleep` を加えます（runは止めません）
- `log.path`、`log.available`、`log.reason`。実行中にtailできる専用run log artifactの状態
- eventsから得られる `usage.total_tokens` / `input_tokens` / `cached_input_tokens` / `output_tokens`
- `final_response.path` と `final_response.body`
- events行数とevents、stderr、state、done、helper-done、PID、promptの各path
- 使用時の `SESSION_FILE` / `SESSION_META`、`wait_status`、`done.created` / `done.exit`、失敗理由（ある場合）

`OBSERVED_MODEL` と `OBSERVED_EFFORT` は対象thread・turnのCodex rollout `turn_context.payload.model` / `effort` を優先します。探索rootは環境の `CODEX_HOME`、app-server `initialize` responseの `codexHome`、既定の `~/.codex` の順で選びます。同threadのrollout file内で `payload.turn_id` が対象turn IDに一致し、event timestampがrunner開始時刻以降のcontextだけを実測に採用します。選んだroot、`sessions` 探索path、filename pattern、thread/turn ID、開始時刻、context件数、採用時刻/path、探索理由をstateとrun logに残します。turn IDを取得した直後に探索し、未取得なら0.5秒から間隔を段階的に広げて最大10秒ごとに再照合します。contextを採用した後は完了時の最終照合まで再走査しません。これらの観測値はturn完了前にもstateとrun logへ追記するため、timeout summaryはその時点の最新値を示します。Rollout値がなくてもapp-serverのturn start responseまたは同threadの `turn/started` / `turn/completed` notificationにturn固有model/effortがあれば使います。複数notificationが異なる値を返す場合は、turn/completed、turn/started、turn/start responseの順に優先します。どちらも得られなければ `unavailable` とreasonおよび探索path/patternを記録します。thread start/resume responseの `model` / `reasoningEffort` は `THREAD_DEFAULT_*` にだけ記録し、turn実測値として扱いません。要求値sourceはrunnerのCLI引数、既定値sourceはthread start/resume response、実測値sourceは採用したrollout fieldまたはturn固有response fieldです。

run.logの作成または追記に失敗した場合、runner/helperは失敗理由を `STDERR_FILE` とsummaryへ記録します。summaryの `log.available` は `false`、`log.reason` は観測した失敗理由です。他の必須artifactを作成できれば、run.logの失敗だけではapp-server起動、turn実行、summary出力を止めません。

`OBSERVED_SANDBOX` はevents内のapp-server responseから得ます。token usageは対象threadの `thread/tokenUsage/updated` eventにある `params.tokenUsage.total` から取り、`last` やsub-agent threadの値は使いません。継続sessionでの `total` は前turnを含むthread累計です。`run.current_tokens` と定期heartbeatはhelperが観測した同threadの最新total snapshotです。Requested値をobserved値として報告しません。rolloutやturn responseに独立した根拠がないmodel/effortは `unavailable` です。最終応答が未作成ならbodyはJSON `null`、空の応答fileなら空文字列です。

`run.log` はprompt、agent本文全体、command引数・出力を記録しません。受信したagent messageはcapture時にcontrol/newlineを除去し、credential形式に見える値を伏せて短く要約します。同じ要約の再送は重複記録しません。commandExecutionは開始eventで数え、完了後に失敗数を更新します。安全な個別command表示は記録しません。signal sender PIDはPython signal handlerから取得できない環境では `unavailable` と理由を記録します。

`wait_status=completed` の場合、jobが開始済みであることを前提に `EXIT` と `done.exit` は有効な現在runの `DONE_FILE` 値に一致し、script process exit codeも同じです。`done.created` は現在runの有効markerを要約時に確認したことを示します。`done.path` はpath情報だけで、既存または後から作られるfileの存在を完了根拠にしません。

入力検証、artifact/session path衝突、Codex CLI不在など起動前の拒否は `wait_status=invocation_error` で、JSON要約を返しDONE markerを作成しません。この場合の `EXIT` はrunnerのinvocation error code、`done.created=false`、`done.exit=null` です。監督workerを起動できない場合は `wait_status=worker_start_failed`、`EXIT=125`、DONEなしです。

10800秒以内にmarkerを確認できない場合は `wait_status=timed_out`、JSONの `EXIT=null`、`done.created=false`、process exit code `124` です。監督workerが有効markerを書かず終了した場合は `wait_status=supervisor_exited_without_done`、`EXIT=null`、`done.created=false`、process exit code `125` です。ローカルの待機処理でI/O errorが起きた場合は `wait_status=wait_error`、`EXIT=null`、`done.created=false`、process exit code `125` です。これらの状態をrunの成功完了として受け入れず、timeout時に残ったworker/helperはrunnerが自動停止・再起動せず実行を続けます。

timeout・親shell終了・runtimeの打ち切りでJSONを得られなかったjobは未終了として扱います。`supervisor_exited_without_done`、および`DONE_FILE`が出ないままの`wait_error`またはtimeoutも未終了です。未終了jobのprocessが生きている間は、その`CWD`に新しい書込みjob・レビュー・commitを割り当てず、同じ`SESSION_FILE`で継続しません。継続的なpollやrunnerによる自動kill・restartは行いません。

再開時は`DONE_FILE`を確認します。`wait_error`でもtimeoutでも、後から有効な現在runの`DONE_FILE`が出現していれば、`DONE_FILE`・最終応答・events・stderr・stateを読み、通常どおり完了状態を受け入れます。DONEの無いjobは、`codex-<RUN_ID>-pid` のhelperと監督workerのprocessが残っているかを確かめます。残っていれば未終了として扱います。processが残っていないと確かめられたら、DONEなしで終了したjobとして扱い、結果を成功とはみなさず、先行diffと成果物を確認してから新しい`RUN_ID`での再委譲・レビュー・commitへ進めます。processの状態を確かめられない場合だけ、ユーザーへblockerとして報告します（`RUN_ID`、`codex-<RUN_ID>-pid`、helperのcommand line、観測したprocess一覧を添える）。
