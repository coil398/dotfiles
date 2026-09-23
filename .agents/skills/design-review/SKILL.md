---
name: design-review
description: Figmaの個別デザインを、既存design repoにあるデザインシステムの正本・仕様・実データの基準に従ってレビューする。明示トリガーは「デザインについてレビューして」「このデザインレビューして」「/design-review URL」。
---

# Design Review

この入口は canonical design repo の Skill へ委譲する bootstrap である。canonical 本文はこの入口へ複製しない。

## canonical Skill の解決

1. 親はロード済みの本 `SKILL.md` の実体ディレクトリから `scripts/resolve-design-repo.sh` を解決し、実在・実行可能を確認して `RESOLVER_PATH` とする。実行し、出力された1行を canonical design repo の root とする。
2. root に `AGENTS.md` があれば先に読む。canonical Skill は design repo 側の配置である `<root>/.claude/skills/design-review/SKILL.md` とし、実在を確認して実体 path を確定する。
3. canonical Skill の相対参照と basename 参照は、すべて design repo root を基準に解決する。短縮参照は次の mapping を使う。
   - `outputs/tokens.json` → `design-system/outputs/tokens.json`
   - `process-blueprint.md` → `design-system/process-blueprint.md`
   - `rules/*.md` および `qa-common-ui-rules.md`、`generation-process-rules.md`、`figma-management-rules.md`、`ui-common-rules.md` → `design-system/rules/...`
   - `reference/*.md` → `design-system/reference/...`
   - `review-cycle-log.md` → `design-system/retro/review-cycle-log.md`
4. canonical Skill の指示を正本として実行する。canonical Skill にない内容を推測して補わず、読み替えが必要な場合はその事実を報告する。

resolver が失敗した、または canonical Skill が見つからない場合は迂回せず、本文を推測せず、blocker として報告して停止する。特定 runtime の別 home path、cwd 内の同名 Skill、未確認の fallback は推測しない。

## 読む担当と委任

親が直接レビューする場合は、resolver、canonical Skill、指定された基準を自分で順に Read する。委任する場合は、親が実在確認した `RESOLVER_PATH`、resolver が返した root、canonical Skill と必要な基準の物理 path/URL、上の mapping、対象デザイン、範囲、返却形式を担当へ渡し、担当自身に専門資料を Read させる。canonical 専門本文を委任のためだけに親が無条件で先読みしない。担当は観察と未確認範囲だけを親へ返し、レビュー対象や report・記憶を保存せず、親の進行や委任を再起動しない。

実行方法は現在の runtime が提供するツールと委譲機能に合わせ、親が範囲と最終判断を持つ。resolver、canonical Skill、指定された必須基準のいずれかを取得できなければ、全体を `INCOMPLETE` とし、正本への準拠判定は行わない。独立して確認できた観察は未確認の必須範囲と分けて返し、本文や実行結果を補完して成功としない。

レビュー依頼だけではデザイン・コード・設定・記憶を変更せず、外部投稿を行わない。子の評価結果は親へ返し、保存は依頼または既存の明確な保存方針に従い親が行う。
