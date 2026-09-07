---
name: design-review
description: Figmaの個別デザインを、既存design repoの正本と基準に従ってレビューする。「このデザインレビューして」「/design-review URL」で使う。
---

# Design Review

親はこの入口の実体 path から既存 bootstrap を次の相対 path で解決し、実在・可読性を確認して `BOOTSTRAP_PATH` とする。

```bash
THIS_SKILL_PATH="<ロード済み共有 Skill の絶対 path>"
BOOTSTRAP_PATH="$(cd -P "$(dirname "$THIS_SKILL_PATH")/../../../.claude/skills/design-review" 2>/dev/null && pwd -P)/SKILL.md"
[ -r "$BOOTSTRAP_PATH" ] || exit 1
```

親は `BOOTSTRAP_PATH` を Read し、bootstrap に指定された resolver をその実体 path で実行する。resolver の出力を canonical design repo の root とし、解決先の適用 `AGENTS.md` を確認して canonical Skill の実体 path を確定し、bootstrap の相対参照 mapping を適用する。canonical Skill の読者は次段落に従い、委任のためだけに親が無条件で全文を Read しない。特定 runtime の別 home path、cwd 内の同名 Skill、未確認の fallback は推測しない。

親が直接レビューする場合は、bootstrap、resolver、canonical Skill、指定された基準を自分で順に Read する。委任する場合は、親が実在確認した `BOOTSTRAP_PATH`、resolver の実体 path、resolver が返した canonical Skill/必要な基準の物理 path/URL、対象デザイン、範囲、返却形式を担当へ渡し、担当自身に専門資料を Read させる。canonical専門本文を委任のためだけに親が無条件で先読みしない。担当は観察と未確認範囲だけを親へ返し、レビュー対象や report・記憶を保存せず、親の進行や委任を再起動しない。

canonical本文はこの入口へ複製しない。実行方法は現在のruntimeが提供するツールと委譲機能に合わせ、親が範囲と最終判断を持つ。bootstrap、resolver、canonical Skill、指定された必須基準のいずれかを取得できなければ、全体を `INCOMPLETE` とし、正本への準拠判定は行わない。独立して確認できた観察は未確認の必須範囲と分けて返し、本文や実行結果を補完して成功としない。

レビュー依頼だけではデザイン・コード・設定・記憶を変更せず、外部投稿を行わない。子の評価結果は親へ返し、保存は依頼または既存の明確な保存方針に従い親が行う。
