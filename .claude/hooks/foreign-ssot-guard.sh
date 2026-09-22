#!/usr/bin/env bash
# foreign-ssot-guard
#
# 用途: 自セッションが dotfiles リポ等のグローバル SSOT を含む repo で、その SSOT
#       パス (AGENTS.md / .agents/skills/** / .claude/CLAUDE.md /
#       .claude/agents/** / .claude/skills/** / .claude/hooks/**)
#       への staged diff の追加行に「他プロジェクト固有名」
#       (foreign-names.cache 記載) が含まれていたら block する。
#
# トークンソース: 動的キャッシュ (foreign-names.cache) のみ。
#   - 各 session cwd を Git root に正規化
#   - 有効な origin org/repo slug があればそれを優先し、無い場合のみ root basename を使う
#   - Git root のない cwd は project identity の根拠がないため収集しない
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

# 検査対象パスのパターン (cwd_toplevel 相対)。共通 SSOT と legacy Claude SSOT。
SSOT_PATHS_RE='^(AGENTS\.md|\.agents/skills/|\.claude/(CLAUDE\.md|format\.md|pir-handoff\.md|user-feedback-protocol\.md|agent-delegation\.md|pir2-protocol\.md|dev-server\.md|subagent-permissions\.md|agents/|skills/|hooks/))'

# staged file 一覧を取得
staged_files=$(git -C "$cwd_toplevel" diff --cached --name-only 2>/dev/null || true)
[ -n "$staged_files" ] || exit 0

# SSOT パスに該当する file があるか確認。無ければ素通り。
# (SSOT_EXCLUDE_RE は foreign-names.txt 廃止に伴い削除。除外対象ファイルなし)
ssot_staged=$(echo "$staged_files" | grep -E "$SSOT_PATHS_RE" || true)
[ -n "$ssot_staged" ] || exit 0

# 動的 cache: ~/.claude/projects/<sanitized>/*.jsonl の cwd から Git root を特定し、
# 有効な origin slug または root basename を収集する。foreign-names.txt は廃止済み。
cache_file="${hook_dir}/foreign-names.cache"
projects_dir="$HOME/.claude/projects"
guard_source="${hook_dir}/$(basename "${BASH_SOURCE[0]}")"

remote_slug() {
    printf '%s\n' "$1" | sed -E \
        's#^ssh://[^@]*@[^/:]+:[0-9]+/##; s#^ssh://[^@]*@[^/]+/##; s#^[^@]+@[^:]+:##; s#^https?://[^/]+/##; s#\.git$##' \
        2>/dev/null || true
}

valid_remote_slug() {
    grep -qE '^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$' <<<"$1"
}

# session_basename: 自リポ名 (git hook 環境では CLAUDE_PROJECT_DIR が無いため
# cwd_toplevel の basename で代替)。自リポ名・自 org slug の自己ブロックを防ぐ。
session_basename=$(basename "$cwd_toplevel")

# current repo の org/repo token は native 扱いにする。
# dotfiles 自体がユーザー所有 repo のため、owner 名が README 内の正当な URL に出ることがある。
current_remote_url=$(git -C "$cwd_toplevel" remote get-url origin 2>/dev/null || true)
current_org=""
current_repo=""
if [ -n "$current_remote_url" ]; then
    current_slug=$(remote_slug "$current_remote_url")
    if valid_remote_slug "$current_slug"; then
        current_org=${current_slug%%/*}
        current_repo=${current_slug##*/}
    fi
fi

needs_rebuild=0
if [ ! -f "$cache_file" ]; then
    needs_rebuild=1
elif [ "$guard_source" -nt "$cache_file" ]; then
    needs_rebuild=1
elif [ -d "$projects_dir" ] && [ "$projects_dir" -nt "$cache_file" ]; then
    needs_rebuild=1
elif [ -d "$projects_dir" ] && find "$projects_dir" -mindepth 1 \
    \( -type d -o \( -type f -name '*.jsonl' \) \) \
    -newer "$cache_file" -print -quit | grep -q .; then
    needs_rebuild=1
fi

if [ "$needs_rebuild" = "1" ]; then
    tmp=$(mktemp)
    seen_roots=$(mktemp)
    trap 'rm -f "$tmp" "$seen_roots"' EXIT
    if [ -d "$projects_dir" ]; then
        for jsonl in "$projects_dir"/*/*.jsonl; do
            [ -f "$jsonl" ] || continue
            # `.cwd` だけを読む。session 本文はcacheにも出力にも含めない。
            cwd=$(grep -m1 '"cwd"' "$jsonl" 2>/dev/null | jq -r '.cwd // empty' 2>/dev/null || true)
            [ -n "$cwd" ] || continue

            # cwd がrepoのサブディレクトリでも、名前の根拠はGit rootから取る。
            repo_root=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null || true)
            [ -n "$repo_root" ] || continue
            repo_root=$(cd -P "$repo_root" 2>/dev/null && pwd -P || true)
            [ -n "$repo_root" ] || continue
            if grep -Fqx -- "$repo_root" "$seen_roots" 2>/dev/null; then
                continue
            fi
            printf '%s\n' "$repo_root" >> "$seen_roots"

            remote_url=$(git -C "$repo_root" remote get-url origin 2>/dev/null || true)
            slug=$(remote_slug "$remote_url")
            if valid_remote_slug "$slug"; then
                # 有効な origin がある場合はclone先の任意basenameを識別子にしない。
                while IFS= read -r token; do
                    [ -n "$token" ] || continue
                    [ "$token" = "$session_basename" ] && continue
                    [ -n "$current_org" ] && [ "$token" = "$current_org" ] && continue
                    [ -n "$current_repo" ] && [ "$token" = "$current_repo" ] && continue
                    printf '%s\n' "$token" >> "$tmp"
                done <<<"$(printf '%s\n' "$slug" | tr '/' '\n')"
            else
                # originが無い/認識できないrepoだけ、canonical root basenameを使う。
                bn=$(basename "$repo_root")
                if [ "$bn" != "$session_basename" ] && [ "$bn" != "$current_org" ] && [ "$bn" != "$current_repo" ]; then
                    printf '%s\n' "$bn" >> "$tmp"
                fi
            fi
        done
    fi
    sort -u "$tmp" > "$cache_file" 2>/dev/null || true
    rm -f "$tmp" "$seen_roots"
    trap - EXIT
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
        case "$line" in
            # 汎用インフラ語。foreign project 固有名ではなく、SSOT path や仕様説明に不可避に出る。
            agents|agent|skills|skill|codex|claude|config|dotfiles) continue ;;
        esac
        [ "$line" = "$session_basename" ] && continue
        [ -n "$current_org" ] && [ "$line" = "$current_org" ] && continue
        [ -n "$current_repo" ] && [ "$line" = "$current_repo" ] && continue
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
        echo "  (cache は guard / Claude project source 更新後に自動再生成。収集元: Git rootのorigin slug、またはoriginが無い場合のroot basename)"
        echo
        echo "理由: グローバル SSOT (AGENTS.md / .agents/skills 等) は全プロジェクトで読まれるため、"
        echo "      特定プロジェクト固有名を混入させない。"
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
