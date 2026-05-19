#!/usr/bin/env bash
# Claude Code PostToolUse hook: lint shell scripts with shellcheck after edits.
#
# Fires after Edit / Write / MultiEdit. If the edited file is a shell script
# (*.sh extension or an sh/bash/dash/ksh shebang), runs shellcheck and feeds
# any findings back to Claude via additionalContext.
#
# Non-blocking by design: always exits 0. PostToolUse runs after the tool has
# already executed, so it cannot block anything -- it only surfaces lint
# findings for Claude to act on in the next turn.
#
# zsh is intentionally excluded: shellcheck does not support zsh scripts.

set -euo pipefail

# jq drives stdin parsing; if it is missing, silently no-op.
command -v jq >/dev/null 2>&1 || exit 0

input=$(cat)
file_path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
[ -z "$file_path" ] && exit 0

# Resolve to an absolute path.
case "$file_path" in
  /*)   abs="$file_path" ;;
  "~"*) abs="${file_path/#\~/$HOME}" ;;
  *)    abs="$(pwd)/$file_path" ;;
esac

# Resolve the containing directory's symlinks to a physical path.
abs_dir="$(dirname "$abs")"
abs_base="$(basename "$abs")"
if [ -d "$abs_dir" ]; then
  abs="$(cd -P "$abs_dir" 2>/dev/null && pwd)/$abs_base"
fi

[ -f "$abs" ] || exit 0

# Decide whether this is a shellcheck-supported shell script.
is_shell_script=0
case "$abs" in
  *.sh) is_shell_script=1 ;;
  *)
    first_line="$(head -n 1 "$abs" 2>/dev/null || true)"
    case "$first_line" in
      "#!"*bash*|"#!"*dash*|"#!"*ksh*)               is_shell_script=1 ;;
      "#!"*/sh|"#!"*/sh\ *|"#!"*"env sh"|"#!"*"env sh "*) is_shell_script=1 ;;
    esac
    ;;
esac
[ "$is_shell_script" -eq 0 ] && exit 0

# When shellcheck is absent, warn once and pass (mirrors the gitleaks dispatcher).
if ! command -v shellcheck >/dev/null 2>&1; then
  echo "[shellcheck-hook] warn: shellcheck not installed, skipping lint" >&2
  exit 0
fi

# Note: shellcheck exits non-zero when it finds issues; keep going regardless.
findings="$(shellcheck "$abs" 2>&1)" || true
[ -z "$findings" ] && exit 0

jq -nc --arg ctx "shellcheck flagged the shell script just edited (${abs}):

${findings}" '{
  hookSpecificOutput: {
    hookEventName: "PostToolUse",
    additionalContext: $ctx
  }
}'
exit 0
