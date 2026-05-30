#!/usr/bin/env bash
# foreign-ssot-guard
#
# 用途: 自セッションが dotfiles リポ等のグローバル SSOT を含む repo で、その SSOT
#       パス (.claude/CLAUDE.md / .claude/agents/** / .claude/skills/** /
#       .claude/hooks/**) への staged diff の追加行に「他プロジェクト固有名」
#       (foreign-names.cache 記載) が含まれていたら block する。
#
# トークンソース: 動的キャッシュ (foreign-names.cache) のみ。
#   - cwd basename: ~/.claude/projects/<sanitized>/*.jsonl の cwd フィールドから basename を抽出
#   - org/repo slug: 各プロジェクトの git remote get-url origin から自動抽出
#   手入力 blocklist (foreign-names.txt) は廃止済み。クラス名検出は非対応。
#
# Hook 配置: .githooks/pre-commit dispatcher から呼び出し
#             (dotfiles 以外のリポでは hook 物理パスで自己判定して exit 0 素通り)
# 入力:     引数なし (git hook として staged diff を直接参照)
# 出力:     OK なら exit 0、違反検知で exit 2 (dispatcher が exit 1 に正規化)

set -euo pipefail

# bypass フラグを先頭でチェック (${VAR:-default} 形式は -u (nounset) 下でも安全なデフォルト展開)
if [ "${FOREIGN_GUARD_DISABLE:-0}" = "1" ]; then
    echo "[foreign-ssot-guard] BYPASSED (FOREIGN_GUARD_DISABLE=1)" >&2
    exit 0
fi

# hook 実体の物理パスを取得 (symlink 解決: ~/.claude/hooks/ → dotfiles/.claude/hooks/)
hook_dir=$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# git toplevel (git hook は cwd がリポ内で実行される)
cwd_toplevel=$(git rev-parse --show-toplevel 2>/dev/null || true)
[ -n "$cwd_toplevel" ] || exit 0

# hook 実体が cwd repo 配下か判定。dotfiles リポ以外では素通り
case "$hook_dir" in
  "$cwd_toplevel"/*) ;;   # hook 実体が cwd repo 配下 = dotfiles → 検査続行
  *) exit 0 ;;            # dotfiles 以外のリポは素通り
esac

# 検査対象パスのパターン (cwd_toplevel 相対)。.claude/ 配下の SSOT のみ。
SSOT_PATHS_RE='^\.claude/(CLAUDE\.md|format\.md|pir-handoff\.md|user-feedback-protocol\.md|agents/|skills/|hooks/)'

# staged file 一覧を取得
staged_files=$(git -C "$cwd_toplevel" diff --cached --name-only 2>/dev/null || true)
[ -n "$staged_files" ] || exit 0

# SSOT パスに該当する file があるか確認。無ければ素通り。
# (SSOT_EXCLUDE_RE は foreign-names.txt 廃止に伴い削除。除外対象ファイルなし)
ssot_staged=$(echo "$staged_files" | grep -E "$SSOT_PATHS_RE" || true)
[ -n "$ssot_staged" ] || exit 0

# 動的 cache: ~/.claude/projects/<sanitized>/*.jsonl の cwd フィールドから
#   - basename
#   - org/repo slug (git remote get-url origin から自動抽出)
# を収集する。foreign-names.txt は廃止済み。
cache_file="${hook_dir}/foreign-names.cache"
projects_dir="$HOME/.claude/projects"

# session_basename: 自リポ名 (git hook 環境では CLAUDE_PROJECT_DIR が無いため
# cwd_toplevel の basename で代替)。自リポ名・自 org slug の自己ブロックを防ぐ。
session_basename=$(basename "$cwd_toplevel")

needs_rebuild=0
if [ ! -f "$cache_file" ]; then
    needs_rebuild=1
elif [ -d "$projects_dir" ] && [ "$projects_dir" -nt "$cache_file" ]; then
    needs_rebuild=1
fi

if [ "$needs_rebuild" = "1" ] && [ -d "$projects_dir" ]; then
    tmp=$(mktemp)
    trap 'rm -f "$tmp"' EXIT
    for dir in "$projects_dir"/*/; do
        [ -d "$dir" ] || continue
        # ディレクトリ内の最初の jsonl の先頭 10 行から cwd を抽出
        jsonl=$(find "$dir" -maxdepth 1 -name '*.jsonl' -print -quit 2>/dev/null)
        [ -n "$jsonl" ] || continue
        cwd=$(grep -m1 '"cwd"' "$jsonl" 2>/dev/null | jq -r '.cwd // empty' 2>/dev/null)
        [ -n "$cwd" ] || continue

        # cwd basename をキャッシュ（自リポ名は除外）
        bn=$(basename "$cwd")
        if [ "$bn" != "$session_basename" ]; then
            echo "$bn" >> "$tmp"
        fi

        # org/repo slug を git remote get-url origin から自動抽出
        # SCP:      git@github.com:org/repo.git           → org, repo
        # HTTPS:    https://github.com/org/repo.git       → org, repo
        # ssh://:   ssh://git@github.com/org/repo.git     → org, repo
        # ssh://+port: ssh://git@github.com:22/org/repo.git → org, repo
        remote_url=$(git -C "$cwd" remote get-url origin 2>/dev/null || true)
        if [ -n "$remote_url" ]; then
            # ホスト部・プロトコルを除去して "org/repo" 形式のパス部を取り出す
            # SCP 形式:  git@host:org/repo.git         → org/repo
            # HTTPS 形式: https://host/org/repo.git    → org/repo
            # ssh:// 形式: ssh://user@host/org/repo.git      → org/repo
            # ssh:// ポート付き: ssh://user@host:22/org/repo.git → org/repo
            slug=$(echo "$remote_url" | \
                sed -E 's#^ssh://[^@]*@[^/:]+:[0-9]+/##; s#^ssh://[^@]*@[^/]+/##; s#^[^@]+@[^:]+:##; s#^https?://[^/]+/##; s#\.git$##' 2>/dev/null || true)
            # slug が "org/repo" 形式（スラッシュ1つ・英数字/記号のみ）でない場合はスキップ
            grep -qE '^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$' <<<"$slug" || continue
            if [ -n "$slug" ]; then
                # "org/repo" を "/" で分割して個別トークンに展開
                while IFS= read -r token; do
                    [ -n "$token" ] || continue
                    # 自リポ名と一致するトークンは除外（自己ブロック防止）
                    [ "$token" = "$session_basename" ] && continue
                    echo "$token" >> "$tmp"
                done <<EOF
