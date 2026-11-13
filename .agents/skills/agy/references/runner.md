# agy ACP runner

実行scriptは [`scripts/agy-run.py`](../scripts/agy-run.py) です。ACP clientは [`scripts/agy-acp-run.py`](../scripts/agy-acp-run.py) で、runnerの監督workerだけが起動します。呼び出し元は一意な `RUN_ID` と絶対pathを渡して1回起動し、stdoutの1行JSON要約を受け取ります。modelとmodeは呼び出し元が選び、runnerは形式だけを検証します。

## 入力

| 引数 | 条件 |
| --- | --- |
| `--prompt-file PATH` または `--prompt TEXT` | どちらか一方。非空。既定は絶対pathのfile。runnerは先頭に委譲実行者向けの固定前置き（別AI CLI・サブエージェント・多agent機能・`agy` Skillを使わない、recallしない、commit・push・外部送信をしない、plan modeでは編集しない、自分の確認は完了まで実行する、親が監視する長時間の処理は起動を確認したら返り監視しない、大きなログは必要行に絞る）を付けて保存する |
| `--cwd PATH` | 必須。既存directoryの絶対path。canonical化し、`agy acp` のprocess cwdと `session/new`・`session/load` の `cwd` の両方に渡す |
| `--model ID` | 必須。`agy models` にある完全なmodel id（例 `gemini-4-hydrogen-xhigh`）。`[A-Za-z0-9._-]+` |
| `--mode {plan,auto}` | 必須。相談は `plan`、実装は `auto` |
| `--work-dir PATH` | 必須の絶対path。無ければmode `0700` で作成 |
| `--run-id ID` | 必須。一意な `[A-Za-z0-9._-]+` |
| `--session-file PATH` | 任意の絶対path。前の文脈が必要な同一jobの継続にだけ使う。新規はfileと `.meta` の両方が未作成、継続は両方が既存のregular non-symlink file。親directoryが無ければ起動前にmode `0700` で作成する |

例:

```bash
python3 /absolute/path/.agents/skills/agy/scripts/agy-run.py \
  --prompt-file /absolute/path/prompt.md \
  --cwd /absolute/path/repository \
  --model gemini-4-carbon-high \
  --mode plan \
  --work-dir /absolute/path/agy-jobs \
  --run-id consult-001
```

## 起動と完了

1. 引数を検証する。引数の誤りも `wait_status=invocation_error` の1行JSONで返す。同じ `RUN_ID` の成果物が1つでもあれば起動を拒否する。`SESSION_FILE` と `.meta` が成果物pathと衝突する場合、片方だけ存在する場合、`.meta` の `CWD` / `MODE` が今回の値と一致しない場合も拒否する。
2. `agy` を `shutil.which("agy")` で解決する。相対path、またはrunnerのcurrent directory配下に解決された場合は拒否する。
3. prompt・stderr・run.logをexclusive作成し、監督workerを新しいsessionで親shellから切り離して起動する。
4. workerがhelperを起動し、helperのPIDを `agy-<RUN_ID>-pid` に、worker自身のPIDを run.log の `event=worker_start pid=` に記録する。helper PIDを記録できない場合はhelperを停止してから終了する。helperは `DOTFILES_AUTOSYNC_SKIP=1`、`JEV_HOOKS_MODE=off` を付けて `agy acp` を起動し、実行中は `${XDG_STATE_HOME:-$HOME/.local/state}/dotfiles-autosync/holds/` に自分のPIDを記録したhold fileを保持する。
5. helperは `initialize` → `session/new`（継続時は `session/load`）→ `session/set_model` → `session/set_mode` → `session/prompt` を送る。準備段階の各requestは120秒で打ち切り、`session/prompt` には期限を設けない。
6. helper終了後、新規sessionで `SESSION_FILE` が指定されていれば、workerがsession idと `.meta`（`CWD=` と `MODE=`）を一時fileからhard linkで公開する。既存fileは置き換えず、片方だけ公開できた場合はそれを取り除く。保存に失敗し、helperが成功していた場合はEXITを125にする。
7. workerが公開marker `agy-<RUN_ID>-done` に `EXIT=<整数>` の1行をexclusive作成する。捕捉できないsignal（SIGKILL等）で終了したhelperは `128+signal番号` を記録する。
8. 親scriptは最大10800秒、markerを待つ。待機中にworkerがmarkerなしで終了した場合と期限に達した場合は、agyをkill・restartせずに未完了statusを返す。

helperはSIGTERM・SIGINT・SIGHUPを受けると `agy acp` を停止し、stateとhelper-doneを書き、hold fileを除去してから終了する（EXIT 4）。runnerに自動retry、model・mode変更、権限昇格、外部送信はありません。

## permission と mode

