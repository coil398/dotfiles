#!/bin/sh
# check-updates.sh — git管理されたskills/pluginsの更新チェック＆自動pull
#
# 使い方: sh check-updates.sh [project_root]
#   project_root: プロジェクトの .claude/skills/ をチェックする場合に指定

set -eu

CLAUDE_DIR="${HOME}/.claude"
PROJECT_ROOT="${1:-}"

updated=0
checked=0
errors=""

check_and_pull() {
    dir="$1"
    label="$2"

    # .git がなければスキップ（git リポジトリでない）
    if [ ! -d "$dir/.git" ] && [ ! -f "$dir/.git" ]; then
        return
    fi

    checked=$((checked + 1))
    name="$(basename "$dir")"

    # デフォルトブランチを判定（main or master）
    default_branch=""
    for branch in main master; do
        if git -C "$dir" rev-parse --verify "origin/$branch" >/dev/null 2>&1; then
            default_branch="$branch"
            break
        fi
    done

    if [ -z "$default_branch" ]; then
        errors="${errors}\n- ${label}/${name}: デフォルトブランチ(main/master)が見つからない"
        return
    fi

    # fetch して差分チェック
    if ! git -C "$dir" fetch origin "$default_branch" --quiet 2>/dev/null; then
        errors="${errors}\n- ${label}/${name}: fetch失敗（ネットワークエラー？）"
        return
    fi

    local_hash=$(git -C "$dir" rev-parse HEAD 2>/dev/null)
    remote_hash=$(git -C "$dir" rev-parse "origin/$default_branch" 2>/dev/null)

    if [ "$local_hash" != "$remote_hash" ]; then
        # 差分あり — pull 実行
        behind=$(git -C "$dir" rev-list HEAD.."origin/$default_branch" --count 2>/dev/null || echo "?")
        if git -C "$dir" pull origin "$default_branch" --quiet 2>/dev/null; then
            echo "UPDATED: ${label}/${name} (${behind} commits behind → pulled)"
            updated=$((updated + 1))
        else
            # コンフリクト情報を収集
            conflict_files=$(git -C "$dir" diff --name-only --diff-filter=U 2>/dev/null || true)
            dirty_files=$(git -C "$dir" status --porcelain 2>/dev/null || true)
            echo "CONFLICT: ${label}/${name}"
            echo "CONFLICT_DIR: ${dir}"
            if [ -n "$conflict_files" ]; then
                echo "CONFLICT_FILES: ${conflict_files}"
            fi
            if [ -n "$dirty_files" ]; then
                echo "DIRTY_FILES:"
                echo "$dirty_files"
            fi
            # pull 失敗を巻き戻す
            git -C "$dir" merge --abort 2>/dev/null || true
            errors="${errors}\n- ${label}/${name}: pull失敗（コンフリクトまたはローカル変更あり）"
        fi
    fi
}

# 0. dotfiles リポジトリ本体（~/.claude のシンボリックリンク元）
dotfiles_dir=""
if [ -L "$CLAUDE_DIR/skills" ]; then
    resolved=$(readlink -f "$CLAUDE_DIR/skills" 2>/dev/null || readlink "$CLAUDE_DIR/skills")
    # .claude/skills/ → dotfiles/.claude/skills/ → dotfiles/ を取得
    candidate=$(dirname "$(dirname "$resolved")")
    if [ -d "$candidate/.git" ]; then
        dotfiles_dir="$candidate"
    fi
fi
if [ -n "$dotfiles_dir" ]; then
    check_and_pull "$dotfiles_dir" "dotfiles"
fi

# 1. マーケットプレースプラグイン
if [ -d "$CLAUDE_DIR/plugins/marketplaces" ]; then
    for dir in "$CLAUDE_DIR/plugins/marketplaces"/*/; do
        [ -d "$dir" ] && check_and_pull "$dir" "marketplace"
    done
fi

# 2. ユーザースコープ skills
if [ -d "$CLAUDE_DIR/skills" ]; then
    for dir in "$CLAUDE_DIR/skills"/*/; do
        [ -d "$dir" ] && check_and_pull "$dir" "user-skills"
    done
fi

# 3. プロジェクトスコープ skills
if [ -n "$PROJECT_ROOT" ] && [ -d "$PROJECT_ROOT/.claude/skills" ]; then
    for dir in "$PROJECT_ROOT/.claude/skills"/*/; do
        [ -d "$dir" ] && check_and_pull "$dir" "project-skills"
    done
fi

# 4. インストール済みプラグイン (cache)
if [ -d "$CLAUDE_DIR/plugins/cache" ]; then
    for marketplace_dir in "$CLAUDE_DIR/plugins/cache"/*/; do
        [ -d "$marketplace_dir" ] || continue
        for dir in "$marketplace_dir"/*/; do
            [ -d "$dir" ] && check_and_pull "$dir" "plugin-cache"
        done
    done
fi

# 結果出力
echo "---"
echo "CHECKED: ${checked} repos"
echo "UPDATED: ${updated} repos"
if [ -n "$errors" ]; then
    echo ""
    echo "ERRORS:"
    printf "%b\n" "$errors"
fi
if [ "$updated" -eq 0 ] && [ -z "$errors" ]; then
    echo "ALL_UP_TO_DATE"
fi
