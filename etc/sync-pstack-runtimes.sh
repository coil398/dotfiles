#!/bin/sh
# Register official pstack with Codex and Grok Build through their own plugin commands.
# Claude Code reads pstack from .claude/settings.json (link.sh deploys it) and Cursor is
# handled by sync-pstack.sh, so neither is touched here. Plugin and marketplace state stays
# runtime-owned: nothing is written into this checkout, and every failure is non-fatal.
set -eu

MARKETPLACE="${PSTACK_CODEX_MARKETPLACE:-cursor-plugins}"
MARKETPLACE_SOURCE="${PSTACK_MARKETPLACE_SOURCE:-cursor/plugins}"
GROK_SOURCE="${PSTACK_GROK_SOURCE:-cursor/plugins#pstack}"

if ! command -v timeout >/dev/null 2>&1; then
    echo "[sync-pstack-runtimes] skip reason=timeout_unavailable"
    exit 0
fi

bounded() {
    timeout 120 env GIT_TERMINAL_PROMPT=0 "$@"
}

sync_codex() {
    if ! command -v codex >/dev/null 2>&1; then
        echo "[sync-pstack-runtimes] codex skip reason=codex_unavailable"
        return 0
    fi
    if ! codex_marketplaces="$(bounded codex plugin marketplace list 2>/dev/null)"; then
        echo "[sync-pstack-runtimes] codex skip reason=marketplace_list_failed"
        return 0
    fi
    if printf '%s\n' "$codex_marketplaces" | grep -Eq "^${MARKETPLACE}[[:space:]]"; then
        if bounded codex plugin marketplace upgrade "$MARKETPLACE" >/dev/null 2>&1; then
            echo "[sync-pstack-runtimes] codex marketplace upgraded name=$MARKETPLACE"
        else
            echo "[sync-pstack-runtimes] codex marketplace upgrade_failed name=$MARKETPLACE preserved=1"
        fi
    elif bounded codex plugin marketplace add "$MARKETPLACE_SOURCE" >/dev/null 2>&1; then
        echo "[sync-pstack-runtimes] codex marketplace added source=$MARKETPLACE_SOURCE"
    else
        echo "[sync-pstack-runtimes] codex skip reason=marketplace_add_failed source=$MARKETPLACE_SOURCE"
        return 0
    fi
    if bounded codex plugin add "pstack@${MARKETPLACE}" >/dev/null 2>&1; then
        echo "[sync-pstack-runtimes] codex plugin installed name=pstack@${MARKETPLACE}"
    else
        echo "[sync-pstack-runtimes] codex plugin install_failed name=pstack@${MARKETPLACE}"
    fi
}

sync_grok() {
    if ! command -v grok >/dev/null 2>&1; then
        echo "[sync-pstack-runtimes] grok skip reason=grok_unavailable"
        return 0
    fi
    if ! grok_plugins="$(bounded grok plugin list 2>/dev/null)"; then
        echo "[sync-pstack-runtimes] grok skip reason=plugin_list_failed"
        return 0
    fi
    if printf '%s\n' "$grok_plugins" | grep -Eq '[[:space:]]pstack[[:space:]]+\['; then
        if bounded grok plugin update pstack >/dev/null 2>&1; then
            echo "[sync-pstack-runtimes] grok plugin updated name=pstack"
        else
            echo "[sync-pstack-runtimes] grok plugin update_failed name=pstack preserved=1"
        fi
    elif bounded grok plugin install "$GROK_SOURCE" --trust >/dev/null 2>&1; then
        echo "[sync-pstack-runtimes] grok plugin installed source=$GROK_SOURCE"
    else
        echo "[sync-pstack-runtimes] grok plugin install_failed source=$GROK_SOURCE"
    fi
}

sync_codex
sync_grok