- helperは `session/request_permission` に `reject_once` のoptionを返し（無ければ `cancelled`）、tool名とkindを記録する。agent→clientの他のrequestにはJSON-RPC error `-32601` を返す。
- `plan` はagyが計画を先に立てる読み取り中心のmodeで、OS sandboxではない。編集を指示されてもworkspaceは編集せず、計画書をagyのbrain directory（`~/.gemini/antigravity-cli/brain/`）へ書く。この挙動はagy側の動作であってrunnerやOSが強制するものではないため、親は相談jobの前後で `git status` を照合する。
- `auto` は、agyのtrusted workspace（`~/.gemini/antigravity-cli/settings.json` の `trustedWorkspaces`）内ならファイル編集と安全と判定したcommandを承認なしに実行する。untrusted workspaceではファイル読取りにもpermission requestが来て拒否されるため、`permission_rejected` 警告とともに作業が進まずに終わる。`plan` ではuntrusted workspaceでもファイルを読んで回答できるが、commandの実行にはpermission requestが来て拒否される。

## helper の EXIT

| EXIT | 意味 |
| --- | --- |
| `0` | `session/prompt` が `stopReason=end_turn` で終了した。permission拒否や空応答もここに含まれ、`warnings` で示す |
| `3` | `end_turn` 以外のstopReason（`refusal`、`cancelled`、`max_tokens` 等） |
| `4` | JSON-RPC error、object以外のresult、準備requestのtimeout、agyの異常終了、session idの欠落、helperへのsignal |
| `125` | helperを起動できない、または新規sessionの保存に失敗した |

## 成果物

すべて `WORK_DIR` 直下に新規作成し、既存fileを上書き・削除しません。file modeは `0600` です。

| File | 内容 |
| --- | --- |
| `agy-<RUN_ID>-prompt.md` | 前置きを付けてagyへ送ったprompt |
| `agy-<RUN_ID>-last.md` | 今回の `session/prompt` 送信後に受け取った `agent_message_chunk` の連結。`session/load` で再送される過去の履歴は含めない |
| `agy-<RUN_ID>-events.jsonl` | `agy acp` から受信した全行 |
| `agy-<RUN_ID>-err.txt` | agy・helper・workerのstderr |
| `agy-<RUN_ID>-run.log` | 固定event名と `key=value` の実行ログ。prompt・応答本文・command引数は記録しない |
| `agy-<RUN_ID>-state.txt` | helperが追記する `key=value`。同じkeyは後の行が優先 |
| `agy-<RUN_ID>-done` | 公開完了marker |
| `agy-<RUN_ID>-helper-done` | helper内部の完了marker |
| `agy-<RUN_ID>-pid` | helperのPID |

## JSON要約

stdoutの1行JSONには次を含めます。

- `EXIT`、`session_id`、`stop_reason`、`usage`（`session/prompt` resultの値）
- `REQUESTED_MODEL` / `REQUESTED_MODE`
- `OBSERVED_MODEL` / `OBSERVED_THOUGHT_LEVEL` / `OBSERVED_MODE`。`session/update` の `config_option_update` で最後に受け取った値で、得られなければ `unavailable`。requested値をobserved値として報告しない
- `MODEL_MATCH_STATUS` / `MODE_MATCH_STATUS`（`match` / `mismatch` / `unavailable`）。modelはrequested idが `<model>-<thought_level>` または `<model>` と一致すれば `match`
- `run`。開始・終了時刻、elapsed、agyのversion、tool call数と失敗数、permission拒否の件数と一覧、未対応request、agyの終了値、helperの失敗理由
- `final_response.path` / `body`（未作成なら `null`）
- `warnings`。`permission_rejected`、`empty_final_response`、`model_mismatch`、`mode_mismatch`
- `wait_status`、`done.path` / `created` / `exit`、`log.path` / `available`、`artifacts`
- 使用時の `SESSION_FILE` / `SESSION_META`、起動前拒否などの `error`

## 終了契約

| `wait_status` | JSONの `EXIT` | process exit code | DONE |
| --- | --- | --- | --- |
| `completed` | DONEの値 | DONEの値 | あり |
| `invocation_error` | `2`（入力・衝突）または `5`（agy不在） | 同じ | なし |
| `worker_start_failed` | `125` | `125` | なし |
| `timed_out` | `null` | `124` | なし |
| `supervisor_exited_without_done` / `wait_error` | `null` | `125` | なし |

開始済みjobは `wait_status=completed`、`done.created=true`、`EXIT` と `done.exit` の一致を確認してから受け入れます。`timed_out`・`supervisor_exited_without_done`・`wait_error`、およびJSONを得られなかったjobは未終了として扱い、processが生きている間はその `CWD` に新しい書込みjob・レビュー・commitを割り当てず、同じ `SESSION_FILE` で継続しません。再開時は `DONE_FILE` を確認し、後から有効なmarkerが出ていれば通常の完了として読みます。markerが無く、`agy-<RUN_ID>-pid` のhelperと run.log の `worker_start pid=` のworkerが残っていなければ、DONEなしで終了したjobとして先行diffと成果物を確認してから新しい `RUN_ID` で進めます。
