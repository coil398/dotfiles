---
name: codex
description: "Codex app-serverへboundedな相談、独立レビュー、または親が範囲を決めた実装を委譲する入口。『Codexに聞いて』『第二意見』『Codexで実装』『/pir2 の実装を任せる』や `/codex` で使う。"
argument-hint: "[相談内容 / 実装タスク]"
---

# /codex — Codex CLI への相談と実装委譲

`/codex <内容>` は、Codex CLI に第二意見（相談）または実装を依頼する入口です。どちらの場合も、呼び出し元が範囲・最終判断・受入を持ち、Codex の自己申告を受入結果へ変換しません。

## 経路

- 相談・短いレビューは `SANDBOX=read-only` で runner へ委譲します。
- 実装は、ユーザーが Codex での実装を指定した場合、または親が Codex へ渡すと判断した場合に runner へ委譲します。`SANDBOX` は省略し、ユーザーの Codex 設定に従います。Claude の親は [PIR² implementation delegation の既定の実装担当](../pir2/references/implementation-delegation.md#既定の実装担当) に従います。
- Codex runtime では本 Skill を使いません（`etc/sync-codex.sh` が無効化します）。Codex 自身の委譲は native collaboration で行います。
- 調査・仮説形成が主目的なら `/research` に接続します。
- background 完了通知が利用できる場合は、親は通知を受け取る実行方法で runner を起動し、待たずに別作業へ進みます。通知がないruntimeでは、この runner script のみを実行して結果を返す最小担当へ任せても構いません。
- 継続の可能性がある job では初回から未作成の `SESSION_FILE` を渡します。同じ `SESSION_FILE` を使うjobは同時に1つだけです。継続時は前のjobの `DONE_FILE` を確認してから、同じpathと新しい `RUN_ID` を渡します。

## model と effort

| 担当 | model / effort | 用途 |
| --- | --- | --- |
| worker | `gpt-6-luna` / 作業別目安 | 相談・実装・レビュー・分析の通常作業 |
| expert | `gpt-6.1-sol` / `medium` | 難しい独立作業、設計判断、複数の条件を統合する作業 |
| expert_max | `gpt-6.1-sol` / `max` | 高リスク、複数仮説、特に難しい根本原因・設計に限る例外 |
| worker の引き継ぎ | `gpt-6.1-sol` / `high` | 既定実装担当の引き継ぎ（詳細は[implementation-delegation SSOT](../pir2/references/implementation-delegation.md#既定の実装担当)） |

- このeffort目安はworkerの `gpt-6-luna` に限ります。機械的な置換・参照付け替え・定型編集は `medium`、新しい設計を伴う実装は `high`、難所や高リスクの作業は `max` を目安にします。expertの `gpt-6.1-sol` へ切り替えるのは、通常のworker配分を超える設計判断や複数条件の統合が必要な場合です。特に高リスクの例外は `expert_max` を選びます。
- `gpt-6-luna` は `low` / `medium` / `high` / `xhigh` / `max`、`gpt-6.1-sol` はこれらを利用できます。インストール済みCodex CLIのcatalogは `gpt-6.1-sol` に `ultra` も掲載する場合があります。OpenAI APIの `reasoning.effort` 文書とは別のcatalogなので、CLIにある値がAPIでも有効とは推測しません。この表では標準配分に含めず、明示指定がある場合だけ実際に使うCLI catalogで確認します。
- 親は作業内容から model と effort を選び、runner へ渡します。runner は値の形式だけを確認し、組合せを選び直しません。
- `gpt-6-luna` からの引き継ぎは [implementation-delegation SSOT](../pir2/references/implementation-delegation.md#既定の実装担当) に従います。
- 相談・レビュー・実装・分析は同じ表から選びます。決まった受け渡し・起動・結果取得はCodex CLIの役割ではなく、scriptを優先します。
- 使えるモデルは `codex debug models` で確認します。一覧にないモデルは CLI の更新（`codex update`）を先に確認します。
- 入力不足、要件未決定、権限、環境の問題では model を変更しません。runner は model を自動変更せず、Luna からの引き継ぎは [implementation-delegation SSOT](../pir2/references/implementation-delegation.md#既定の実装担当) の条件に従って親が判断します。

## runner へ渡す入力

親は起動前に次を確定し、実在する値だけを渡します。

| 入力 | 内容 |
| --- | --- |
| `PROMPT` | 既定はfileを `--prompt-file` で渡します（POSIXではmode `0600`）。runnerが保存するprompt artifactもPOSIXではmode `0600` です。`--prompt` は秘密を含まない短い問いに限ります。実装は目的・所有ファイル・変更禁止範囲・受入条件・実行する焦点を絞った確認 |
| `CWD` | 対象リポジトリの絶対 path |
| `SANDBOX` | 任意。指定時は `read-only`。実装では省略してユーザーの Codex 設定に従う |
| `MODEL` / `EFFORT` | 上の表から選んだ組合せ |
| `WORK_DIR` / `RUN_ID` | `WORK_DIR` は絶対 path。runner が作成してよい。`RUN_ID` は一意な `[A-Za-z0-9._-]+` |
| `SESSION_FILE` | 継続の可能性がある場合に使う絶対 path。初回はfileと`.meta`の両方が未作成、継続時は両方が既存 |

PROMPT には「全文を cat/rg する」「MCP を使う」「外部状態を変更する」といった指示を含めません。

## runner の完走と証拠

実行scriptは [`scripts/codex-run.py`](scripts/codex-run.py)、その入力・成果物・終了契約は [references/runner.md](references/runner.md) が正本です。開始済みjobは `wait_status=completed`、`done.created=true` と `EXIT` / `done.exit` / markerの一致を確認してから受け入れます。preflight拒否は `wait_status=invocation_error` でDONEなしです。workerを起動できない場合は `worker_start_failed`、`EXIT=125`、DONEなしです。timeout、supervisor異常終了、wait errorは `EXIT=null` の未完了結果として扱い、受け入れません。

Codex app-server helper は子プロセスへ `DOTFILES_AUTOSYNC_SKIP=1` を渡し、実行中は `${XDG_STATE_HOME:-$HOME/.local/state}/dotfiles-autosync/holds/` に自分の PID を記録した hold file を保持します。session-start hook は lock 取得後に live hold があれば autosync engine を起動せず、dead hold は除去してから通常起動します。

runner script は Codex app-server の実行、長時間 job の完走・再開、job 固有の完了 marker、events、stderr、最終応答、thread/session、観測した cwd と要求入力を管理します。親はJSON要約の `EXIT`、thread_id、実行状態、証拠 path を受け取り、途中結果や存在しない結果を補いません。親が同じ Codex job を別経路で直接ポーリングしません。

timeout・親shell終了・runtimeの打ち切りでJSONを得られなかったjobは、そのjobの `CWD` に新しい書込みjob・レビュー・commitを割り当てません。`DONE_FILE` がまだなければこの制限を維持し、継続的なpollはしません。再開時に `DONE_FILE` を確認し、出現後は `DONE_FILE`、最終応答、events、stderr、stateを読んでjobの完了状態を受け入れます。この操作は完了markerの確認であり、jobの継続的なpollではありません。

runner は prompt、CWD、sandbox、scope、model、effort を親の入力から変更せず、自動 fallback、blind retry、権限昇格、approval bypass、hook trust bypass、外部送信を行いません。証拠保存先は job ごとに分け、既存の成果物を削除・上書きしません。session を継続する場合も CWD と sandbox の一致を確認し、不一致を別 session へ黙って切り替えません。

## 相談の境界と結果

相談担当は対象リポジトリを編集・作成・削除・stage・commit・push せず、破壊的 git 操作や外部・本番状態の変更を行いません。返却には `ANSWER`、`EVIDENCE`、`RISKS`、`NEXT_CHECKS` を含め、欠落情報は `BLOCKED` とします。相談結果は受入判定、レビュー結果、実装完了の証拠ではありません。

## 実装の境界と受入

- 親が計画・所有範囲・受入条件を持ち、job ごとに目的、対象版、許可・禁止ファイル、依存、受入条件、focused check を切り出します。
- 独立した job だけを別 `RUN_ID` で並列化します。同じファイル、共有契約、schema、lockfile、生成物を複数 session へ同時に割り当てず、順序依存の job は先行 diff を確認してから直列に渡します。
- Codex には commit・push、外部送信、本番操作、破壊的操作、権限昇格を許可しません。
- runner の完了前に review や受入へ進みません。親が起動前後の `git status`、対象 diff、変更ファイル、確認結果を照合し、Codex の変更申告と実差分の食い違いは原因を確認します。
- FAIL 時は親が実差分と review/test 結果から原因を特定し、影響する job だけを同じ thread の継続または新しい job として渡し直します。
