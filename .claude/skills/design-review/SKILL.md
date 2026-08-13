---
name: "design-review"
description: "Figmaの個別デザインをデザインシステムの正本・仕様・実データに基づいてレビューする。明示トリガーは「デザインについてレビューして」「このデザインレビューして」「/design-review URL」。"
---

# design-review bootstrap

次の手順でcanonical design repoのSkillへ委譲せよ。

1. `$HOME/.claude/skills/design-review/scripts/resolve-design-repo.sh` を実行し、出力された1行をcanonical design repoのrootとして解決せよ。
2. 解決したrepoのrootに `AGENTS.md` があれば先に全文を読め。その後、repo内の `.claude/skills/design-review/SKILL.md` を全文読め。
3. canonical Skillが見つからない、またはresolverが失敗した場合は迂回せず、本文を推測せず、blockerとして報告して停止せよ。
4. canonical Skillの相対参照とbasename参照は、すべてdesign repo rootを基準に解決せよ。旧短縮参照は次のmappingを使え。
   - `outputs/tokens.json` → `design-system/outputs/tokens.json`
   - `process-blueprint.md` → `design-system/process-blueprint.md`
   - `rules/*.md` および `qa-common-ui-rules.md`、`generation-process-rules.md`、`figma-management-rules.md`、`ui-common-rules.md` → `design-system/rules/...`
   - `reference/*.md` → `design-system/reference/...`
   - `review-cycle-log.md` → `design-system/retro/review-cycle-log.md`
5. canonical Skillの指示を正本として実行せよ。このbootstrapへcanonical本文を複製せず、canonical Skillにない内容を推測して補わず、読み替えが必要な場合はその事実を報告せよ。
