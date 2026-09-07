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
- ローカルコードは親の直接確認、または `Task(subagent_type="explorer")` に対象版、範囲、問い、編集禁止、チャット返却を渡して確認します。readerに保存、記憶追記、コード変更、外部投稿をさせません。
- 技術候補の選定は必要なときだけ、親または `Task` に共有 `research/references/tech-validator.md` の実体pathと比較条件を渡します。役名や固定人数でTaskを増やしません。

安定した知識、雑談、ユーザー提示本文の要約は外部調査なしで答えます。問いの結果を変える未決定だけを一つ質問し、既に確定した条件を再確認しません。

## 回答

問いの深さに応じて、結論、詳細、比較・注意点、次に役立つこと、実際に参照したURL/pathを構成します。短い回答指定は守り、一般論で終わらせず、セッションの目的・環境・制約へ結び付けます。推測・未確認はラベル付けします。

`/chat` から実装、設定変更、commit、push、外部投稿へ進みません。別作業が明示された場合は対応するSkillへ渡します。
