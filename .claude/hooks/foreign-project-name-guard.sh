#!/usr/bin/env bash
# foreign-project-name-guard
#
# 用途:
#   全 project へ配布される汎用 repo (= この hook 自身が属する dotfiles repository) への
#   git commit / gh pr (create|edit) のコマンドに、セッションの project 名 (git toplevel の
#   basename) が単語として含まれていたら block する。
#
# 根拠: .agents/global-instructions.md 冒頭「プロジェクト固有の型・API・ディレクトリ構成・
#       社内名はここに混ぜず…」。汎用 repo の commit message / PR body に自 project 固有名を書かない。
#
# 対象 repo: コマンドの `git -C <path>` があればその path、なければ $PWD の git toplevel。
#           dotfiles root でなければ、または session repo が dotfiles 自身なら検査しない。
#
# Hook 配置: PreToolUse, matcher=Bash
# 入力:     stdin に Hook input JSON
# 出力:     OK なら exit 0、違反検知で exit 2 (= block + reason を stderr で model に提示)

set -euo pipefail

input=$(cat)
tool=$(echo "$input" | jq -r '.tool_name // ""')
[ "$tool" = "Bash" ] || exit 0

cmd=$(echo "$input" | jq -r '.tool_input.command // ""')

# 文章を伴うコマンド (commit message / PR body) のみ検査対象。
# `git -C <path> commit` の形も含める。
if ! [[ "$cmd" =~ git[[:space:]]+(.*[[:space:]])?commit([[:space:]]|$) || "$cmd" == *"gh pr create"* || "$cmd" == *"gh pr edit"* ]]; then
  exit 0
fi

session_root="${CLAUDE_PROJECT_DIR:-}"
[ -n "$session_root" ] || exit 0

# dotfiles root: この hook は ~/.claude/hooks 経由 (symlink) で実行されるため物理位置で解決する。
dotfiles_root="$(cd -P "$(dirname "${BASH_SOURCE[0]}")/../.." 2>/dev/null && pwd)" || exit 0
dotfiles_toplevel=$(git -C "$dotfiles_root" rev-parse --show-toplevel 2>/dev/null || echo "$dotfiles_root")

session_toplevel=$(git -C "$session_root" rev-parse --show-toplevel 2>/dev/null || echo "$session_root")
[ "$session_toplevel" != "$dotfiles_toplevel" ] || exit 0

# 対象 repo: 最初の `git -C <path>` (引用符付き可)。無ければ $PWD。
target_dir=""
if [[ "$cmd" =~ git[[:space:]]+-C[[:space:]]+(\"([^\"]*)\"|\'([^\']*)\'|([^[:space:]]+)) ]]; then
  target_dir="${BASH_REMATCH[2]:-${BASH_REMATCH[3]:-${BASH_REMATCH[4]}}}"
fi
[ -n "$target_dir" ] || target_dir="$PWD"
target_toplevel=$(git -C "$target_dir" rev-parse --show-toplevel 2>/dev/null) || exit 0
[ "$target_toplevel" = "$dotfiles_toplevel" ] || exit 0

project_name=$(basename "$session_toplevel")
if echo "$cmd" | grep -w -F -q -- "$project_name"; then
  cat >&2 <<MSG
[foreign-project-name-guard] BLOCKED (generic repo commit)

  session project: ${session_toplevel}
  target repo:     ${target_toplevel}
  detected name:   ${project_name}

汎用 repo (${target_toplevel}) に対する git commit / gh pr (create|edit) のコマンドに、
セッションの project 名 '${project_name}' が含まれています。

理由: .agents/global-instructions.md 冒頭の「プロジェクト固有の型・API・ディレクトリ構成・
社内名はここに混ぜず…」に反します。汎用 repo の commit message / PR body には自 project
固有名・固有ファイルパス・固有シンボル名を書きません。

対処: コマンド文字列から '${project_name}' とそれに紐づく具体名を取り除き、
"a real-world Go repo" "the target codebase" 等の汎用表現に書き換えてから再実行。
MSG
  exit 2
fi

exit 0
