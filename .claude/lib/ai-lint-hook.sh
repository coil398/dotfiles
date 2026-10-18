#!/usr/bin/env bash
# Advisory PostToolUse scanner; analysis failures never block the completed edit.

set -u
SCRIPT_DIR="$(builtin cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." 2>/dev/null && pwd)" || exit 0
exec python3 "${SCRIPT_DIR}/ai-lint/ai_lint.py" --hook claude