$(echo "$slug" | tr '/' '\n')
EOF
            fi
        fi
    done
    sort -u "$tmp" > "$cache_file" 2>/dev/null || true
    rm -f "$tmp"
fi

# tokens = 動的キャッシュ (foreign-names.cache) のみ
# mapfile は bash 4+ 限定なので while ループで bash 3.2 (macOS デフォルト) 互換にする
tokens=()
if [ -f "$cache_file" ]; then
    while IFS= read -r line; do
        [ -n "$line" ] || continue
        # ドット始まりトークンは native 扱いで除外する。
        # foreign な「プロジェクト固有名」は repo/org slug や非ドットの dir basename であって、
        # .claude / .codex / .config のような汎用設定ディレクトリ名は識別子にならない。
        # 特に本 guard は .claude/** SSOT を検査対象にするため、.claude は全 diff に不可避に
        # 出現し誤検知の主因になる（cwd basename が .claude だったセッションから cache に混入）。
        # 非ドットの foreign 名検知は一切弱めない。
        case "$line" in
            .*) continue ;;
        esac
        tokens+=("$line")
    done < <(grep -v -E '^[[:space:]]*(#|$)' "$cache_file" | sed -E 's/[[:space:]]+$//')
fi

[ "${#tokens[@]}" -gt 0 ] || exit 0

# 各 SSOT staged file の追加行 (+で始まる diff 行、ヘッダ +++ は除外) を抽出
# shellcheck disable=SC2046
added_lines=$(git -C "$cwd_toplevel" diff --cached -- $(echo "$ssot_staged" | tr '\n' ' ') \
  | grep -E '^\+[^+]' || true)

[ -n "$added_lines" ] || exit 0

# 混入トークンを検出
hits=()
for token in "${tokens[@]}"; do
    if grep -F -q -- "$token" <<<"$added_lines"; then
        hits+=("$token")
    fi
done

if [ "${#hits[@]}" -gt 0 ]; then
    {
        echo "[foreign-ssot-guard] BLOCKED (SSOT contamination)"
        echo
        echo "  cwd repo:        ${cwd_toplevel}"
        echo "  SSOT staged:"
        echo "$ssot_staged" | awk '{print "    " $0}'
        echo
        echo "  detected tokens (動的 foreign-names.cache のマッチ):"
        printf '    %s\n' "${hits[@]}"
        echo
        echo "  (cache は commit ごとに自動再生成。収集元: cwd basename + git remote org/repo slug)"
        echo
        echo "理由: グローバル SSOT (.claude/CLAUDE.md 等) は全プロジェクトで読まれるため、"
        echo "      特定プロジェクト固有名を混入させない (グローバル CLAUDE.md「汎用性ルール」)。"
        echo
        echo "対処:"
        echo "  - 該当箇所を汎用表現に置換 (具体プロジェクト名 → '<project-A>' / 'XxxService' 等)"
        echo "  - 事例参照ごと削除して抽象化"
        echo
        echo "BYPASS: どうしても commit したい場合のみ"
        echo "        FOREIGN_GUARD_DISABLE=1 git commit ..."
        echo "        git commit --no-verify  (全 hook を無効化)"
    } >&2

    exit 2
fi

exit 0
