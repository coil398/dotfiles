---
name: colab
description: "Google Colab の CPU/GPU/TPU VM でローカルのスクリプトを実行し、成果物を回収する。GPU学習・大きな推論・重い数値計算をローカルより速く回したい依頼で使う。AIへの相談・実装委譲は agy または codex を使う。"
---

# /colab：Google Colab VM での計算実行

ローカルのスクリプト一式を Google Colab の VM（CPU/GPU/TPU）へ送り、実行結果と成果物を回収して VM を解放します。実行管理には [`scripts/colab-job.py`](scripts/colab-job.py) を使います。

## 使う場面・使わない場面

- 使う場面: GPU 学習、大きな推論、重い数値計算など、Google Colab の GPU/TPU/CPU で実行した方が速い処理。
- 使わない場面: 数分以内にローカルで終わる処理、対話的な作業、秘密情報や外部へ出せないデータを含む処理。AI への相談・実装委譲は `agy` または `codex` を使う。

## 前提と認証

- CLI は `google-colab-cli`（`colab`）を使う。WSL など OS keyring が無い環境では `uv tool install google-colab-cli --with keyrings.alt` で file backend を入れる。
- CLI 認証は既定の `oauth2` を使う。他ツールの認証状態を変えるため ADC を作り直さない。
- トークンが無い場合や失効している場合は、親が `colab whoami` を入力待ちで起動し、出力された認可 URL だけをユーザーへ渡す。受け取ったコードを標準入力へ入力して認証を完了させる。

## 起動前の確認

- 実行前に `colab usage` で compute unit 残高を確認する。
- accelerator は必要最小限を選ぶ。既定は CPU とし、GPU が必要な場合は `T4` から検討する。`L4` / `G4` / `A100` / `H100` や TPU（`v5e1` / `v6e1`）は計算量やメモリが明確に要る場合だけ指定する。
- `colab new` が 400 で失敗した場合は権限・枠不足のため、別の accelerator を勝手に選ばずユーザーへ返して判断を仰ぐ。

## job の書き方

- `--job-dir` の内容が VM 上の `/content/job` に展開され、カレントディレクトリ `/content/job` で `--entry` が実行される。入力ファイルは自分のディレクトリからの相対パスで読む。
- 回収対象の成果物は環境変数 `$COLAB_JOB_OUT`（`/content/out`）へ書き出す。
- 長い計算は進捗を定期的に標準出力へ `print` し、中断に備えて途中経過の checkpoint も `$COLAB_JOB_OUT` に保存する。
- 必要な Python パッケージは `--job-dir` 内のファイルにまとめ、`--requirements` で渡す。

## データの境界

- `.env`、API キー、鍵、トークン、個人情報、社外秘など外部へ出せないデータは `--job-dir` に入れない。
- データを Colab 側へ送ってよいか迷う場合は実行前にユーザーへ確認する。

## 実行

- [`scripts/colab-job.py`](scripts/colab-job.py) を絶対パスで起動する。background 実行できる runtime では完了通知を受け取る形で起動し、sleep や poll で待たない。
- `--max-minutes` は想定実行時間に十分な余裕を持たせて整数（1〜1440）で指定する。
- 入力引数・処理手順・終了コード・要約 JSON の詳細は [references/runner.md](references/runner.md) を参照する。

## 受入と残存 session の確認

- 実行後は標準出力の 1 行 JSON 要約（および `colab-<RUN_ID>-summary.json`）で `status` / `EXIT`、`stop_verified`、`cu_used`、`out_dir` を確認する。
- Colab の残高表示は即時に更新されないため、短い job の `cu_used` は 0 になることがある。消費の目安は accelerator の時間単価（`colab usage` の `Usage rate`）と `elapsed_s` から見積もる。
- `stop_verified` が `true` でない場合や要約が出ずに終わった場合は、`colab --config <sessions file> sessions` と `colab sessions` で残存 session を確認し、残っていれば `colab ... stop -s <session>` で確実に解放する。VM を残すと compute unit を消費し続ける。

## 使わないコマンド

エージェントからは TTY や対話操作を要する次のコマンドを使わない。

- `colab repl`
- `--` 無しの `colab ssh`
- `colab auth`
- `colab drivemount`
