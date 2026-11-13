---
name: agy
description: agy（Antigravity CLI）へACP経由で相談・思考、または範囲を決めた実装を委譲する。agy・Gemini Carbon/Hydrogenを指名した依頼で使う。Codexへの委譲は codex、Devin等その他のCLIは agent-cli、指名のない熟考は deepthink を使う。
argument-hint: "[相談内容 / 実装タスク]"
---

# /agy：Antigravity CLI への相談と実装委譲

ロード済みの本Skillの実体から共有原本 `../../../.agents/skills/agy/SKILL.md` を解決して先に Read し、用途は[用途別カタログ](../../../.agents/skills/agy/references/use-cases.md)で選びます。入力、model・mode、実行script、受入条件は共有原本と[runner reference](../../../.agents/skills/agy/references/runner.md)に従います。選んだカタログ節と必要な専門資料の実体絶対pathをPROMPTへ含めます。Claude固有の起動方式だけを本ファイルで定めます。

## 起動

共有原本のpackage rootを基準に `scripts/agy-run.py` を解決します。wrapperの位置からは `../../../.agents/skills/agy/scripts/agy-run.py` です。共有原本の引数を組み立て、Claudeの `Bash` をbackground実行します。

```text
Bash({ command: "python3 <script-path> <runner-arguments>", run_in_background: true })
```

## 完了通知

開始済みjobは `wait_status=completed`、`done.created=true`、`EXIT` と marker の一致を確認し、`warnings` と observed値を見てから受け入れます。preflight拒否は `wait_status=invocation_error` でDONEなし、worker起動失敗は `wait_status=worker_start_failed`、`EXIT=125`、DONEなしです。timeout・supervisor異常終了・wait errorは `EXIT=null` で完了扱いしません。DONEの無いjobは、helperとworkerのprocessが残っているかを確かめます。残っていれば未終了として扱い、その `CWD` に新しい書込みjob・レビュー・commitを割り当てません。processが残っていないと確かめられたら、成功とはみなさず、先行diffと成果物を確認してから新しい `RUN_ID` で進めます。詳細は runner reference の終了契約に従います。継続的なpollはせず、再開時に `DONE_FILE` を確認します。
