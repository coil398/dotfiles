---
name: harness-run
description: Codex以外のharness（Pi、Oh my Pi、OpenCode、DeepSeek Harness）で、Codexサブスクのgpt系modelやサブスク付属APIキーのDeepSeekを、相談・レビュー・実装の担当として呼ぶ。ユーザーがこれらのharnessやmodelを指名した場合に使う。Codex CLIそのものへの委譲は codex Skill を使う。
---

# harness-run：他harnessへの委譲

`scripts/harness-run.py` は、Pi・Oh my Pi（`omp`）・OpenCode・DeepSeek Harness（`dsh`）のいずれかを非対話・ブロッキングで1回実行し、1行JSONで結果を返す。これはopt-inの経路であり、既定の実装担当は変えない。既定は [implementation-delegation](../pir2/references/implementation-delegation.md#既定の実装担当) に従う。

## 使い分け

| 目的 | 経路 |
|---|---|
| Codex CLIへの相談・実装 | `codex` Skill |
| Codexサブスク（ChatGPT OAuth）のgpt系modelをCodex以外のharnessで使う | `--harness pi` または `omp`、model `openai-codex/<id>` |
| OAuth経由のOpenCode上のgpt model | `--harness opencode`、model `openai/<id>`（認証が有効な場合） |
| DeepSeek V4.1 Flashをサブスク付属APIキーで使う | `--harness dsh`、model `opencode-go/deepseek-v4.1-flash` など |

- OpenCode Goの枠でgpt系modelを使う用途には使わない。
- `OPENAI_API_KEY`（従量課金）へは流さない。runnerは子processのenvから `OPENAI_API_KEY` を外し、`pi`/`omp`/`dsh` では provider `openai` を拒否する。
- `~/.codex/auth.json` のtokenを他harnessへ流用しない。各harnessのloginを使う。
- dshでは `openai-codex` を使えない（CLIにsign-inの経路がない）。DeepSeek専用として使う。

## 入力

```text
python3 <package>/scripts/harness-run.py --harness {pi,omp,opencode,dsh} --model <provider/model>
  --effort {low,medium,high,xhigh,max} (--prompt-file PATH | --prompt TEXT)
  --cwd ABS --work-dir ABS --run-id ID [--read-only] [--minimal-context]
  [--dsh-patch PATH] [--timeout SEC] [--dry-run]
```

- `--prompt-file` を既定にする。runnerは先頭に「別のAI CLIを起動しない」などの実行条件を付けて保存する。
- `--minimal-context` は AGENTS.md / skills / MCP / extensions を読ませない。付けた場合、委譲先repositoryの規約は依頼文に書く。
- `--run-id` は `[A-Za-z0-9._-]+`。同じIDの成果物があれば拒否する。
- `--dry-run` は組み立てたargv、env差分（キー名のみ）、書き出すfileをJSONで出し、何も実行・作成しない。
- 親はBashのbackground実行で起動し、完了通知後に1行JSONを読む。

## 認証

| harness | ログイン | 確認 |
|---|---|---|
| pi | `pi auth login openai-codex --no-browser` | runnerが `pi auth check` を起動前に実行 |
| omp | `omp login openai-codex`（Piとは別store） | runnerが `omp token <provider> --list` を実行 |
| opencode | `opencode providers login` | 起動前の確認なし。失効は `Token refresh failed` を `auth_not_ready` にする |
| dsh | 該当routeのAPIキーを環境変数で渡す（`OPENCODE_API_KEY` など） | 環境変数の有無と、`MISSING_CREDENTIAL`/`AUTH` を `auth_not_ready` にする |

`auth_not_ready` が返ったら、runnerは再試行もmodel変更もしない。ログインが必要だとユーザーへ伝える。

## read-onlyの限界

`--read-only` は各harnessのtool制限またはpermission presetで編集系を外す。OS sandboxではないため、cwd外の読取は防げない。bashを外すのでテストやgit操作はできない（dshはsandboxで拒否される）。詳細は [harnesses.md](references/harnesses.md)。

## 結果と受入

stdoutの1行JSON（`harness, model, effort, run_id, cwd, status, exit, final_text_path, events_path, stderr_path, usage, duration_s, error`）で判定する。

- `status`: `completed` / `failed` / `auth_not_ready` / `invocation_error` / `timeout`。`completed` 以外は成功扱いしない。
- 成果物は `<work-dir>/harness-<RUN_ID>-{prompt.md,events.jsonl,err.txt,last.md,summary.json,run.log}`。
- `usage` の `input_uncached` はcacheを含まない入力、`total_input = input_uncached + cache_read + cache_write`、`output` はreasoningを含む。`cost` は返さない。
- 実装を委譲した場合は、起動前後の `git status` と対象diffを親が照合する。担当の自己申告だけで受け入れない。
- `timeout`・`failed` の後は、cwdの差分を確認してから新しい `RUN_ID` で進める。
