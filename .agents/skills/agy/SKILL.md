---
name: agy
description: "agy（Antigravity CLI）へACP経由で相談・思考、または範囲を決めた実装を委譲する。agy・Gemini Carbon/Hydrogenを指名した依頼で使う。Codexへの委譲は codex、Devin等その他のCLIは agent-cli、指名のない熟考は deepthink を使う。"
---

# /agy：Antigravity CLI への相談と実装委譲

`/agy <内容>` は、agy に相談・思考または実装を依頼する入口です。呼び出し元が範囲・最終判断・受入を持ち、agy の自己申告を受入結果へ変換しません。この経路はopt-inで、既定の実装担当は [implementation-delegation SSOT](../pir2/references/implementation-delegation.md#既定の実装担当) のまま変わりません。

## 用途別カタログ

用途の選択、依頼する作業、返却内容、model・modeの配分は[用途別カタログ](references/use-cases.md)を参照します。親は選んだ用途の節と必要な専門資料の実体絶対pathをPROMPTに含め、agy自身がそれを読みます。親のSkill読込状態はagyへ継承されません。

## 経路

- 相談・思考は `--mode plan` で runner へ委譲します。`plan` はworkspaceを編集しない読み取り中心のmodeですが、OS sandboxではありません。親は相談jobの前後で `git status` を照合します。
- 実装は `--mode auto` で委譲します。対象 `CWD` はagyのtrusted workspaceである必要があります。summaryに `permission_rejected` が出て作業が進んでいない場合は、trusted workspaceへの追加をユーザーに判断してもらい、新しい `RUN_ID` で再実行します。
- Codex runtimeでは本Skillを使いません（`etc/sync-codex.sh` が無効化します）。agy内からの再委譲はrunnerの前置きで禁止します。
- background完了通知が利用できる場合は、通知を受け取る実行方法でrunnerを起動し、待たずに別作業へ進みます。
- 同じ `SESSION_FILE` は、前の文脈が必要な同一jobの継続にだけ使います。継続の可能性があるjobでは初回から未作成の `SESSION_FILE` を渡します。同じ `SESSION_FILE` を使うjobは同時に1つだけで、継続時は前のjobの `DONE_FILE` を確認してから同じpath・同じ `CWD` と mode・新しい `RUN_ID` を渡します。

## model と mode

- 用途と標準配分の唯一の対応表は[用途別カタログ](references/use-cases.md#モデルと推論量)です。effortはmodel id（例 `gemini-4-hydrogen-xhigh`）に含まれます。runnerは値の形式だけを確認し、組合せを選び直しません。
- 使えるmodel idは `agy models` で確認します。一覧にないmodelは `agy update` を先に確認します。
- 入力不足、要件未決定、権限、環境の問題ではmodelを変更しません。

## runner へ渡す入力

| 入力 | 内容 |
| --- | --- |
| `PROMPT` | 既定はfileを `--prompt-file` で渡します。`--prompt` は秘密を含まない短い問いに限ります。実装では目的・所有ファイル・変更禁止範囲・受入条件・実行するfocused checkを書きます |
| `CWD` | 対象リポジトリの絶対path |
| `MODEL` / `MODE` | カタログから選んだ組合せ |
| `WORK_DIR` / `RUN_ID` | `WORK_DIR` は絶対path。`RUN_ID` は一意な `[A-Za-z0-9._-]+` |
| `SESSION_FILE` | 継続の可能性がある場合の絶対path |

PROMPTに「全文を cat する」「MCPを使う」「外部状態を変更する」といった指示を含めません。

## runner の完走と証拠

実行scriptは [`scripts/agy-run.py`](scripts/agy-run.py)、入力・成果物・終了契約は [references/runner.md](references/runner.md) が正本です。開始済みjobは `wait_status=completed`、`done.created=true` と `EXIT` / `done.exit` の一致を確認してから受け入れます。`OBSERVED_MODEL` / `OBSERVED_MODE` と `warnings` を確認し、`permission_rejected`・`empty_final_response`・mismatchがあれば結果を成功扱いにする前に原因を確かめます。preflight拒否は `wait_status=invocation_error` でDONEなし、workerを起動できない場合は `worker_start_failed`、`EXIT=125`、DONEなしです。timeout、supervisor異常終了、wait errorは `EXIT=null` の未完了結果として扱い、受け入れません。

runnerはagyのACP実行、完了marker、events、stderr、最終応答、session、観測したmodel・modeを管理します。親はJSON要約の `EXIT`、`session_id`、実行状態、証拠pathを受け取り、途中結果や存在しない結果を補いません。親が同じjobを別経路で直接ポーリングしません。未終了jobの扱いと再開時の確認は[runner reference](references/runner.md#終了契約)の終了契約に従います。

## 相談の境界と結果

相談担当は対象リポジトリを編集・作成・削除・stage・commit・pushせず、外部・本番状態を変更しません。返却には `ANSWER`、`EVIDENCE`、`RISKS`、`NEXT_CHECKS` を含め、欠落情報は `BLOCKED` とします。相談結果は受入判定、レビュー結果、実装完了の証拠ではありません。

## 実装の境界と受入

- 親が計画・所有範囲・受入条件を持ち、jobごとに目的、対象版、許可・禁止ファイル、依存、受入条件、focused checkを切り出します。
- 独立したjobだけを別 `RUN_ID` で並列化します。同じファイル、共有契約、schema、lockfile、生成物を複数jobへ同時に割り当てず、順序依存のjobは先行diffを確認してから直列に渡します。
- agyにはcommit・push、外部送信、本番操作、破壊的操作、権限昇格を許可しません。
- runnerの完了前にreviewや受入へ進みません。親が起動前後の `git status`、対象diff、変更ファイル、確認結果を照合し、agyの変更申告と実差分の食い違いは原因を確認します。
- FAIL時は親が実差分とreview/test結果から原因を特定し、影響するjobだけを同じsessionの継続または新しいjobとして渡し直します。
