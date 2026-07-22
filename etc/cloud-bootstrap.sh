#!/bin/sh
# Bootstrap these dotfiles in a Claude Code on the web (cloud) session.
#
# Cross-repo auto-deploy: a repo-committed SessionStart hook can only deploy when
# a session is opened on THIS repo (other repos never clone dotfiles). To get the
# dotfiles into EVERY cloud session regardless of which repo it runs on, wire this
# script into the environment's *setup script* (Claude Code on the web ->
# environment settings). See docs:
#   https://code.claude.com/docs/en/claude-code-on-the-web
#
# Recommended setup-script line (dotfiles is a public repo, so no auth needed):
#   curl -fsSL https://raw.githubusercontent.com/coil398/dotfiles/master/etc/cloud-bootstrap.sh | sh
#
# It deploys via etc/link.sh, which symlinks the config into $HOME. link.sh
# derives its source tree from its own location, so the checkout need not live at
# ~/dotfiles literally.
#
# Source selection:
#   - If this session is opened ON the dotfiles repo, deploy FROM that in-place
#     checkout (the working tree you are editing) -- never re-clone a second copy
#     of master to lay on top of the repo you came here to work on.
#   - Otherwise clone/update a managed copy at ~/dotfiles and deploy from it.
#
# Overrides (env vars):
#   DOTFILES_DIR       force this checkout dir (skips detection & clone)
#   DOTFILES_REPO_URL  clone URL                (default: public HTTPS remote)
#   DOTFILES_BRANCH    branch to clone          (default: master)
#   DOTFILES_INSTALL   set to 1 to also run install.sh (apt/prebuilt tools);
#                      off by default because it needs sudo and is heavier than
#                      just laying down the config symlinks.
set -eu

REPO_URL="${DOTFILES_REPO_URL:-https://github.com/coil398/dotfiles.git}"
BRANCH="${DOTFILES_BRANCH:-master}"
DOT_DIRECTORY="${DOTFILES_DIR:-}"

is_dotfiles_checkout() {
    d="$1"
    [ -n "$d" ] && [ -f "$d/etc/link.sh" ] && [ -d "$d/.git" ] || return 1
    case "$(git -C "$d" remote get-url origin 2>/dev/null || echo)" in
        *coil398/dotfiles*) return 0 ;;
        *) return 1 ;;
    esac
}

# 1. Prefer an in-place checkout (a session opened on the dotfiles repo): deploy
#    from the working tree the user is actually editing, without touching it.
if [ -z "$DOT_DIRECTORY" ]; then
    for cand in "${CLAUDE_PROJECT_DIR:-}" "$PWD" /home/user/dotfiles; do
        if is_dotfiles_checkout "$cand"; then
            DOT_DIRECTORY="$cand"
            echo "[cloud-bootstrap] deploying from in-place checkout: $DOT_DIRECTORY"
            break
        fi
    done
fi

# 2. Otherwise clone/update a managed copy at ~/dotfiles.
if [ -z "$DOT_DIRECTORY" ]; then
    DOT_DIRECTORY="${HOME}/dotfiles"
    if [ -d "$DOT_DIRECTORY/.git" ]; then
        echo "[cloud-bootstrap] updating $DOT_DIRECTORY"
        git -C "$DOT_DIRECTORY" pull --ff-only origin "$BRANCH" \
            || echo "[cloud-bootstrap] warn: pull failed; deploying existing checkout"
    else
        echo "[cloud-bootstrap] cloning $REPO_URL -> $DOT_DIRECTORY"
        git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$DOT_DIRECTORY"
    fi
fi

if [ "${DOTFILES_INSTALL:-0}" = "1" ] && [ -f "$DOT_DIRECTORY/install.sh" ]; then
    echo "[cloud-bootstrap] running install.sh (DOTFILES_INSTALL=1)"
    bash "$DOT_DIRECTORY/install.sh" || echo "[cloud-bootstrap] warn: install.sh failed (non-fatal)"
fi

sh "$DOT_DIRECTORY/etc/link.sh"
echo "[cloud-bootstrap] done (source: $DOT_DIRECTORY)"
