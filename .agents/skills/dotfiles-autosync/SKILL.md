---
name: "dotfiles-autosync"
description: "dotfiles 本体を明示的に保全 commit、no-rebase merge、adapter 再生成、submodule 整合、push まで同期する。既存 check-updates とは別の dotfiles 専用入口。"
argument-hint: "[dotfiles の Git top-level]"
---

# Dotfiles Autosync

dotfiles リポジトリ自身を、ユーザーが明示的に依頼したときだけ同期する。
スキルの実装は runtime ごとに複製せず、中央 engine の `etc/dotfiles-autosync.sh` に集約する。

```bash
SKILL_FILE="$HOME/.agents/skills/dotfiles-autosync/SKILL.md" && SKILL_DIR="$(cd -P "$(dirname "$SKILL_FILE")" 2>/dev/null && pwd)" && CANDIDATE_ROOT="$(cd -P "$SKILL_DIR/../../.." 2>/dev/null && pwd)" && if [ -f "$CANDIDATE_ROOT/etc/dotfiles-autosync.sh" ]; then DOTFILES_ROOT="$CANDIDATE_ROOT"; else DOTFILES_ROOT="${DOTFILES_ROOT:-$HOME/dotfiles}"; fi && if [ ! -f "$DOTFILES_ROOT/etc/dotfiles-autosync.sh" ]; then printf 'dotfiles-autosync: missing engine: %s\n' "$DOTFILES_ROOT/etc/dotfiles-autosync.sh" >&2; exit 1; fi && bash "$DOTFILES_ROOT/etc/dotfiles-autosync.sh" "$DOTFILES_ROOT"
```

中央 engine は次を順番に実行する。

- Git root、`origin`、branch/upstream、未完了操作を preflight する
- recursive submodule を深い階層から、dirty path の個別 stage・cached diff 確認・保全 commit・fetch・`git pull --no-rebase --no-edit`・push する
- 親 dotfiles の tracked/staged/untracked 変更を保全 commit する
- 親を no-rebase merge し、`git submodule sync/update` と既存 3 adapter generator を実行する
- 生成物と submodule pointer の差分だけを個別 stage・cached diff 確認・commit し、clean/behind 0 を確認して push する

この処理は commit、merge、生成物更新、submodule 更新、push という明示的な副作用を持つ。ローカル WIP や通常の divergent branch は保全して統合する。実コンテンツまたは gitlink の conflict だけは自動判断せず conflict state を残してユーザーの解決を待つ。hook、認証、network、push、preflight、generator の失敗も破棄や自動再試行をせず、marker と復旧情報を出して停止する。

`/check-updates` はスキル・プラグインを横断して更新確認する既存機能であり、dotfiles 本体の明示的な保全・merge・generator・push をこのスキルの代わりに行うものではない。
