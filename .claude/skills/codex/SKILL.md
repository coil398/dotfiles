---
name: codex
description: Codexを指名した相談・実装委譲、難所の別アプローチ、独立レビューに使う。
---

# /codex — Codex への相談と実装委譲

ロード済みの本Skillの実体から共有原本 `../../../.agents/skills/codex/SKILL.md` を解決して先に Read し、相談・実装の入力、model / effort、実行script、受入条件は共有原本と [runner reference](../../../.agents/skills/codex/references/runner.md) に従います。Claude 固有の起動方式だけを本ファイルで定めます。

## 起動

共有原本のpackage rootを基準に `scripts/codex-run.py` を解決します。wrapperの位置からは `../../../.agents/skills/codex/scripts/codex-run.py` です。共有原本の引数を組み立て、Claudeの `Bash` をbackground実行します。

```text
Bash({ command: "python3 <script-path> <runner-arguments>", run_in_background: true })
```

## 完了通知

開始済みjobは `wait_status=completed`、`done.created=true`、`EXIT` と marker の一致を確認して受け入れます。preflight拒否は `wait_status=invocation_error` で DONE なし、worker 起動失敗は `wait_status=worker_start_failed`、`EXIT=125`、DONE なしです。timeout・supervisor異常終了・wait error は `EXIT=null` で完了扱いしません。JSONを得られなかったjobは、そのjobの `CWD` に新しい書込みjob・レビュー・commitを割り当てません。継続的なpollはせず、再開時に `DONE_FILE` を確認します。
