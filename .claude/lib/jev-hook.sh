#!/usr/bin/env bash
# Claude Code hook entry for optional Jev judgments.
#
# Registered in .claude/settings.json for Stop, UserPromptSubmit, PreToolUse,
# PostToolUse, PostToolUseFailure and SubagentStop. Resolves the dotfiles checkout from this
# file's physical location and hands the payload to jev-hooks/hook.sh, which
# returns {} without starting Python when TYPESAFE_API_KEY is unset.
# See jev-hooks/README.md.

set -eu

SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd -P "${SCRIPT_DIR}/../.." && pwd)"

exec sh "${DOT_DIR}/jev-hooks/hook.sh" claude
