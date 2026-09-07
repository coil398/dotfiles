---
name: codex
description: "codex CLI を使った bounded な第二意見の相談入口。実装は委譲せず、呼び出し元が検証できる証拠と助言だけを返す。ユーザーが `/codex`、または codex への相談を明示した場合に使う。"
argument-hint: "[bounded consultation]"
---

# /codex — bounded consultation

`/codex <相談内容>` は、対象と問いを限定した read-only の第二意見を返す入口です。呼び出し元が最終判断と検証を持ち、相談担当の自己申告を受入結果へ変換しません。

## 経路

- 第二意見・短いレビューは、現在の runtime が提供する `codex-runner` 担当へ委譲します。background 起動が利用できる場合は親は待機せず別作業へ進み、runner が完了状態と証拠を返した後に受入します。runner が利用できない場合は、相談を成功扱いにせず blocker として返します。
- 調査・仮説形成が主目的なら `/research` に接続します。
- 具体的な実装・修正・リポジトリ変更は `worker-delegation` に接続します。本 skill は実装を行いません。
- 同じ相談を続ける場合は、親が実在する session/thread の識別子を渡して既存 runner を継続します。未指定の session や report path を推測しません。

## runner へ渡す入力

親は起動前に次を確定し、実在する値だけを渡します。

| 入力 | 内容 |
| --- | --- |
| `PROMPT` | 一つの問い、成功条件、判定に必要な短い抜粋。全文取得を要求しない |
| `CWD` | 対象リポジトリの絶対 path |
| `SANDBOX` | 相談・レビューは `read-only`。実装を別経路へ渡す場合だけその契約に従う |
| `MODEL` / `EFFORT` | 現在の runtime と runner が公開する選択規則に従う。固定値をこの skill で複製しない |
| `WORK_DIR` / `RUN_ID` | runner が返す証拠を job ごとに分離する実在 path と一意な識別子 |
| `SESSION_FILE` | 継続が必要な場合だけ、親が安全性を確認した実在 path |

PROMPT には対象、問い、受入条件、禁止操作、必要なら参照する関数や行の抜粋を含めます。「全文を cat/rg する」「MCP を使う」「外部状態を変更する」といった指示は含めません。入力不足、権限、環境、CLI の失敗は能力不足と推測せず、runner の実測 blocker として返します。

## runner の完走と証拠

runner は `codex exec` の実行、長時間 job の完走・再開、job 固有の完了 marker、stdout/events、stderr、最終応答、thread/session、観測した cwd と CLI 入力を管理します。runner が返した `EXIT`、thread_id、実行状態、証拠 path を親が受け取り、途中結果や存在しない結果を補いません。長時間 job は、runtime の上限を越えない runner の継続・再開手順に従い、親が同じ CLI を直接ポーリングしません。

runner は prompt、CWD、sandbox、scope、model、effort を親の入力から変更せず、自動 fallback、blind retry、権限昇格、approval bypass、hook trust bypass、外部送信を行いません。証拠保存先は job ごとに分け、既存の成果物を削除・上書きしません。session を継続する場合も CWD と sandbox の一致を確認し、不一致を別 session へ黙って切り替えません。

## 相談結果の利用

親は最終応答、stderr、対象 diff、必要なコマンド出力を照合して助言を採用します。返却には `ANSWER`、`EVIDENCE`、`RISKS`、`NEXT_CHECKS` を含め、欠落情報は `BLOCKED` とします。相談結果は受入判定、レビュー結果、実装完了の証拠ではありません。

## read-only 境界

相談担当は対象リポジトリを編集・作成・削除・stage・commit・push せず、破壊的 git 操作や外部・本番状態の変更を行いません。呼び出し元は相談後に実在する差分と検証結果を自分で確認し、相談担当へ具体的な変更責任や受入判断を委譲しません。
