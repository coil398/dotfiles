---
name: "pir2codex"
description: "CursorのPIR²で、実装だけをCodex CLI bridgeへ委譲する。`/pir2codex`が明示されたときに使う。"
argument-hint: "[タスクの説明]"
---

# PIR² Codex — Cursor

ロード済みの本Skillから `../pir2/SKILL.md` と `../codex/SKILL.md` の実体を解決して全文Readする。PIR²の探索、計画、scope、所有、ユーザー判断、review/test、振り返り、受入を親Cursor agentに残し、実装経路だけをCodex CLI bridgeへ差し替える。

## 実装の委譲

- Codex担当、model、effort、sandbox、codex-runnerの起動・待機・session・証跡はcodex Skillを正とし、この入口で表やCLI手順を複製しない。
- 親はplanから目的、対象版、許可・禁止ファイル、依存、測定可能な受入条件、focused checkをjobごとに切り出す。独立したshardだけ別RUN_IDで並列化し、順序依存unitは先行diffを確認して直列に渡す。
- 各実装jobは`SANDBOX=workspace-write`とし、外部送信、本番操作、破壊的操作、権限昇格を許可しない。同じファイル、共有契約、schema、lockfile、生成物を複数sessionへ同時に割り当てない。
- runnerの完了通知前に受入やreviewへ進まない。親がdone marker、exit、stderr、requested値、観測可能な実効値、最終応答、`git status`、対象diff、確認結果を照合する。観測不能な実効値は`unavailable`とする。

後続担当や再開に実装記録が必要な場合だけ、PIR²が予約した実在RUN_DIRへjob固有のreportを保存する。記録には実測した変更ファイル、確認、runner証跡、未確認事項を含める。未生成report、固定台帳、全job共通fixture、Codexの自己申告を受入条件にしない。

FAIL時は親が実差分・review/test結果から原因を特定し、影響するplanとjobだけを更新する。同じthreadの継続可否はcodex Skillのsession契約に従い、自動fallbackや別modelへの無断変更を行わない。
