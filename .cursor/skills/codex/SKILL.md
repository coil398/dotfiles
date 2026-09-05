---
name: "codex"
description: "Codex CLIへ安全に相談・実装委譲し、codex-runnerが長時間実行を完走管理する。『codexに聞いて』『第二意見』『Codexで実装』や /codex で使う。"
---

<!-- Cursor native overlay: Codex CLI bridge -->

> **Cursor 固有ルール**
> - 子エージェントは `Task` で起動し、`model` は省略または `inherit`（親Auto）
> - Cursor agentへベンダーmodelを固定しない。Codex CLIへ渡す `MODEL` はこのbridge内で明示してよい
> - `deepthink` / `deepplan` の deliberator・synthesizer・gate だけは、それぞれのSSOTに従うFable指定を許す
> - CLI境界はnative collaborationへ置換しない。実行と長時間待機は `codex-runner` が担当する

# /codex — Codex CLI bridge

`/codex <内容>` でCodexへ第二意見または実装を依頼します。MCPは使わず、経路を「呼び出し元 → background `codex-runner` → `codex exec`」に固定します。

呼び出し元は問い、確認済み事実、対象範囲、禁止範囲、期待する出力を具体化します。相談・レビューは `SANDBOX=read-only`、明示された実装だけ `workspace-write` です。runnerの完了通知までは結果を推測せず、別の作業を進めるかターンを終えます。

## 担当の選択

通常は次の組合せを使います。

| 担当 | Codex CLI model / effort | 用途 |
| --- | --- | --- |
| worker | `gpt-5.6-luna` / `max` | scopeと終了条件が明確な通常作業 |
| expert | `gpt-5.6-sol` / `high` | 原因、状態、競合、性能、設計整合性など推論中心の難所 |
| expert_max | `gpt-5.6-sol` / `max` | 高リスク、複数仮説、特に難しい根本原因・設計 |

難所はexpert / expert_maxを最初から選べます。Solを使うためにLunaやTerraを先に失敗させません。`gpt-5.6-terra` は、同種workloadの実測でLunaより手戻りが少なくSolより総費用が低いと確認できた場合だけ、model・effort・根拠を明示して使います。

入力不足、要件未決定、権限、環境、CLI failureはmodel不足ではありません。自動fallback、runnerによるmodel変更、根拠のない再試行は禁止です。ユーザーの `--model` / `--effort` 指定も、安全境界と有効な組合せを満たす範囲で扱います。

## codex-runner の起動

`Task({ subagent_type: "codex-runner", run_in_background: true, model: "inherit", ... })` で起動します。プロンプトに次を渡します。

| 入力 | 内容 |
| --- | --- |
| `PROMPT` | Codexへ渡す非空の本文 |
| `CWD` | 対象リポジトリの絶対パス |
| `SANDBOX` | `read-only` または `workspace-write` |
| `MODEL` / `EFFORT` | 上記の有効な組合せ |
| `SELECTION_REASON` | Sol / Terraを選ぶ具体的根拠。Lunaは `standard` |
| `WORK_DIR` | この実行の入出力ディレクトリ |
| `RUN_ID` | 一意な `[A-Za-z0-9._-]+`。並列job間で重複させない |
| `SESSION_FILE` | 任意。検証済みthreadを継続する場合の保存先 |

runnerは `EXIT`、`thread_id`、最終応答、stderr、event行数、待機時間、観測したprocess cwd、CLIへ渡したrequested model・effort・sandboxと成果物pathを返します。CLI eventsから実効値を独立観測できない項目は `unavailable` とし、requested値をactual値として報告しません。`workspace-write` の場合はCodexの変更申告も返します。

メインはforegroundでCodexを起動・ポーリングしません。runnerが完了マーカーを確認する前にreviewや受入へ進みません。

## CLI契約

新規実行では、非空promptをファイルへ保存し、stdinの主指示を表す末尾引数 `-` を必ず渡します。

```bash
cat "$PROMPT_FILE" | codex exec --json --skip-git-repo-check \
  -m "$MODEL" -c "model_reasoning_effort='$EFFORT'" \
  -c 'mcp_servers.notion.enabled=false' \
  -s "$SANDBOX" -C "$CWD" -o "$OUT_LAST" -
```

空文字 `''` をprompt引数にしません。`codex exec --help` が示すとおり、prompt省略または `-` のときstdinが主指示になり、別promptとstdinを併用するとstdinは補足ブロックになります。resumeは `codex exec resume <SESSION_ID> ... -` の構文を使います。resume subcommandに `-C` / `-s` はないため、runnerがcanonical CWDへ移動し、`-c sandbox_mode=...` を指定したうえで実行します。

このコードは構文の説明です。実際の安全なquoting、デタッチ、完了マーカー、起動確認、polling、session metadataは [codex-runner](../../agents/codex-runner.md) をSSOTとします。

## プロンプト境界

- 必要な関数・差分・ログだけを呼び出し元が `PROMPT` に含め、巨大なファイル全文やリポジトリ全体の探索を無条件に要求しない
- 実装時は所有ファイル、変更禁止範囲、受入条件、実行する焦点を絞った確認を含める
- CodexにMCP、外部送信、権限昇格、破壊的操作を許可しない
- 本番変更、外部送信、破壊的操作、OS・security・権限境界の変更は別途ユーザー承認を得る

## 受入

Codexの自己申告やexit codeだけを成功とみなしません。呼び出し元が実在する最終応答、stderr、git diff、変更ファイル、要求した確認結果を検証します。reviewerとtesterは、失敗時の実害と変更が影響する挙動に必要な場合だけ別系統で使います。全reviewer、固定fixture、台帳、無関係な全テストを一律に追加しません。

`SESSION_FILE` を使う続き質問は新しいcodex-runnerで同じthreadをresumeします。前回とcwd・sandboxが一致しない場合はresumeせず、新しいsessionとして明示的に起動します。
