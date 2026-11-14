#!/usr/bin/env bash
set -u
SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOTFILES="$(cd -P "${SCRIPT_DIR}/../../.." && pwd)"
exec bash "${DOTFILES}/jev-hooks/permission-launcher.sh" antigravity
