---
name: "cursor-dotfiles-autosync"
description: "dotfiles 専用の保全 commit、no-rebase merge、adapter 再生成、submodule 整合、push を中央 engine で実行する。"
argument-hint: "[dotfiles の Git top-level]"
---

# `/cursor-dotfiles-autosync`

Cursor から dotfiles 本体の同期を明示的に依頼されたときに使う。Cursor 用 overlay は入口だけを提供し、実装は dotfiles の中央 script に集約する。

```bash
SKILL_FILE="$HOME/.cursor/skills/cursor-dotfiles-autosync/SKILL.md" && SKILL_DIR="$(cd -P "$(dirname "$SKILL_FILE")" 2>/dev/null && pwd)" && CANDIDATE_ROOT="$(cd -P "$SKILL_DIR/../../.." 2>/dev/null && pwd)" && if [ -f "$CANDIDATE_ROOT/etc/dotfiles-autosync.sh" ]; then DOTFILES_ROOT="$CANDIDATE_ROOT"; else DOTFILES_ROOT="${DOTFILES_ROOT:-$HOME/dotfiles}"; fi && if [ ! -f "$DOTFILES_ROOT/etc/dotfiles-autosync.sh" ]; then printf 'dotfiles-autosync: missing engine: %s\n' "$DOTFILES_ROOT/etc/dotfiles-autosync.sh" >&2; exit 1; fi && bash "$DOTFILES_ROOT/etc/dotfiles-autosync.sh" "$DOTFILES_ROOT"
```

中央 script は Git root/origin/branch/upstream/未完了操作を確認し、recursive submodule を深い順に個別 path stage、cached diff 確認、保全 commit、fetch、`git pull --no-rebase --no-edit`、push する。その後、親を保全・mergeし、submodule sync/update、既存 3 generator、生成物と gitlink の個別 commit、clean/behind 0 確認、push を実行する。commit、merge、生成物更新、submodule 更新、push は明示的な副作用として扱う。

通常の WIP と divergent branch は自動保全して処理する。実コンテンツまたは gitlink conflict だけは自動的に選択せず、conflict state を残してユーザーへ戻す。preflight、hook、network、generator、push の失敗は破棄・自動解決・blind retry を行わず、marker と復旧情報を報告して停止する。

`/check-updates` はスキル／プラグインを横断する既存の更新確認であり、この dotfiles 専用の commit・merge・generator・push 同期とは責務が異なる。
