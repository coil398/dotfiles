---
name: "dotfiles-autosync"
description: "dotfiles 専用の保全 commit、no-rebase merge、adapter 再生成、submodule 整合、push を中央 engine で実行する。"
argument-hint: "[dotfiles の Git top-level]"
---

# `/dotfiles-autosync`

dotfiles リポジトリの同期を明示的に依頼されたときに使う。実装本体はリポジトリ内の中央 script だけであり、Claude 用の処理を複製しない。

```bash
SKILL_FILE="$HOME/.claude/skills/dotfiles-autosync/SKILL.md" && SKILL_DIR="$(cd -P "$(dirname "$SKILL_FILE")" 2>/dev/null && pwd)" && CANDIDATE_ROOT="$(cd -P "$SKILL_DIR/../../.." 2>/dev/null && pwd)" && if [ -f "$CANDIDATE_ROOT/etc/dotfiles-autosync.sh" ]; then DOTFILES_ROOT="$CANDIDATE_ROOT"; else DOTFILES_ROOT="${DOTFILES_ROOT:-$HOME/dotfiles}"; fi && if [ ! -f "$DOTFILES_ROOT/etc/dotfiles-autosync.sh" ]; then printf 'dotfiles-autosync: missing engine: %s\n' "$DOTFILES_ROOT/etc/dotfiles-autosync.sh" >&2; exit 1; fi && bash "$DOTFILES_ROOT/etc/dotfiles-autosync.sh" "$DOTFILES_ROOT"
```

中央 script は Git 状態を preflight し、recursive submodule を深い順に dirty path の個別 stage、cached diff 確認、保全 commit、fetch、`git pull --no-rebase --no-edit`、push まで処理してから、親 dotfiles の保全・merge・`sync-codex.sh` / `sync-opencode.sh` / `sync-cursor.sh`・生成物／gitlink の個別 commit・clean/behind 0 確認・push を行う。したがって commit、merge、generator によるファイル更新、submodule 更新、push が副作用として発生する。

通常の WIP と divergent branch は保全して継続し、実コンテンツまたは gitlink conflict だけは自動判断せず conflict state を残してユーザーの解決を待つ。それ以外の preflight、hook、network、push、generator の失敗は破棄や自動再試行をせず、marker と復旧情報を出して停止する。

`/check-updates` はインストール済みスキル／プラグインを横断する既存の更新確認スキルで、この dotfiles 専用同期とは責務が異なる。
