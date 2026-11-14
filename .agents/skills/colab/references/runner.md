# colab-job runner

実行 script は [`scripts/colab-job.py`](../scripts/colab-job.py) です。1 回の起動で 1 つの job を Google Colab VM で実行し、成果物を回収して VM を必ず解放し、標準出力に 1 行の JSON 要約を出します。Python 3 標準ライブラリのみで動作します。

## 入力

| 引数 | 条件 |
|---|---|
| `--job-dir ABS` | 必須。既存ディレクトリの絶対パス。`.git`、`__pycache__`、`.venv`、`node_modules` を除いて `tar.gz` に固める |
| `--entry REL` | 必須。`--job-dir` 内の `.py` ファイルへの相対パス。`--job-dir` 外を指すパスや symlink（途中のディレクトリを含む）は拒否する |
| `--arg VALUE` | 任意（複数回指定可）。`--entry` の `sys.argv` に指定順で渡す |
| `--requirements REL` | 任意。`--job-dir` 内の requirements ファイルへの相対パス。VM 上で `python -m pip install -r` を実行する |
| `--gpu {T4,L4,G4,H100,A100}` / `--tpu {v5e1,v6e1}` | 任意（排他）。どちらも指定しない場合は CPU になる |
| `--high-mem` | 任意。高メモリ VM を要求する |
| `--max-minutes N` | 必須。1〜1440 の整数。VM 上での `--entry` 実行時間の上限（分） |
| `--work-dir ABS` | 必須。成果物とログを保存するディレクトリの絶対パス。無ければ mode `0700` で作成する |
| `--run-id ID` | 必須。一意な `[A-Za-z0-9._-]+`。`--work-dir` 内に同一 `RUN_ID` の成果物が 1 つでもあれば拒否する |

実行例:

```bash
python3 /absolute/path/.agents/skills/colab/scripts/colab-job.py \
  --job-dir /absolute/path/my-job \
  --entry train.py \
  --arg --epochs --arg 10 \
  --requirements requirements.txt \
  --gpu T4 \
  --max-minutes 30 \
  --work-dir /absolute/path/colab-runs \
  --run-id train-001
```

## 処理順

1. 引数、`--job-dir` 内のパス境界（`--entry`・`--requirements`）、`--work-dir` 内の `RUN_ID` 衝突、および `shutil.which("colab")` を検証する。
2. `colab-<RUN_ID>-run.log` を排他作成（mode `0600`）し、`--job-dir` を `colab-<RUN_ID>-job.tgz` に固め、`colab usage` で実行前残高を取得する。
3. セッション名 `cj-<正規化したRUN_ID>` と状態ファイル `colab-<RUN_ID>-sessions.json` を用いて `colab new` を実行する。以降は `try/finally` で必ず解放処理を行う。`SIGTERM` / `SIGINT` / `SIGHUP` は例外として捕捉し、`finally` を通過させてから終了する。
4. `colab upload` で `job.tgz` を VM の `/content/_runner_job.tgz` へ送る（upload 先のdirは既存である必要があるため `/content` 直下に置く）。
5. 生成した `colab-<RUN_ID>-bootstrap.py` を `colab exec -f ... --timeout 0` で実行する。ローカル側 subprocess にも `max-minutes * 60 + 900` 秒の上限を掛ける。出力は `colab-<RUN_ID>-stdout.log` へ保存する。bootstrap は `/content/job` への安全な展開、必要時の `pip install`、`COLAB_JOB_OUT=/content/out` 付きでの `--entry` 実行（`--max-minutes` 超過時はプロセスグループを停止）、`/content/_runner/status.json` と `/content/_runner/out.tgz` の作成を行う。
6. `colab download` で `status.json` と `out.tgz` を回収し、`out.tgz` を `WORK_DIR/colab-<RUN_ID>-out/` に安全に展開する（絶対パス、`..`、symlink/hardlink、device 等を拒否）。
7. `finally` で `colab stop` と `colab sessions`（session 名が残っていないか `stop_verified` を記録）を実行し、`colab usage` で実行後残高を再取得する。
8. 要約を `colab-<RUN_ID>-summary.json` へ書き、同じ 1 行 JSON を標準出力に出す。

自動 retry、accelerator の自動変更、外部送信は行わない。

## EXIT と status

