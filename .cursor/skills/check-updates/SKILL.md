---
name: "check-updates"
description: "指定ディレクトリ内の独立したgit cloneのupstream更新を確認し、cleanなfast-forwardだけを適用する。スキルやプラグインの更新確認に使う。"
argument-hint: "[更新対象root ...]"
---

<!-- Cursor native overlay: Cursor の root 例と共有実行者への接続だけを定義する。 -->

# check-updates — Cursor native entry

Cursor でロードされたら、まず共有原本 [../../../.agents/skills/check-updates/SKILL.md](../../../.agents/skills/check-updates/SKILL.md) を Read する。別配置で相対 path を解決できない場合は、親が実在確認して渡した共有 Skill の絶対 path を使う。実行 engine `scripts/check-updates.sh` と更新契約は共有 package を原本とし、この入口へ複製しない。

Cursor の既定配置には、この Skill で fast-forward する独立 clone の root は無い。`$HOME/.cursor/plugins/cache/<marketplace>/<plugin>/<commit>` は Cursor が commit 単位で管理する detached cache、`$HOME/.cursor/skills` と `<project>/.agents/skills` は dotfiles 由来のコピーまたは symlink であり、どちらも対象にしない。root は、ユーザーまたは対象リポジトリが文書化し、実在する独立 clone の親だけを明示して渡す。dotfiles root と submodule は `/dotfiles-autosync` の範囲であり、ここへ追加しない。親が対象と結果を持ち、Task の model/effort は AGENTS の runtime 方針に従い、この入口で固定しない。
