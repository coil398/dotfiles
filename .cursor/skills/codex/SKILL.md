---
name: "codex"
description: "Codex app-serverへ相談、独立レビュー、または範囲を決めた実装を委譲する。Codexを指名した相談・実装・第二意見で使う。Codexを指名しない別アプローチや熟考には deepthink を使う。"
---

<!-- Cursor native overlay: Codex app-server runner -->

# /codex：Codex app-serverへの委任

`/codex <内容>` でCodexへ相談または実装を依頼します。問い・確認済み事実・対象範囲・禁止範囲・受入条件を具体化し、model / effort と相談・実装のsandbox境界は共有原本 [../../../.agents/skills/codex/SKILL.md](../../../.agents/skills/codex/SKILL.md) に従います。

## runner の起動

共有runner [../../../.agents/skills/codex/scripts/codex-run.py](../../../.agents/skills/codex/scripts/codex-run.py) の絶対pathをこのSkillの実体から解決します。runnerはblocking scriptなので、`generalPurpose` Taskをbackgroundで起動し、そのTaskにはscriptの起動とJSON結果の返却だけを任せます。Cursor Taskにはvendor modelを固定しません。

```text
Task({ subagent_type: "generalPurpose", run_in_background: true, description: "codex runner", prompt: "Run only: python3 <script-path> <runner-arguments>; return its JSON line and process exit code." })
```

`PROMPT` は非空本文または既存prompt fileのどちらか、`CWD` と `WORK_DIR` と `SESSION_FILE` は必要に応じて絶対pathで渡します。相談・レビューは `--sandbox read-only`、実装では `--sandbox` を省略します。`RUN_ID` は `[A-Za-z0-9._-]+` の一意な値です。新規sessionは未作成の `SESSION_FILE`、続行は同じ `SESSION_FILE` と新しい `RUN_ID` を使います。同じ `SESSION_FILE` を使うjobは同時に1つだけで、前のjobの `DONE_FILE` を確認してから続行します。

Background Taskの完了通知を受けるまで別作業を進め、通知後にJSON要約と実在するartifactを確認します。開始済みjobは `wait_status=completed`、`done.created=true` と `EXIT` / `DONE_FILE` の `EXIT=` が一致した場合に受け入れます。preflight拒否は `wait_status=invocation_error` でDONEなしです。worker起動失敗は `wait_status=worker_start_failed`、`EXIT=125`、DONEなしです。timeout、supervisor異常終了、wait errorは `EXIT=null` の未完了結果として扱います。

timeout・親shell終了・runtimeの打ち切りでJSONを得られなかったjobについては、そのjobの `CWD` に新しい書込みjob・レビュー・commitを割り当てません。`DONE_FILE` がまだなければこの制限を保留し、継続的なpollはしません。再開時に `DONE_FILE` を確認し、出現後は `DONE_FILE`、最終応答、events、stderr、stateを読んでjobの完了状態を受け入れてから続けます。この確認は完了markerの確認であり、jobの継続的なpollではありません。

## app-serverと結果

共有runner scriptはCodex app-server helperを親プロセスから切り離して実行し、終了後に公開完了markerとmachine-readable summaryを作ります。出力path、requested / observed値、usage、最終応答、session検証の詳細は共有 [runner reference](../../../.agents/skills/codex/references/runner.md) を正本とします。

Codexの自己申告やexit codeだけを成功とみなしません。呼び出し元が最終応答、stderr、git diff、変更ファイル、要求した確認結果を検証します。CodexにMCP、外部送信、権限昇格、破壊的操作、本番変更を許可しません。
