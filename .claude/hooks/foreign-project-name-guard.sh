#!/usr/bin/env bash
# foreign-project-name-guard
#
# 用途:
#   1. 別プロジェクト由来の固有名 (= 自セッションのプロジェクト basename) が、
#      別 repo (cwd の git toplevel が session の git toplevel と異なる) への
#      git commit / gh pr (create|edit) コマンドに混入していたら block する。
#   2. 自セッションが dotfiles リポ等のグローバル SSOT を含む repo で、その SSOT
#      パス (.claude/CLAUDE.md / .claude/agents/** / .claude/skills/** /
#      .claude/hooks/**) への staged diff の追加行に「他プロジェクト固有名」
#      (.claude/hooks/foreign-names.txt 記載) が含まれていたら block する。
#
# 動機: グローバル SSOT は全プロジェクト共通で読まれるため、特定プロジェクト固有名
#       を混入させない。ルールベースだと書く瞬間に意識から落ちやすいので物理的に
#       block する。
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
    # Branch A 通過 (foreign-repo 系の検査は終わり、Branch B は skip)
    exit 0
fi

# ---- Branch B: 同一 repo (self) で、グローバル SSOT への staged diff に
#                foreign-names.txt のトークンが混入していないか ----

# 検査対象パスのパターン (cwd_toplevel 相対)。.claude/ 配下の SSOT のみ。
SSOT_PATHS_RE='^\.claude/(CLAUDE\.md|format\.md|pir-handoff\.md|agents/|skills/|hooks/)'
# 例外: foreign-names.txt は blocklist 本体 = 必然的に foreign 名を含むので検査対象外
SSOT_EXCLUDE_RE='^\.claude/hooks/foreign-names\.txt$'

# このコマンドが対象とする staged file 一覧を取得
staged_files=$(git -C "$cwd_toplevel" diff --cached --name-only 2>/dev/null || true)
[ -n "$staged_files" ] || exit 0

# SSOT パスに該当する file があるか確認。無ければ素通り。
ssot_staged=$(echo "$staged_files" | grep -E "$SSOT_PATHS_RE" | grep -v -E "$SSOT_EXCLUDE_RE" || true)
[ -n "$ssot_staged" ] || exit 0

# foreign-names.txt の場所: hook script と同じディレクトリ (symlink 経由でも辿れる)
# 物理パス取得は -P で symlink 解決
hook_dir=$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)
names_file="${hook_dir}/foreign-names.txt"

if [ ! -f "$names_file" ]; then
    # blocklist が無ければ Branch B は no-op
    exit 0
fi

# blocklist 読み込み (空行・# 始まり除外)
# mapfile は bash 4+ 限定なので while ループで bash 3.2 (macOS デフォルト) 互換にする
tokens=()
while IFS= read -r line; do
    [ -n "$line" ] && tokens+=("$line")
done < <(grep -v -E '^[[:space:]]*(#|$)' "$names_file" | sed -E 's/[[:space:]]+$//')

[ "${#tokens[@]}" -gt 0 ] || exit 0

# 各 SSOT staged file の追加行 (+で始まる diff 行、ヘッダ +++ は除外) を抽出
# shellcheck disable=SC2046
added_lines=$(git -C "$cwd_toplevel" diff --cached -- $(echo "$ssot_staged" | tr '\n' ' ') \
  | grep -E '^\+[^+]' || true)

[ -n "$added_lines" ] || exit 0

# 混入トークンを検出
hits=()
for token in "${tokens[@]}"; do
    if echo "$added_lines" | grep -F -q -- "$token"; then
        hits+=("$token")
    fi
done

if [ "${#hits[@]}" -gt 0 ]; then
    {
        echo "[foreign-project-name-guard] BLOCKED (SSOT contamination)"
        echo
        echo "  cwd repo:        ${cwd_toplevel}"
        echo "  SSOT staged:"
        echo "$ssot_staged" | awk '{print "    " $0}'
        echo
        echo "  detected tokens (foreign-names.txt にマッチ):"
        printf '    %s\n' "${hits[@]}"
        echo
        echo "理由: グローバル SSOT (.claude/CLAUDE.md 等) は全プロジェクトで読まれるため、"
        echo "      特定プロジェクト固有名を混入させない (グローバル CLAUDE.md「汎用性ルール」)。"
        echo
        echo "対処:"
        echo "  - 該当箇所を汎用表現に置換 (具体プロジェクト名 → '<project-A>' / 'XxxService' 等)"
        echo "  - 事例参照ごと削除して抽象化"
        echo "  - foreign-names.txt のメンテ運用は ${names_file} を参照"
        echo
        echo "BYPASS: どうしても commit したい場合のみ"
        echo "        FOREIGN_GUARD_DISABLE=1 git commit ..."
    } >&2

    # bypass フラグ確認 (環境変数経由)
    if [ "${FOREIGN_GUARD_DISABLE:-0}" = "1" ]; then
        echo "[foreign-project-name-guard] BYPASSED (FOREIGN_GUARD_DISABLE=1)" >&2
        exit 0
    fi
    exit 2
fi

exit 0
