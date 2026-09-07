---
name: walkthrough
description: CursorでPR・ブランチ・差分・既存コードを実コードに対応する読み物へ整理する。必要な探索はCursorの標準Taskへ委譲し、保存・詳細化・HTMLは依頼と対象に応じて選ぶ。固定分量や固定人数を要求しない。ユーザーが /walkthrough と入力したときに使う。
argument-hint: "[対象] [--html] [--no-save] [--fresh]"
---

<!-- Cursor native overlay: 共通walkthroughのCursor実行方式。 -->

# Walkthrough — Cursor

このnative入口の実体ディレクトリを基準に、共有原本 [../../../.agents/skills/walkthrough/SKILL.md](../../../.agents/skills/walkthrough/SKILL.md) を最初にReadします。HTML reference は共有原本の実体ディレクトリにある [references/html-mode.md](../../../.agents/skills/walkthrough/references/html-mode.md) と [references/html-template.html](../../../.agents/skills/walkthrough/references/html-template.html) を起点に解決します。別配置で起動されて共有pathを相対解決できない場合は、親が実在確認した共有Skillの絶対pathを使い、その同じpackage内のreferencesを解決します。親Cursor agentが対象版、範囲、統合、保存、詳細化、終了を所有し、対象repo内のSkill pathを推測しません。

## 対象・探索

- 明示されたPR、ブランチ、ファイル、ディレクトリ、topicを実在確認し、省略時は親が確認したローカル差分を使います。PR/branch/diffはbase/headまたは現在の変更状態を記録します。
- 既知の単一ファイルは親が直接読めます。複数レイヤー、ディレクトリ、topic、間接参照で追加確認が必要な場合だけ Cursor の標準 Task または標準 read-only child を使います。対象版、所有範囲、具体的な問い、編集禁止、実コードと `path:line` をチャットで返すこと、必要な実行者用 Skill / reference の実体 path を渡して、子自身に資料をReadさせます。特定の探索Agentや固定Task識別子を必須にせず、親が直接確認する場合だけ必要なreferenceをReadします。
- readerに保存、記憶追記、コード変更、外部投稿をさせず、失敗・timeout・未読を未確認として扱います。子へ親用 `/walkthrough` の説明・詳細化・保存ループを渡して同じ工程を再起動させません。

## HTML・詳細化

`--html` が明示されたら、共有原本の実体起点から `references/html-mode.md` をReadし、そこに指定された同じ共有package内の `references/html-template.html` をReadします。親からHTML reference/template pathを渡されることを前提にせず、その手順に従ってmdと同じ事実から生成します。共有referenceの実体を解決できない場合は未確認として理由を返し、HTMLを推測生成しません。外部アップロードはしません。

詳細化、キャッシュ、再開、保存、返却は共有原本の手順に接続し、説明結果の統合と実際の保存は親が行います。
