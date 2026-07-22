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
# It clones (or updates) the repo into ~/dotfiles and runs etc/link.sh, which
# symlinks the config into $HOME. link.sh derives its source tree from its own
# location, so the checkout does not have to live at ~/dotfiles literally.
#
# Overrides (env vars):
#   DOTFILES_DIR       target checkout dir      (default: $HOME/dotfiles)
#   DOTFILES_REPO_URL  clone URL                (default: public HTTPS remote)
#   DOTFILES_BRANCH    branch to deploy         (default: master)
#   DOTFILES_INSTALL   set to 1 to also run install.sh (apt/prebuilt tools);
#                      off by default because it needs sudo and is heavier than
#                      just laying down the config symlinks.
set -eu

DOT_DIRECTORY="${DOTFILES_DIR:-${HOME}/dotfiles}"
REPO_URL="${DOTFILES_REPO_URL:-https://github.com/coil398/dotfiles.git}"
BRANCH="${DOTFILES_BRANCH:-master}"

if [ -d "$DOT_DIRECTORY/.git" ]; then
    echo "[cloud-bootstrap] updating $DOT_DIRECTORY"
    git -C "$DOT_DIRECTORY" pull --ff-only origin "$BRANCH" \
        || echo "[cloud-bootstrap] warn: pull failed; deploying existing checkout"
else
    echo "[cloud-bootstrap] cloning $REPO_URL -> $DOT_DIRECTORY"
    git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$DOT_DIRECTORY"
fi

if [ "${DOTFILES_INSTALL:-0}" = "1" ] && [ -f "$DOT_DIRECTORY/install.sh" ]; then
    echo "[cloud-bootstrap] running install.sh (DOTFILES_INSTALL=1)"
    bash "$DOT_DIRECTORY/install.sh" || echo "[cloud-bootstrap] warn: install.sh failed (non-fatal)"
fi

sh "$DOT_DIRECTORY/etc/link.sh"
echo "[cloud-bootstrap] done"
