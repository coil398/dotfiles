---
name: "check-updates"
description: "明示されたディレクトリ内の独立した git clone の upstream 更新を確認し、clean な fast-forward だけを適用する。マーケットプレース・プラグイン・スキルの更新確認、更新チェック、スキル更新、プラグイン最新？、update skills、check for updates に対応する。ユーザーが /check-updates と入力したら必ずこのスキルを使う。"
argument-hint: "[更新対象root ...]"
---

<!-- Cursor native overlay: Cursor の root 例と共有実行者への接続だけを定義する。 -->

# check-updates — Cursor native entry

Cursor でロードされたら、まず共有原本 [../../../.agents/skills/check-updates/SKILL.md](../../../.agents/skills/check-updates/SKILL.md) を Read する。別配置で相対 path を解決できない場合は、親が実在確認して渡した共有 Skill の絶対 path を使う。実行 engine `scripts/check-updates.sh` と更新契約は共有 package を原本とし、この入口へ複製しない。

Cursor で root を明示する場合の候補は、実在確認したものに限る（`$HOME/.cursor/plugins/marketplaces`、`$HOME/.cursor/plugins/cache`、`$HOME/.cursor/skills`、`<project>/.cursor/skills`、`<project>/.agents/skills`）。dotfiles root と submodule は `/dotfiles-autosync` の範囲であり、ここへ追加しない。親が対象と結果を持ち、Task の model/effort は AGENTS の runtime 方針に従い、この入口で固定しない。
