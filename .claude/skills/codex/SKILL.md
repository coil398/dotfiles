---
name: codex
description: Codex app-serverへ相談（read-only）または実装（ユーザーのCodex設定）を委譲する。「codexに聞いて」「codexに相談」「Codexで実装」、難所の別アプローチ、独立レビュー、/pir2 の実装を Codex に任せるときに使う。
---

# /codex — Codex への相談と実装委譲

ロード済みの本 Skill の実体から共有原本 `../../../.agents/skills/codex/SKILL.md` を解決して先に Read し、相談と実装委譲の契約（入力、model / effort、実行script、相談・実装の境界と受入）に従います。本ファイルはClaude固有の起動方式だけを定めます。

`/codex <相談内容>` で第二意見を求め、`/codex <実装タスク>` で実装を委任します。Codex app-serverは共有 `scripts/codex-run.py` を通じて起動し、`mcp__codex__codex` とClaudeからの直接CLI実行は使いません。

## 起動

共有実行scriptの絶対pathをこのSkillの実体から解決します。親Claudeは共有Skillで定めた引数を組み立て、次の形で `Bash` をbackground実行します。

```text
Bash({ command: "python3 <script-path> <runner-arguments>", run_in_background: true })
```

Promptはprivateなfileを `--prompt-file` で渡す方法を既定にします（POSIXはmode `0600`、Windowsはprivate ACL）。runnerが保存するfileもmode `0600` です。`--prompt` は秘密を含まない短い問いに限ります。相談・レビューでは `--sandbox read-only` を指定し、実装ではsandboxを省略します。`MODEL` と `EFFORT` は共有 `/codex` の表とworker向けeffort目安から選び、Codex app-serverへ渡します。

Background Bashの完了通知を受け取るまで、メインClaudeは別作業へ進みます。通知後にscriptの1行JSONと返却された実在artifactを確認します。開始済みjobは `wait_status=completed`、`done.created=true` と `EXIT` がmarkerの値に一致する場合に受け入れます。preflight拒否は `wait_status=invocation_error` のJSONでDONEなしです。worker起動失敗は `wait_status=worker_start_failed`、`EXIT=125`、DONEなしです。timeout、supervisor異常終了、wait errorでは `EXIT=null` となり、完了として扱いません。timeout・親shell終了・runtimeの打ち切りでJSONを得られなかったjobは、そのjobの `CWD` に新しい書込みjob・レビュー・commitを割り当てません。`DONE_FILE` がまだなければこの制限を維持し、継続的なpollはしません。再開時に `DONE_FILE` を確認し、出現後は `DONE_FILE`、最終応答、events、stderr、stateを読んでjobの完了状態を受け入れます。この操作は完了markerの確認であり、jobの継続的なpollではありません。

Windowsではnpm版 `codex.cmd` を優先して解決します。sessionの継続、完了markerとartifact契約は共有 [runner reference](../../../.agents/skills/codex/references/runner.md) が正本です。同じ `SESSION_FILE` を使うjobは同時に1つだけです。前のjobの `DONE_FILE` を確認してから継続します。

## 受入

Codexの自己申告やexit codeだけを成功とみなしません。呼び出し元が最終応答、stderr、git diff、変更ファイル、要求した確認結果を検証します。CodexにMCP、外部送信、権限昇格、破壊的操作、本番変更を許可しません。
