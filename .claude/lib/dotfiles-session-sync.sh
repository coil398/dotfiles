#!/usr/bin/env bash
# Session-start hook shared by every AI runtime.
#
# Starts etc/dotfiles-autosync.sh in the background so each machine picks up
# the settings pushed from other machines and publishes its own local changes.
# The hook itself returns immediately and prints nothing, because some
# runtimes parse hook stdout and all of them wait for the hook to exit.
#
# Engine output goes to ${STATE_DIR}/last.log and the result to
# ${STATE_DIR}/status. On failure (conflict, push rejection, ...) a desktop
# notification is shown where the platform provides one.

set -u

SCRIPT_PATH="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
DOT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")/../.." && pwd)"
ENGINE="${DOT_DIR}/etc/dotfiles-autosync.sh"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/dotfiles-autosync"
LOCK_DIR="${STATE_DIR}/lock"

notify_failure() {
  local message="$1"
  if command -v osascript >/dev/null 2>&1; then
    osascript -e "display notification \"${message}\" with title \"dotfiles sync failed\"" >/dev/null 2>&1 || true
  elif command -v notify-send >/dev/null 2>&1; then
    notify-send "dotfiles sync failed" "$message" >/dev/null 2>&1 || true
  fi
}

# A lock left by a crashed run is reclaimed when its PID is no longer alive.
acquire_lock() {
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    printf '%s\n' "$$" > "${LOCK_DIR}/pid"
    return 0
  fi
  local holder
  holder="$(cat "${LOCK_DIR}/pid" 2>/dev/null || true)"
  if [ -n "$holder" ] && kill -0 "$holder" 2>/dev/null; then
    return 1
  fi
  rm -rf "$LOCK_DIR"
  mkdir "$LOCK_DIR" 2>/dev/null || return 1
  printf '%s\n' "$$" > "${LOCK_DIR}/pid"
}

run_sync() {
  acquire_lock || exit 0
  trap 'rm -rf "$LOCK_DIR"' EXIT

  # Fail instead of waiting for a credential prompt nobody can answer.
  export GIT_TERMINAL_PROMPT=0
  export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -o BatchMode=yes}"

  local status=0
  {
    printf 'started %s\n' "$(date '+%Y-%m-%d %H:%M:%S')"
    bash "$ENGINE" "$DOT_DIR" || status=$?
    printf 'finished %s exit=%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$status"
  } > "${STATE_DIR}/last.log" 2>&1

  if [ "$status" -eq 0 ]; then
    printf 'SUCCESS %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" > "${STATE_DIR}/status"
  else
    printf 'FAILED %s exit=%s log=%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$status" "${STATE_DIR}/last.log" > "${STATE_DIR}/status"
    notify_failure "See ${STATE_DIR}/last.log"
  fi
}

[ -f "$ENGINE" ] || exit 0
mkdir -p "$STATE_DIR" || exit 0

if [ "${1:-}" = "--run" ]; then
  run_sync
  exit 0
fi

# Hook mode: detach from the runtime's stdin/stdout so it does not wait for the sync.
nohup bash "$SCRIPT_PATH" --run </dev/null >/dev/null 2>&1 &
exit 0
