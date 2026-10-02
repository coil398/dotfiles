#!/bin/sh
# Optional acquisition shared by the normal and cloud bootstrap entrypoints.
set -eu
DOT_DIRECTORY="${1:-${DOTFILES_DIR:-${HOME}/dotfiles}}"

# Private skills are optional and live beside the public checkout. Never change
# an existing dirty source or replace a checkout when its update fails.
PRIVATE_DIRECTORY="${PRIVATE_SKILLS_DIR:-$(dirname "$DOT_DIRECTORY")/private-skills}"
PRIVATE_URL="${PRIVATE_SKILLS_REPO_URL:-git@github.com:coil398/private-skills.git}"
if ! command -v timeout >/dev/null 2>&1; then
    echo "[sync-private-skills] private update skipped: timeout unavailable"
elif [ -e "$PRIVATE_DIRECTORY" ]; then
    if [ ! -d "$PRIVATE_DIRECTORY" ] || [ "$(git -C "$PRIVATE_DIRECTORY" rev-parse --show-toplevel 2>/dev/null || true)" != "$(cd "$PRIVATE_DIRECTORY" && pwd -P)" ]; then
        echo "[sync-private-skills] private update skipped: existing path is not a checkout"
    elif ! private_status="$(git -C "$PRIVATE_DIRECTORY" status --porcelain)"; then
        echo "[sync-private-skills] private update skipped: checkout status unavailable"
    elif [ -n "$private_status" ]; then
        echo "[sync-private-skills] private update skipped: dirty checkout preserved"
    elif ! git -C "$PRIVATE_DIRECTORY" rev-parse --verify '@{upstream}' >/dev/null 2>&1; then
        echo "[sync-private-skills] private update skipped: no existing upstream"
    elif ! timeout 60 env GIT_TERMINAL_PROMPT=0 \
        GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh} -o BatchMode=yes -o ConnectTimeout=10" \
        git -C "$PRIVATE_DIRECTORY" pull --no-rebase --ff-only; then
        echo "[sync-private-skills] private update failed: existing checkout preserved"
    fi
else
    private_clone_stage="$(mktemp -d "$(dirname "$PRIVATE_DIRECTORY")/.private-skills-fetch.XXXXXX")" || private_clone_stage=""
    if [ -n "$private_clone_stage" ]; then
        if timeout 60 env GIT_TERMINAL_PROMPT=0 \
            GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh} -o BatchMode=yes -o ConnectTimeout=10" \
            git clone "$PRIVATE_URL" "$private_clone_stage/checkout" \
            && mv "$private_clone_stage/checkout" "$PRIVATE_DIRECTORY"; then
            echo "[sync-private-skills] private checkout acquired"
        else
            echo "[sync-private-skills] private acquisition failed: public deployment continues"
        fi
        rm -rf "$private_clone_stage"
    else
        echo "[sync-private-skills] private acquisition skipped: staging directory unavailable"
    fi
fi
