---
name: codex
description: "codex CLI へ bounded な相談、または親が範囲を決めた実装を委譲する入口。『codexに聞いて』『第二意見』『Codexで実装』や `/codex` で使う。"
argument-hint: "[相談内容 / 実装タスク]"
---

# /codex — Codex CLI への相談と実装委譲

`/codex <内容>` は、Codex CLI に第二意見（相談）または実装を依頼する入口です。どちらの場合も、呼び出し元が範囲・最終判断・受入を持ち、Codex の自己申告を受入結果へ変換しません。

## 経路

- 相談・短いレビューは `SANDBOX=read-only` で runner へ委譲します。
- 実装は、ユーザーが Codex での実装を指定した場合、または親が Codex へ渡すと判断した場合に `SANDBOX=workspace-write` で runner へ委譲します。`/pir2` の実装を Codex に任せる場合もこの経路を使います。
- Codex runtime では本 Skill を使いません（`etc/sync-codex.sh` が無効化します）。Codex 自身の委譲は native collaboration で行います。
- 調査・仮説形成が主目的なら `/research` に接続します。
- background 起動が利用できる場合は親は待機せず別作業へ進み、runner が完了状態と証拠を返した後に受入します。runner が利用できない場合は、成功扱いにせず blocker として返します。
- 同じ相談・実装を続ける場合は、親が実在する session/thread の識別子を渡して既存 thread を継続します。未指定の session や report path を推測しません。

## model と effort

| 担当 | model / effort | 用途 |
| --- | --- | --- |
| worker | `gpt-6-luna` / `max` | 実装の既定。scope と終了条件が明確な通常作業 |
| expert | `gpt-6-sol` / `high` | 原因、状態、競合、性能、設計整合性など推論中心の難所 |
| expert_max | `gpt-6-sol` / `max` | 高リスク、複数仮説、特に難しい根本原因・設計 |

- 対応 effort は `gpt-6-luna` が `low` / `medium` / `high` / `xhigh` / `max`、`gpt-6-sol` がそれに加えて `ultra` です。runner はこの組合せ以外を起動前に拒否します。
- 難所は expert / expert_max を最初から選べます。Sol を使うために Luna を先に失敗させません。
- 相談の effort は問いの重さから選びます。runtime 入口に選択表がある場合はそれに従います。
- 使えるモデルは `codex debug models` で確認します。一覧にないモデルは CLI の更新（`codex update`）を先に確認します。
- 入力不足、要件未決定、権限、環境、CLI の失敗はモデル不足ではありません。自動 fallback、runner によるモデル変更、根拠のない再試行はしません。

## runner へ渡す入力

親は起動前に次を確定し、実在する値だけを渡します。

| 入力 | 内容 |
| --- | --- |
| `PROMPT` | 相談は一つの問い・成功条件・短い抜粋。実装は目的・所有ファイル・変更禁止範囲・受入条件・実行する焦点を絞った確認 |
| `CWD` | 対象リポジトリの絶対 path |
| `SANDBOX` | 相談・レビューは `read-only`、実装は `workspace-write` |
| `MODEL` / `EFFORT` | 上の表から選んだ組合せ |
| `WORK_DIR` / `RUN_ID` | runner が返す証拠を job ごとに分離する実在 path と一意な識別子 |
| `SESSION_FILE` | 継続が必要な場合だけ、親が安全性を確認した実在 path |

PROMPT には「全文を cat/rg する」「MCP を使う」「外部状態を変更する」といった指示を含めません。

## runner の完走と証拠

runner の実行手順（入力検証、stdin prompt、デタッチ起動、完了 marker の polling、resume、返却する証拠）は [references/runner.md](references/runner.md) を正本とします。親は runner 担当へこの reference の絶対 path を渡して先に Read させ、自身は内容を先読みしません。

runner は `codex exec` の実行、長時間 job の完走・再開、job 固有の完了 marker、stdout/events、stderr、最終応答、thread/session、観測した cwd と CLI 入力を管理します。runner が返した `EXIT`、thread_id、実行状態、証拠 path を親が受け取り、途中結果や存在しない結果を補いません。親が同じ CLI を直接ポーリングしません。

runner は prompt、CWD、sandbox、scope、model、effort を親の入力から変更せず、自動 fallback、blind retry、権限昇格、approval bypass、hook trust bypass、外部送信を行いません。証拠保存先は job ごとに分け、既存の成果物を削除・上書きしません。session を継続する場合も CWD と sandbox の一致を確認し、不一致を別 session へ黙って切り替えません。

## 相談の境界と結果

相談担当は対象リポジトリを編集・作成・削除・stage・commit・push せず、破壊的 git 操作や外部・本番状態の変更を行いません。返却には `ANSWER`、`EVIDENCE`、`RISKS`、`NEXT_CHECKS` を含め、欠落情報は `BLOCKED` とします。相談結果は受入判定、レビュー結果、実装完了の証拠ではありません。

## 実装の境界と受入

- 親が計画・所有範囲・受入条件を持ち、job ごとに目的、対象版、許可・禁止ファイル、依存、受入条件、focused check を切り出します。
- 独立した job だけを別 `RUN_ID` で並列化します。同じファイル、共有契約、schema、lockfile、生成物を複数 session へ同時に割り当てず、順序依存の job は先行 diff を確認してから直列に渡します。
- Codex には commit・push、外部送信、本番操作、破壊的操作、権限昇格を許可しません。
- runner の完了前に review や受入へ進みません。親が起動前後の `git status`、対象 diff、変更ファイル、確認結果を照合し、Codex の変更申告と実差分の食い違いは原因を確認します。
- FAIL 時は親が実差分と review/test 結果から原因を特定し、影響する job だけを同じ thread の継続または新しい job として渡し直します。
