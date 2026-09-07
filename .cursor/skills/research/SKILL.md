---
name: research
description: Cursorで研究テーマを必要な資料収集・集約・分析・仮説形成へ進める。Web/ローカル資料は問いに必要な場合だけ調べ、確認事実と推測を分ける。ユーザーが /research と入力したときに使う。
argument-hint: "[研究テーマ・問い]"
---

<!-- Cursor native overlay: 共通researchのCursor実行方式。 -->

# Research — Cursor

このnative入口の実体ディレクトリを基準に、共有原本 [../../../.agents/skills/research/SKILL.md](../../../.agents/skills/research/SKILL.md) を最初にReadします。別配置で起動されて相対pathを解決できない場合は、親が実在確認して渡した共有Skillの絶対pathを使います。親Cursor agentが問い、対象版、範囲、統合、受入、保存を所有し、未指定のRUN_DIRやHOME pathを推測しません。

## 調査

- Web、Browser、ローカル資料は問いの根拠に必要な場合だけ使います。最新仕様・リリース・価格・法令・APIは公式一次資料を確認し、URL、対象版、確認日を示します。安定した知識や提示済み本文は外部調査を省けます。
- 独立したサブ問いがあり分離の利益がある場合だけ、`Task(subagent_type="explorer")` を起動します。対象版、問い、確定事実、編集禁止、根拠をチャットで返すことを渡します。
- 技術選定が必要な場合は、Taskへ共通原本から解決した `references/tech-validator.md` の実体pathと比較条件を渡すか、親が公式資料を比較します。役名や固定人数を完了条件にしません。
- readerは常に親へチャットで返し、保存、記憶追記、コード変更、テスト生成、外部投稿をしません。Taskの失敗・timeout・未読・取得不能は未確認と明示します。

## 思考・仮説

親が調査結果を重複、出典付き事実、弱い情報、推測、対立、空白に整理します。必要な場合だけ `Task(subagent_type="thinker")` と `Task(subagent_type="hypothesizer")` を順に起動し、各Taskへ対応する共有referenceの実体path、実在する入力、対象版、編集禁止、チャット返却を渡します。thinkerは新規調査をせず、hypothesizerは検証方法の設計までです。

新しい根拠が必要になった場合だけ、具体的な追加問いをTaskへ渡します。資料不足を推測で補ったり、別モデルへ無断で切り替えたりしません。

## 統合・保存

親が、確認事実（出典）、推測、仮説（根拠・検証方法・反証条件・確信度）、未解決の問いを一つの自己完結したレポートへ必要な場合だけ統合します。保存は後段の実在消費者またはユーザーが指定した場合だけ親が行い、readerへ保存させません。研究結果から実装、commit、push、外部投稿へ自動進行しません。
