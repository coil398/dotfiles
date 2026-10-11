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
- background 起動が利用できる場合は親は待機せず別作業へ進み、runner が完了状態と証拠を返した後に受入します。runner が利用できない場合は、成功扱いにせず blocker として返します。
- 継続の可能性がある job では初回から未作成の `SESSION_FILE` を渡します。継続時は同じ path と新しい `RUN_ID` を渡します。

## model と effort

| 担当 | model / effort | 用途 |
| --- | --- | --- |
| worker | `gpt-6-luna` / `max` | 相談・実装・レビュー・分析の通常作業 |
| expert | `gpt-6.1-sol` / `medium` | 難しい独立作業、設計判断、複数の条件を統合する作業 |
| expert_max | `gpt-6.1-sol` / `max` | 高リスク、複数仮説、特に難しい根本原因・設計に限る例外 |
| worker の引き継ぎ | `gpt-6.1-sol` / `high` | 既定実装担当の引き継ぎ（詳細は[implementation-delegation SSOT](../pir2/references/implementation-delegation.md#既定の実装担当)） |

- `gpt-6-luna` は `low` / `medium` / `high` / `xhigh` / `max`、`gpt-6.1-sol` はこれらを利用できます。インストール済みCodex CLIのcatalogは `gpt-6.1-sol` に `ultra` も掲載する場合があります。OpenAI APIの `reasoning.effort` 文書とは別のcatalogなので、CLIにある値がAPIでも有効とは推測しません。この表では標準配分に含めず、明示指定がある場合だけ実際に使うCLI catalogで確認します。
- 親は作業内容からこの表の組合せを選び、runner へ渡します。runner は値の形式だけを確認し、組合せを選び直しません。
- `gpt-6-luna` / `max` からの引き継ぎは [implementation-delegation SSOT](../pir2/references/implementation-delegation.md#既定の実装担当) に従います。
- 相談・レビュー・実装・分析は同じ表から選びます。決まった受け渡し・起動・結果取得はCodex CLIの役割ではなく、scriptを優先します。
- 使えるモデルは `codex debug models` で確認します。一覧にないモデルは CLI の更新（`codex update`）を先に確認します。
- 入力不足、要件未決定、権限、環境の問題では model を変更しません。runner は model を自動変更せず、Luna からの引き継ぎは [implementation-delegation SSOT](../pir2/references/implementation-delegation.md#既定の実装担当) の条件に従って親が判断します。

## runner へ渡す入力

親は起動前に次を確定し、実在する値だけを渡します。

| 入力 | 内容 |
| --- | --- |
| `PROMPT` | 相談は一つの問い・成功条件・短い抜粋。実装は目的・所有ファイル・変更禁止範囲・受入条件・実行する焦点を絞った確認 |
| `CWD` | 対象リポジトリの絶対 path |
| `SANDBOX` | 任意。相談・レビューは `read-only`、実装では省略してユーザーの Codex 設定に従う |
| `MODEL` / `EFFORT` | 上の表から選んだ組合せ |
| `WORK_DIR` / `RUN_ID` | `WORK_DIR` は runner が作成する job 固有の出力先 path。`RUN_ID` は一意な識別子 |
| `SESSION_FILE` | 継続の可能性がある場合に使う path。初回は未作成、継続時は既存 |

PROMPT には「全文を cat/rg する」「MCP を使う」「外部状態を変更する」といった指示を含めません。

## runner の完走と証拠

runner の実行手順（入力検証、prompt、デタッチ起動、完了 marker の polling、resume、返却する証拠）は [references/runner.md](references/runner.md) を正本とします。親は runner 担当へこの reference の絶対 path を渡して先に Read させ、自身は内容を先読みしません。

runner は Codex app-server の実行、長時間 job の完走・再開、job 固有の完了 marker、events、stderr、最終応答、thread/session、観測した cwd と要求入力を管理します。runner が返した `EXIT`、thread_id、実行状態、証拠 path を親が受け取り、途中結果や存在しない結果を補いません。親が同じ Codex job を直接ポーリングしません。

runner は prompt、CWD、sandbox、scope、model、effort を親の入力から変更せず、自動 fallback、blind retry、権限昇格、approval bypass、hook trust bypass、外部送信を行いません。証拠保存先は job ごとに分け、既存の成果物を削除・上書きしません。session を継続する場合も CWD と sandbox の一致を確認し、不一致を別 session へ黙って切り替えません。

## 相談の境界と結果

相談担当は対象リポジトリを編集・作成・削除・stage・commit・push せず、破壊的 git 操作や外部・本番状態の変更を行いません。返却には `ANSWER`、`EVIDENCE`、`RISKS`、`NEXT_CHECKS` を含め、欠落情報は `BLOCKED` とします。相談結果は受入判定、レビュー結果、実装完了の証拠ではありません。

## 実装の境界と受入

- 親が計画・所有範囲・受入条件を持ち、job ごとに目的、対象版、許可・禁止ファイル、依存、受入条件、focused check を切り出します。
- 独立した job だけを別 `RUN_ID` で並列化します。同じファイル、共有契約、schema、lockfile、生成物を複数 session へ同時に割り当てず、順序依存の job は先行 diff を確認してから直列に渡します。
- Codex には commit・push、外部送信、本番操作、破壊的操作、権限昇格を許可しません。
- runner の完了前に review や受入へ進みません。親が起動前後の `git status`、対象 diff、変更ファイル、確認結果を照合し、Codex の変更申告と実差分の食い違いは原因を確認します。
- FAIL 時は親が実差分と review/test 結果から原因を特定し、影響する job だけを同じ thread の継続または新しい job として渡し直します。
