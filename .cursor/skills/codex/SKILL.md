---
name: "codex"
description: "Codex CLIへ安全に相談・実装委譲し、background runnerが長時間実行を完走管理する。『codexに聞いて』『第二意見』『Codexで実装』や /codex で使う。"
---

<!-- Cursor native overlay: Codex CLI bridge -->

> **Cursor 固有ルール**
> - runner は標準Task（`subagent_type: "generalPurpose"`）で起動し、`model` は省略（親Auto）
> - Cursor Taskへベンダーmodelを固定しない。Codex CLIへ渡す `MODEL` はこのbridge内で明示してよい
> - CLI境界はnative collaborationへ置換しない。実行と長時間待機は runner が担当する

# /codex — Codex CLI bridge

`/codex <内容>` でCodexへ第二意見または実装を依頼します。MCPは使わず、経路を「呼び出し元 → background runner Task → `codex exec`」に固定します。

呼び出し元は問い、確認済み事実、対象範囲、禁止範囲、期待する出力を具体化します。相談・レビューは `SANDBOX=read-only`、明示された実装だけ `workspace-write` です。runnerの完了通知までは結果を推測せず、別の作業を進めるかターンを終えます。

## 担当の選択

model / effort の組合せ（worker・expert・expert_max）と、相談・実装それぞれの境界は共有原本 [../../../.agents/skills/codex/SKILL.md](../../../.agents/skills/codex/SKILL.md) に従います。ユーザーの `--model` / `--effort` 指定も、安全境界と有効な組合せを満たす範囲で扱います。

## runner の起動

このnative入口の実体から共有runner [../../../.agents/skills/codex/references/runner.md](../../../.agents/skills/codex/references/runner.md) の絶対pathを解決し、実在だけを確認します。親は内容を先読みしません。

`Task({ subagent_type: "generalPurpose", run_in_background: true, description: "codex runner", prompt })` で起動し、`model` は渡しません。`prompt` の先頭に「次の手順ファイルを先にReadし、その範囲だけ行う: <共有runnerの絶対path>」を置き、続けて次を渡します。

| 入力 | 内容 |
| --- | --- |
| `PROMPT` | Codexへ渡す非空の本文 |
| `CWD` | 対象リポジトリの絶対パス |
| `SANDBOX` | `read-only` または `workspace-write` |
| `MODEL` / `EFFORT` | 上記の有効な組合せ |
| `SELECTION_REASON` | Solを選ぶ具体的根拠。Lunaは `standard` |
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
  -s "$SANDBOX" -C "$CWD" -o "$OUT_LAST" -
```

空文字 `''` をprompt引数にしません。`codex exec --help` が示すとおり、prompt省略または `-` のときstdinが主指示になり、別promptとstdinを併用するとstdinは補足ブロックになります。resumeは `codex exec resume <SESSION_ID> ... -` の構文を使います。resume subcommandに `-C` / `-s` はないため、runnerがcanonical CWDへ移動し、`-c sandbox_mode=...` を指定したうえで実行します。

このコードは構文の説明です。実際の安全なquoting、デタッチ、完了マーカー、起動確認、polling、session metadataは共有runnerをSSOTとします。

## プロンプト境界

- 必要な関数・差分・ログだけを呼び出し元が `PROMPT` に含め、巨大なファイル全文やリポジトリ全体の探索を無条件に要求しない
- 実装時は所有ファイル、変更禁止範囲、受入条件、実行する焦点を絞った確認を含める
- CodexにMCP、外部送信、権限昇格、破壊的操作を許可しない
- 本番変更、外部送信、破壊的操作、OS・security・権限境界の変更は別途ユーザー承認を得る

## 受入

Codexの自己申告やexit codeだけを成功とみなしません。呼び出し元が実在する最終応答、stderr、git diff、変更ファイル、要求した確認結果を検証します。reviewerとtesterは、失敗時の実害と変更が影響する挙動に必要な場合だけ別系統で使います。全reviewer、固定fixture、台帳、無関係な全テストを一律に追加しません。

`SESSION_FILE` を使う続き質問は新しいrunner Taskで同じthreadをresumeします。前回とcwd・sandboxが一致しない場合はresumeせず、新しいsessionとして明示的に起動します。
