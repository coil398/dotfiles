---
name: design-review
description: Figmaの個別デザインを、既存design repoの正本と基準に従ってレビューする。「このデザインレビューして」「/design-review URL」で使う。
---

# Design Review

親は既存の `$HOME/.claude/skills/design-review/SKILL.md` を読み、そこに指定されたresolverを実行してcanonical design repoを解決する。解決先の `AGENTS.md` と `.claude/skills/design-review/SKILL.md` を読み、bootstrapの相対参照mappingを適用する。

canonical本文はこの入口へ複製しない。実行方法は現在のruntimeが提供するツールと委譲機能に合わせ、親が範囲と最終判断を持つ。bootstrap、resolver、canonical Skill、指定された必須基準のいずれかを取得できなければ、全体を `INCOMPLETE` とし、正本への準拠判定は行わない。独立して確認できた観察は未確認の必須範囲と分けて返し、本文や実行結果を補完して成功としない。

レビュー依頼だけではデザイン・コード・設定・記憶を変更せず、外部投稿を行わない。子の評価結果は親へ返し、保存は依頼または既存の明確な保存方針に従い親が行う。