| `EXIT` | `status` | 意味 |
|---|---|---|
| `0` | `completed` | `--entry` が終了コード 0 で完了した |
| `3` | `job_failed` | `--requirements` のインストールまたは `--entry` が非 0 で終了した（`job_exit` に終了コードが入る） |
| `124` | `timed_out` | VM 上で `--max-minutes` を超過した、またはローカル側の `exec` 上限時間を超過した |
| `4` | `runner_failed` | `upload` / `exec` / `download` / `status.json` 読取 / `out.tgz` 展開など runner 側の失敗 |
| `125` | `allocation_failed` | `colab new` による VM 確保に失敗した |
| `130` | `interrupted` | `SIGTERM` / `SIGINT` / `SIGHUP` を受けて中断し、`stop` を実行して終了した |
| `2` | `invocation_error` | 引数不正、パス境界違反、または `RUN_ID` 衝突 |
| `5` | `invocation_error` | `colab` CLI が `PATH` 上に見つからない |

## 成果物

`WORK_DIR` 直下にすべて新規作成します。ファイルは排他作成で mode `0600`、ディレクトリは mode `0700` です。

| パス | 内容 |
|---|---|
| `colab-<RUN_ID>-job.tgz` | VM へ送信した job アーカイブ |
| `colab-<RUN_ID>-sessions.json` | `--config` で分離した `colab` セッション状態ファイル |
| `colab-<RUN_ID>-bootstrap.py` | VM 上で実行した生成 bootstrap スクリプト |
| `colab-<RUN_ID>-stdout.log` | `colab exec` の標準出力・標準エラー出力 |
| `colab-<RUN_ID>-status.json` | VM から回収した実行状態 JSON（`phase`, `exit`, `timed_out`, `elapsed_s`） |
| `colab-<RUN_ID>-out.tgz` | VM から回収した `/content/out` のアーカイブ |
| `colab-<RUN_ID>-out/` | `out.tgz` を安全に展開したディレクトリ |
| `colab-<RUN_ID>-run.log` | `event + key=value` 形式の実行ログ（各 `colab` 呼出の種別・rc・所要時間を含む） |
| `colab-<RUN_ID>-summary.json` | 標準出力と同じ内容の 1 行 JSON 要約 |

## 要約 JSON

標準出力と `colab-<RUN_ID>-summary.json` に出力するフィールドは次のとおりです。

- `run_id`: 実行 ID
- `status`: 終了状態（上表の `status`）
- `EXIT`: runner の終了コード
- `job_exit`: VM 上のコマンド終了コード（未取得時は `null`）
- `phase`: 終了・失敗時の工程名（`validate`, `prepare`, `allocate`, `upload`, `exec`, `download`, `extract`, `install`, `run`, `status`, `extract_out` 等）
- `accelerator`: 要求した構成（`cpu`, `gpu:T4`, `tpu:v5e1` 等。`--high-mem` 指定時は `+high-mem` を付与）
- `session`: Colab セッション名（`cj-...`）
- `elapsed_s`: runner 全体の経過秒数
- `balance_before` / `balance_after`: 実行前後 `colab usage` の残高（取得・解析できない場合は `null`）
- `cu_used`: `balance_before - balance_after`（いずれかが `null` なら `null`）
- `stop_ok`: `colab stop` が正常終了したか（未実行時は `null`）
- `stop_verified`: `colab sessions` の出力に当該セッション名が含まれないことを確認できたか（未実行時は `null`）
- `out_dir`: 展開先ディレクトリパス（未展開時は `null`）
- `out_files`: 展開した通常ファイル数
- `artifacts`: 各成果物パスのマップ
- `error`: 失敗・中断時のエラー概要（正常終了時は省略）

## 異常終了時の確認手順

1. `stop_verified` が `true` でない場合、または要約 JSON を得られずプロセスが終了した場合は、次の 2 つのコマンドで残存セッションを確認する。
   - `colab --config <WORK_DIR>/colab-<RUN_ID>-sessions.json sessions`
   - `colab sessions`
2. 該当セッション（`cj-<正規化したRUN_ID>`）が残っている場合は、同じ `--config`（または既定設定）で `colab stop -s <session>` を実行し、再度 `sessions` で消えたことを確認する。
3. 必要に応じて `colab-<RUN_ID>-run.log` と `colab-<RUN_ID>-stdout.log` で失敗箇所と途中出力を確認する。
