#!/usr/bin/env bash

sync_hook_init() {
  local entry_script="$1"
  local producer_script="$2"
  local producer_label="$3"

  SYNC_HOOK_SCRIPT_DIR="$(cd -P "$(dirname "$entry_script")" && pwd)"
  SYNC_HOOK_DOT_DIR="$(cd -P "${SYNC_HOOK_SCRIPT_DIR}/../.." && pwd)"
  SYNC_HOOK_SYNC_SCRIPT="${SYNC_HOOK_DOT_DIR}/etc/${producer_script}"
  SYNC_HOOK_LABEL="$producer_label"
}

sync_hook_read_file_path() {
  local input

  input=$(cat)
  if ! SYNC_HOOK_FILE_PATH=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null); then
    return 1
  fi
  [ -n "$SYNC_HOOK_FILE_PATH" ]
}

sync_hook_resolve_path() {
  local abs="$1"
  local link_target
  local abs_dir
  local abs_base

  case "$abs" in
    /*) ;;
    ~*) abs="${abs/#\~/$HOME}" ;;
    *)  abs="$(pwd)/$abs" ;;
  esac

  # readlink without -f keeps this compatible with macOS; resolve each hop.
  while [ -L "$abs" ]; do
    link_target="$(readlink "$abs")"
    case "$link_target" in
      /*) abs="$link_target" ;;
      *)  abs="$(dirname "$abs")/$link_target" ;;
    esac
  done
  abs_dir="$(dirname "$abs")"
  abs_base="$(basename "$abs")"
  # A new file may have a missing parent; leave it unresolved for a no-op match.
  if [ -d "$abs_dir" ]; then
    abs="$(cd -P "$abs_dir" 2>/dev/null && pwd)/$abs_base"
  fi
  SYNC_HOOK_ABS_PATH="$abs"
}

sync_hook_emit_result() {
  local status="$1"
  local output="$2"
  local context

  if [ "$status" -eq 0 ]; then
    context="[${SYNC_HOOK_LABEL}-hook] sync completed: ${SYNC_HOOK_SYNC_SCRIPT}"
  else
    context="[${SYNC_HOOK_LABEL}-hook] sync failed (exit ${status}): ${SYNC_HOOK_SYNC_SCRIPT}"
  fi
  if [ -n "$output" ]; then
    context+=$'\n'
    context+="$output"
  fi

  jq -nc --arg ctx "$context" '{
    hookSpecificOutput: {
      hookEventName: "PostToolUse",
      additionalContext: $ctx
    }
  }'
}
