---
name: harness-run
description: Codex以外のharness（Pi、Oh my Pi、OpenCode、DeepSeek Harness）で、Codexサブスクのgpt系modelやサブスク付属APIキーのDeepSeekを、相談・レビュー・実装の担当として呼ぶ。ユーザーがこれらのharness名、またはDeepSeekを指名した場合に使う。harnessを挙げずにgpt系modelだけを指名した場合とCodex CLIそのものへの委譲は codex Skill を使う。
argument-hint: "[harness / model / 依頼内容]"
---

# /harness-run：他harnessへの委譲

ロード済みの本Skillの実体から共有原本 `../../../.agents/skills/harness-run/SKILL.md` を解決して先に Read し、入力・認証・read-onlyの限界・受入は共有原本と[harness別reference](../../../.agents/skills/harness-run/references/harnesses.md)に従います。Claude固有の起動方式だけを本ファイルで定めます。この経路はopt-inで、既定の実装担当は変わりません。

## 起動

共有原本のpackage rootを基準に `scripts/harness-run.py` を解決します。wrapperの位置からは `../../../.agents/skills/harness-run/scripts/harness-run.py` です。引数を組み立て、Claudeの `Bash` をbackground実行します。

```text
Bash({ command: "python3 <script-path> <runner-arguments>", run_in_background: true })
```

## 完了通知

完了通知後に1行JSONを読み、`status=completed` を確認して受け入れます。`auth_not_ready` はログインが必要だとユーザーへ伝え、`failed`・`timeout` は `CWD` の差分を確認してから新しい `RUN_ID` で進めます。継続的なpollはしません。実装では起動前後の `git status` と対象diffを照合します。
