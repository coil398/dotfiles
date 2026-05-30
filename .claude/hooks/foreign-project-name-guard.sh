#!/usr/bin/env bash
# foreign-project-name-guard
#
# 用途:
#   別プロジェクト由来の固有名 (= 自セッションのプロジェクト basename) が、
#   別 repo (cwd の git toplevel が session の git toplevel と異なる) への
#   git commit / gh pr (create|edit) コマンドに混入していたら block する。
#
# 動機: 汎用ツール repo の commit message / PR body には自プロジェクト固有名・固有
#       ファイルパス・固有シンボル名を書かない (グローバル CLAUDE.md「汎用性ルール」)。
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
case "$cmd" in
  *"git commit"*|*"gh pr create"*|*"gh pr edit"*) ;;
  *) exit 0 ;;
esac

session_root="${CLAUDE_PROJECT_DIR:-}"
[ -n "$session_root" ] || exit 0

session_toplevel=$(git -C "$session_root" rev-parse --show-toplevel 2>/dev/null || echo "$session_root")
cwd_toplevel=$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || echo "$PWD")

# ---- Branch A: 別 repo への commit に session project name が混入していないか ----
if [ "$cwd_toplevel" != "$session_toplevel" ]; then
    project_name=$(basename "$session_toplevel")
    if echo "$cmd" | grep -F -q -- "$project_name"; then
      cat >&2 <<MSG
[foreign-project-name-guard] BLOCKED (foreign-repo commit)

  session project: ${session_toplevel}
  cwd repo:        ${cwd_toplevel}
  detected name:   ${project_name}

外部 repo (${cwd_toplevel}) に対する git commit / gh pr (create|edit) のコマンドに、
セッションのプロジェクト名 '${project_name}' が含まれています。

理由: 汎用ツール repo の commit message / PR body には自プロジェクト固有名・固有
ファイルパス・固有シンボル名を書かない (グローバル CLAUDE.md「汎用性ルール」)。

対処: コマンド文字列から '${project_name}' とそれに紐づく具体名を取り除き、
"a real-world Go repo" "the target codebase" 等の汎用表現に書き換えてから再実行。
MSG
      exit 2
    fi
fi

exit 0
