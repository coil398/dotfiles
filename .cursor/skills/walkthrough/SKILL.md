---
name: walkthrough
description: CursorでPR・ブランチ・差分・既存コードを実コードに対応する読み物へ整理する。必要な探索はTaskのexplorerへ委譲し、保存・詳細化・HTMLは依頼と対象に応じて選ぶ。固定分量や固定人数を要求しない。ユーザーが /walkthrough と入力したときに使う。
argument-hint: "[対象] [--html] [--no-save] [--fresh]"
---

<!-- Cursor native overlay: 共通walkthroughのCursor実行方式。 -->

# Walkthrough — Cursor

このnative入口の実体ディレクトリを基準に、共有原本 [../../../.agents/skills/walkthrough/SKILL.md](../../../.agents/skills/walkthrough/SKILL.md) を最初にReadします。HTML reference は共有原本の実体ディレクトリにある [references/html-mode.md](../../../.agents/skills/walkthrough/references/html-mode.md) と [references/html-template.html](../../../.agents/skills/walkthrough/references/html-template.html) を起点に解決します。別配置で起動されて共有pathを相対解決できない場合は、親が実在確認した共有Skillの絶対pathを使い、その同じpackage内のreferencesを解決します。親Cursor agentが対象版、範囲、統合、保存、詳細化、終了を所有し、対象repo内のSkill pathを推測しません。

## 対象・探索

- 明示されたPR、ブランチ、ファイル、ディレクトリ、topicを実在確認し、省略時は親が確認したローカル差分を使います。PR/branch/diffはbase/headまたは現在の変更状態を記録します。
- 既知の単一ファイルは親が直接読めます。複数レイヤー、ディレクトリ、topic、間接参照で追加確認が必要な場合だけ `Task(subagent_type="explorer")` を使います。対象版、所有範囲、具体的な問い、編集禁止、実コードと `path:line` をチャットで返すことを渡します。
- Task数、分量、ラウンド、チーム化を固定しません。readerに保存、記憶追記、コード変更、外部投稿をさせず、失敗・timeout・未読を未確認として扱います。

## 説明・キャッシュ

親は実コードとTask結果を照合し、対象規模に応じた全体像、読む順序、経路、状態・失敗、設計上の注意を返します。引用は実在する `path:line` の核心だけにし、確認できない理由は推測と表示します。キャッシュは `--fresh` でない場合に対象版・ファイル状態と比較し、一致なら再利用、部分変化なら該当範囲を更新します。保存する場合は親が実在を確認した親directory配下の今回未使用のファイルpathへ書き込み、`--no-save` ではチャットのみです。

## HTML・詳細化

`--html` が明示されたら、共有原本の実体起点から `references/html-mode.md` をReadし、そこに指定された同じ共有package内の `references/html-template.html` をReadします。親からHTML reference/template pathを渡されることを前提にせず、その手順に従ってmdと同じ事実から生成します。共有referenceの実体を解決できない場合は未確認として理由を返し、HTMLを推測生成しません。外部アップロードはしません。

ユーザーがメニューまたは自然文で指定した場合だけ、必要な実コード引用と説明を追加します。既存結果で足りる場合は再調査せず、不足する具体的な問いだけTaskへ渡します。短いQ&Aを保存せず、記録を求められた構造化説明だけ親が記録します。

返却には対象、対象版、確認範囲、全体像、読む順序、注意点、未確認事項、実際に保存したpath（保存時のみ）を含め、実装修正、review verdict、commit、pushへ自動拡張しません。
