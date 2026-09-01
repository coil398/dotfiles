#!/usr/bin/env bash
# Audit skill/agent layout for the launch directory and this dotfiles repo.
# Usage: bash etc/audit-skill-agent-layout.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CWD="${1:-$(pwd)}"

exec python3 "${SCRIPT_DIR}/audit-skill-agent-layout.py" --cwd "$CWD" --dotfiles "$DOT_DIR"
