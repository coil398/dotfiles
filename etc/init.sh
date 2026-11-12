#!/bin/sh

DOT_DIRECTORY="${DOTFILES_DIR:-${HOME}/dotfiles}"
DOT_TARBALL="https://github.com/coil398/dotfiles/tarball/master"
GIT_URL="https://github.com/coil398/dotfiles"

if [ ! -d "$DOT_DIRECTORY" ];then
    echo 'Downloading dotfiles...'
    mkdir "$DOT_DIRECTORY"

    if type "git" > /dev/null 2>&1; then
        git clone --recursive "${GIT_URL}" "${DOT_DIRECTORY}"
    else
        curl -fsSLo ${HOME}/dotfiles.tar.gz ${DOT_TARBALL}
        tar -zxf ${HOME}/dotfiles.tar.gz --strip-components 1 -C ${DOT_DIRECTORY}
        rm -f ${HOME}/dotfiles.tar.gz
    fi

    echo "Download finished."
fi

export DOTFILES_DIR="$DOT_DIRECTORY"
export PRIVATE_SKILLS_DIR="${PRIVATE_SKILLS_DIR:-$(dirname "$DOT_DIRECTORY")/private-skills}"
sh "$DOT_DIRECTORY/etc/sync-private-skills.sh" "$DOT_DIRECTORY" \
    || echo "[init] private acquisition failed: public deployment continues"

"${DOT_DIRECTORY}/etc/install/homebrew/install.sh" || {
    status=$?
    echo "[init] homebrew installation failed: exit ${status}" >&2
    exit "$status"
}
"${DOT_DIRECTORY}/etc/set.sh" || {
    status=$?
    echo "[init] settings setup failed: exit ${status}" >&2
    exit "$status"
}
"${DOT_DIRECTORY}/etc/link.sh" || {
    status=$?
    echo "[init] dotfile linking failed: exit ${status}" >&2
    exit "$status"
}
"${DOT_DIRECTORY}/etc/sync-mcp.sh" ||
    echo "[init] MCP sync failed: optional user-scope configuration was not updated" >&2
