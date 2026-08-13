---
name: "design-review"
description: "CodexでFigmaの個別デザインレビューを実行する。明示トリガーは「デザインについてレビューして」「このデザインレビューして」「/design-review URL」。"
---

# design-review Codex adapter

`$HOME/.claude/skills/design-review/SKILL.md` のbootstrapを全文読め。その手順に従い、bootstrapに記載された `$HOME/.claude/skills/design-review/scripts/resolve-design-repo.sh` を実行してcanonical design repoを解決し、canonical repoの `.claude/skills/design-review/SKILL.md` を全文読め。

Claude bootstrapが指定するroot基準の相対参照mappingもそのまま適用せよ。canonical Skillが見つからない場合は迂回・本文推測をせず、blockerとして報告して停止せよ。

canonical本文をこのadapterへ複製せず、Claude固有のtool・agent表現は現在のCodex capabilitiesで同じ目的を達成する形へ読み替えよ。利用できない能力を捏造せず、読み替え不能な指示はその事実を報告せよ。
