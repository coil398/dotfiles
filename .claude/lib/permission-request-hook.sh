#!/usr/bin/env bash
# Shared permission hook launcher. Claude Code uses the default runtime;
# native adapters for other runtimes pass their runtime name explicitly.
set -u
SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd -P "${SCRIPT_DIR}/../.." && pwd)"
RUNTIME="${1:-claude}"
exec bash "${DOT_DIR}/jev-hooks/permission-launcher.sh" "$RUNTIME"
