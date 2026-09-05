---
name: "dotfiles-autosync"
description: "dotfiles 本体を中央 engine で保全 commit、no-rebase merge、adapter 再生成、submodule 整合、push する明示的同期。"
argument-hint: "[dotfiles の Git top-level]"
---

# `/dotfiles-autosync`

Codex から dotfiles 本体の同期を明示的に依頼された場合の入口。runtime 固有の Git 実装は持たず、次の中央 script を呼ぶ。

```bash
SKILL_FILE="$HOME/.codex/skills/dotfiles-autosync/SKILL.md" && SKILL_DIR="$(cd -P "$(dirname "$SKILL_FILE")" 2>/dev/null && pwd)" && CANDIDATE_ROOT="$(cd -P "$SKILL_DIR/../../.." 2>/dev/null && pwd)" && if [ -f "$CANDIDATE_ROOT/etc/dotfiles-autosync.sh" ]; then DOTFILES_ROOT="$CANDIDATE_ROOT"; else DOTFILES_ROOT="${DOTFILES_ROOT:-$HOME/dotfiles}"; fi && if [ ! -f "$DOTFILES_ROOT/etc/dotfiles-autosync.sh" ]; then printf 'dotfiles-autosync: missing engine: %s\n' "$DOTFILES_ROOT/etc/dotfiles-autosync.sh" >&2; exit 1; fi && bash "$DOTFILES_ROOT/etc/dotfiles-autosync.sh" "$DOTFILES_ROOT"
```

中央 script は preflight 後、recursive submodule を深い階層から個別 path stage → cached diff 確認 →保全 commit → fetch → `git pull --no-rebase --no-edit` → push の順に処理する。続いて親の WIP 保全、no-rebase merge、`git submodule sync --recursive`、`git submodule update --init --recursive`、Codex/OpenCode/Cursor/Antigravity の adapter generator、生成物／gitlink の個別 commit、clean/behind 0 確認、push を行う。commit、merge、生成物更新、submodule 更新、push が明示的な副作用である。

通常の WIP や divergent branch は保全して継続するが、実コンテンツまたは gitlink conflict は自動選択せず conflict state を保持してユーザーへ戻す。preflight、hook、network、generator、push の失敗も状態を残して marker と復旧情報を出し、破棄や自動再試行はしない。

`/check-updates` はスキル・プラグインを横断して更新を確認する既存機能であり、dotfiles 本体をこの入口の代わりに同期する責務は持たない。
