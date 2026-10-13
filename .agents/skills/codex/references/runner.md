# Codex app-server runner

実行scriptは [`scripts/codex-run.py`](../scripts/codex-run.py) です。呼び出し元は一意な `RUN_ID` と絶対pathを渡して1回起動し、scriptが出力するJSON要約を受け取ります。modelとeffortは呼び出し元が選び、scriptは形式だけを検証します。

## 入力

`--prompt-file` と `--prompt` のどちらか一方を必ず指定します。

| 引数 | 条件 |
| --- | --- |
| `--prompt-file PATH` または `--prompt TEXT` | 非空の指示本文。既定はmode `0600` のfileを `--prompt-file` で渡し、runnerが保存するprompt artifactもPOSIXではmode `0600` です。POSIXではinput fileのmode `0600` を確認します。`--prompt` は秘密を含まない短い問いに限ります |
| `--cwd PATH` | 必須、既存directoryの絶対path。helperへ渡す前にcanonical化 |
| `--model NAME` | 必須、`[A-Za-z0-9._-]+` |
| `--effort NAME` | 必須、`[a-z]+` |
| `--sandbox read-only` | 任意。省略時はCodexのuser configを使う |
| `--work-dir PATH` | 必須の絶対path。存在しなければ作成 |
| `--run-id ID` | 必須、一意な `[A-Za-z0-9._-]+` |
| `--session-file PATH` | 任意の絶対path。新規sessionではfileと`.meta`の両方が未作成、resumeでは双方が既存 |

`WORK_DIR` と `SESSION_FILE` の親pathは先にcanonicalizeします。canonical path上の各directory componentがsymlinkでないこと、POSIXでは所有者がrootまたは実行中uidでgroup/world writableでないことを確認します。root所有のsticky directory（例: `/tmp`）は共有書込先として許可します。対象directoryは実行中uidが所有し、group/world writableでない必要があります。Windowsではsymlinkとdirectory種別を検査します。既存session fileとmetadataはregular non-symlink fileで、POSIXでは実行中uidが所有しgroup/world writableでないことが条件です。artifact pathとsummaryのpathにはcanonical pathを使います。

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
4. 監督workerが既存の `codex-app-run.py` helperを別process/sessionで起動し、helperが完了するまで待ちます。HelperのJSON-RPC protocolとapproval refusal behaviorはこのrunnerから変更しません。
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
| `codex-<RUN_ID>-done` | wrapper公開完了marker。開始済みjobの完了後に `EXIT=<整数>` の1行 |
| `codex-<RUN_ID>-helper-done` | helper内部の完了marker |
| `codex-<RUN_ID>-state.txt` | helperが記録する開始時刻、観測cwd、要求model/effort/sandbox |
| `codex-<RUN_ID>-pid` | helper process ID |

`SESSION_FILE` を指定すると、新規turnの結果にかかわらず、helper終了後にeventsからthread IDが得られた場合はそのIDを1行で保存し、`${SESSION_FILE}.meta` に `CWD=<canonical path>` と `SANDBOX=<値>` を保存します。保存失敗はhelperが失敗していた場合はその終了値を保持し、helperが成功していた場合はrunner startup error `125` にします。両方を同じdirectoryの一時fileからatomicに公開します。続行では既存の2 fileがregular non-symlink fileであること、session本文がthread IDの1行であること、metadataのCWDとsandboxが一致することを確認します。継続時はsession fileを変更しません。session pathが一部だけ存在する場合やCWD/sandboxが一致しない場合は起動しません。同じ `SESSION_FILE` を使うjobは同時に1つだけです。前のjobの `DONE_FILE` を確認してから続行します。

## JSON要約

stdoutの1行JSONには次を含めます。

- `EXIT` と `thread_id`
- `REQUESTED_MODEL` / `REQUESTED_EFFORT` / `REQUESTED_SANDBOX`
- `OBSERVED_MODEL` / `OBSERVED_EFFORT` / kebab表記の `OBSERVED_SANDBOX` / `OBSERVED_CWD`
- eventsから得られる `usage.total_tokens` / `input_tokens` / `cached_input_tokens` / `output_tokens`
- `final_response.path` と `final_response.body`
- events行数とevents、stderr、state、done、helper-done、PID、promptの各path
- 使用時の `SESSION_FILE` / `SESSION_META`、`wait_status`、`done.created` / `done.exit`、失敗理由（ある場合）

Eventsに独立した根拠がない観測値やtoken usageは `unavailable` です。token usageは対象threadの `thread/tokenUsage/updated` eventにある `params.tokenUsage.total` から取り、`last` やsub-agent threadの値は使いません。継続sessionでの `total` は前turnを含むthread累計です。Requested値をobserved値として報告しません。最終応答が未作成ならbodyはJSON `null`、空の応答fileなら空文字列です。

`wait_status=completed` の場合、jobが開始済みであることを前提に `EXIT` と `done.exit` は有効な現在runの `DONE_FILE` 値に一致し、script process exit codeも同じです。`done.created` は現在runの有効markerを要約時に確認したことを示します。`done.path` はpath情報だけで、既存または後から作られるfileの存在を完了根拠にしません。

入力検証、artifact/session path衝突、Codex CLI不在など起動前の拒否は `wait_status=invocation_error` で、JSON要約を返しDONE markerを作成しません。この場合の `EXIT` はrunnerのinvocation error code、`done.created=false`、`done.exit=null` です。監督workerを起動できない場合は `wait_status=worker_start_failed`、`EXIT=125`、DONEなしです。

10800秒以内にmarkerを確認できない場合は `wait_status=timed_out`、JSONの `EXIT=null`、`done.created=false`、process exit code `124` です。監督workerが有効markerを書かず終了した場合は `wait_status=supervisor_exited_without_done`、`EXIT=null`、`done.created=false`、process exit code `125` です。ローカルの待機処理でI/O errorが起きた場合は `wait_status=wait_error`、`EXIT=null`、process exit code `125` です。これら3状態ではrun完了として受け入れず、timeout時に残ったworker/helperはそのまま実行を続けます。

timeout・親shell終了・runtimeの打ち切りでJSONを得られなかったjobは、そのjobの `CWD` に新しい書込みjob・レビュー・commitを割り当てません。`DONE_FILE` がまだなければこの制限を維持し、継続的なpollはしません。再開時に `DONE_FILE` を確認し、出現後は `DONE_FILE`、最終応答、events、stderr、stateを読んでjobの完了状態を受け入れます。この操作は完了markerの確認であり、jobの継続的なpollではありません。
