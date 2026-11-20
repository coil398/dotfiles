#!/bin/sh
# Fetch official pstack and copy it into Cursor's local plugin directory.
# Claude Code reads pstack from ~/.claude/settings.json, which link.sh deploys.
set -eu

CHECKOUT="${CURSOR_PLUGINS_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/dotfiles/cursor-plugins}"
URL="${CURSOR_PLUGINS_REPO_URL:-https://github.com/cursor/plugins.git}"
LOCAL_DIR="${HOME}/.cursor/plugins/local"
DEST="${LOCAL_DIR}/pstack"
MARKER="${LOCAL_DIR}/.pstack.dotfiles-managed"
PSTACK_NAME_PATTERN='"name"[[:space:]]*:[[:space:]]*"pstack"'

if [ -z "${HOME:-}" ] || [ "$HOME" = "/" ]; then
    echo "[sync-pstack] skip reason=home_unavailable"
    exit 0
fi

manifest_is_pstack() {
    [ -f "$1" ] && grep -Eq "$PSTACK_NAME_PATTERN" "$1"
}

marketplace_pstack_present() {
    plugins_root="$HOME/.cursor/plugins"
    [ -d "$plugins_root" ] || return 1
    find "$plugins_root" \
        \( -path "$plugins_root/local" -o -path "$plugins_root/local/*" \) -prune -o \
        -type f -name plugin.json -exec grep -Eq "$PSTACK_NAME_PATTERN" {} \; -print |
        grep -q .
}

remove_managed_copy() {
    if [ -f "$MARKER" ]; then
        rm -rf "$DEST"
        rm -f "$MARKER"
        echo "[sync-pstack] removed path=$DEST reason=marketplace_pstack_present"
    fi
}

if marketplace_pstack_present; then
    remove_managed_copy
    echo "[sync-pstack] skip reason=marketplace_pstack_present"
    exit 0
fi

if ! command -v git >/dev/null 2>&1; then
    echo "[sync-pstack] skip reason=git_unavailable"
    exit 0
fi
if ! command -v timeout >/dev/null 2>&1; then
    echo "[sync-pstack] skip reason=timeout_unavailable"
    exit 0
fi

git_quiet() {
    timeout 60 env GIT_TERMINAL_PROMPT=0 \
        GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh} -o BatchMode=yes -o ConnectTimeout=10" \
        git "$@"
}

checkout_ready=0
checkout_dirty=0
if [ -e "$CHECKOUT" ]; then
    if [ ! -d "$CHECKOUT" ] || [ "$(git -C "$CHECKOUT" rev-parse --show-toplevel 2>/dev/null || true)" != "$(cd "$CHECKOUT" && pwd -P)" ]; then
        echo "[sync-pstack] skip reason=existing_path_not_checkout path=$CHECKOUT"
        exit 0
    elif ! checkout_status="$(git -C "$CHECKOUT" status --porcelain)"; then
        echo "[sync-pstack] update_failed reason=status_unavailable path=$CHECKOUT preserved=1"
    elif [ -n "$checkout_status" ]; then
        echo "[sync-pstack] update_skipped reason=dirty_checkout path=$CHECKOUT preserved=1"
        checkout_ready=1
        checkout_dirty=1
    elif ! git_quiet -C "$CHECKOUT" pull --ff-only; then
        echo "[sync-pstack] update_failed reason=ff_only_failed path=$CHECKOUT preserved=1"
        checkout_ready=1
    else
        echo "[sync-pstack] updated path=$CHECKOUT"
        checkout_ready=1
    fi
else
    checkout_parent="$(dirname "$CHECKOUT")"
    mkdir -p "$checkout_parent" || {
        echo "[sync-pstack] skip reason=checkout_parent_unavailable path=$checkout_parent"
        exit 0
    }
    fetch_stage="$(mktemp -d "$checkout_parent/.cursor-plugins-fetch.XXXXXX")" || fetch_stage=""
    if [ -z "$fetch_stage" ]; then
        echo "[sync-pstack] skip reason=staging_unavailable"
        exit 0
    fi
    if git_quiet clone --depth 1 --filter=blob:none --sparse "$URL" "$fetch_stage/checkout" \
        && git_quiet -C "$fetch_stage/checkout" sparse-checkout set pstack \
        && mv "$fetch_stage/checkout" "$CHECKOUT"; then
        echo "[sync-pstack] acquired path=$CHECKOUT"
        checkout_ready=1
    else
        echo "[sync-pstack] acquire_failed path=$CHECKOUT url=$URL preserved=1"
    fi
    rm -rf "$fetch_stage"
fi

if [ "$checkout_ready" -ne 1 ]; then
    exit 0
fi

source_dir="$CHECKOUT/pstack"
if ! manifest_is_pstack "$source_dir/.cursor-plugin/plugin.json"; then
    echo "[sync-pstack] skip reason=pstack_manifest_missing path=$source_dir"
    exit 0
fi

head_sha="$(git -C "$CHECKOUT" rev-parse HEAD)"
if [ "$checkout_dirty" -eq 1 ] && [ -f "$MARKER" ] && [ -d "$DEST" ]; then
    echo "[sync-pstack] skip reason=dirty_checkout path=$DEST preserved=1"
    exit 0
fi
if [ -f "$MARKER" ] && [ -d "$DEST" ] && [ "$(cat "$MARKER")" = "$head_sha" ]; then
    echo "[sync-pstack] skip reason=already_current sha=$head_sha path=$DEST"
    exit 0
fi
if [ -e "$DEST" ] && [ ! -f "$MARKER" ]; then
    echo "[sync-pstack] skip reason=local_directory_not_managed path=$DEST"
    exit 0
fi

mkdir -p "$LOCAL_DIR"
copy_stage="$(mktemp -d "$LOCAL_DIR/.pstack-copy.XXXXXX")" || {
    echo "[sync-pstack] skip reason=copy_staging_unavailable"
    exit 0
}
if ! mkdir -p "$copy_stage/tree" || ! cp -a "$source_dir/." "$copy_stage/tree/"; then
    rm -rf "$copy_stage"
    echo "[sync-pstack] copy_failed path=$DEST preserved=1"
    exit 0
fi
if ! manifest_is_pstack "$copy_stage/tree/.cursor-plugin/plugin.json"; then
    rm -rf "$copy_stage"
    echo "[sync-pstack] copy_failed reason=manifest_missing path=$DEST preserved=1"
    exit 0
fi
rm -rf "$DEST"
if ! mv "$copy_stage/tree" "$DEST"; then
    rm -rf "$copy_stage"
    echo "[sync-pstack] copy_failed reason=move_failed path=$DEST"
    exit 0
fi
rm -rf "$copy_stage"
printf '%s\n' "$head_sha" >"$MARKER"
echo "[sync-pstack] installed path=$DEST sha=$head_sha"
