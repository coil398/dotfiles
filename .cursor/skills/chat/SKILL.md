---
name: chat
description: Cursorでユーザーが明示的に /chat と入力したときの深掘り対話。必要な最新確認・ローカル確認・比較を実際に利用可能なBrowser/Search/Taskで行い、根拠と不確実性を含めて返す。通常の会話には自動適用しない。
argument-hint: "[問い]"
disable-model-invocation: true
---

<!-- Cursor native overlay: /chatの明示起動とCursorの実際の操作だけを定義する。 -->

# Chat — Cursor

`/chat <問い>` の明示入力でだけこのSkillを適用します。通常会話やSkill名の一致から自動起動しません。このnative入口の実体ディレクトリを基準に、共有原本 [../../../.agents/skills/chat/SKILL.md](../../../.agents/skills/chat/SKILL.md) を最初にReadします。別配置で起動されて相対pathを解決できない場合は、親が実在確認して渡した共有Skillの絶対pathを使います。Cursorの実際の操作へ読み替えます。

## 裏取り

- 現在・最新の仕様、価格、法令、ニュース、リリース、API、比較候補、指定URLは、Cursorセッションが公開する Browser/Search で公式一次資料を確認します。操作が利用できない、失敗した、または権限がない場合は未確認として理由を返し、推測しません。
- ローカルコードは親の直接確認、または Cursor の標準 Task に対象版、範囲、問い、編集禁止、チャット返却と必要な実行者用 Skill / reference の実体 path を渡して確認します。委任時は子自身が資料をReadし、親が直接確認する場合だけ親が必要なreferenceをReadします。readerに保存、記憶追記、コード変更、外部投稿をさせません。
- 技術候補の選定は必要なときだけ、親または標準 Task に共有 `research/references/tech-validator.md` の実体pathと比較条件を渡します。子自身が必要な資料を Read し、親が直接選定する場合だけ親が Read します。役名や固定人数でTaskを増やしません。子は親用 `/chat` の進行を再起動しません。

## 回答

共有原本の回答契約に沿って、親が結論、根拠、比較、未確認事項を構成します。

`/chat` から実装、設定変更、commit、push、外部投稿へ進みません。別作業が明示された場合は対応するSkillへ渡します。
