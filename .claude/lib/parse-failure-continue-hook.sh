#!/usr/bin/env bash
#
# Stop hook: auto-continue after an unrecoverable tool-call parse failure.
#
# When the model emits a malformed tool_use and the harness's own retry also
# fails, the turn ends with the harness error:
#
#   The model's tool call could not be parsed (retry also failed)
#
# leaving the session stuck waiting for manual input. This Stop hook inspects
# the transcript's terminal entry; if it is that parse-failure error it returns
# a block decision so Claude re-issues the tool call instead of stopping.
#
# Safety:
#   - stop_hook_active is the loop guard: when we are already continuing because
#     of a previous Stop-hook block we do NOT block again, capping auto-continue
#     at one attempt per stuck point.
#   - Every invocation appends a debug record to the log so the real transcript
#     structure can be verified against a genuine failure and the matcher tuned.
#
# Input  (stdin, JSON): session_id, transcript_path, stop_hook_active, cwd, ...
# Output (stdout, JSON): {"decision":"block","reason":"..."} to force continue;
#                        empty + exit 0 to allow the stop.

set -u

log_dir="$HOME/.claude/logs"
log_file="$log_dir/parse-failure-continue-hook.log"
mkdir -p "$log_dir" 2>/dev/null || true

now() { date '+%Y-%m-%dT%H:%M:%S'; }
allow_stop() { exit 0; }

input="$(cat)"

transcript_path="$(printf '%s' "$input" \
  | grep -Eo '"transcript_path"[[:space:]]*:[[:space:]]*"[^"]*"' \
  | head -n1 \
  | sed -E 's/^.*:[[:space:]]*"//; s/"$//')"

stop_hook_active="$(printf '%s' "$input" \
  | grep -Eo '"stop_hook_active"[[:space:]]*:[[:space:]]*(true|false)' \
  | grep -Eo 'true|false' \
  | head -n1)"

# Loop guard: never block twice in a row for the same stuck point.
if [ "${stop_hook_active:-false}" = "true" ]; then
  printf '%s allow-stop: stop_hook_active=true (loop guard)\n' "$(now)" >>"$log_file" 2>/dev/null || true
  allow_stop
fi

# Without a readable transcript we cannot judge -> allow the stop.
if [ -z "${transcript_path:-}" ] || [ ! -f "$transcript_path" ]; then
  printf '%s allow-stop: no transcript (path=%s)\n' "$(now)" "${transcript_path:-}" >>"$log_file" 2>/dev/null || true
  allow_stop
fi

last_line="$(tail -n1 "$transcript_path" 2>/dev/null)"

{
  printf '%s ---- Stop hook fired ----\n' "$(now)"
  printf '  stop_hook_active=%s\n' "${stop_hook_active:-}"
  printf '  transcript=%s\n' "$transcript_path"
  printf '  last_line=%s\n' "$last_line"
} >>"$log_file" 2>/dev/null || true

# The verbatim harness text emitted on an unrecoverable tool-call parse failure.
signature='tool call could not be parsed (retry also failed)'

case "$last_line" in
  *"$signature"*)
    reason='直前のターンはツール呼び出しのパースに失敗して中断した（tool call could not be parsed / retry also failed）。原因はツール呼び出しの整形崩れ（複数 invoke の同時発行・heredoc を含むパラメータ・余分な前置きトークン等）の可能性が高い。作業を最初からやり直す必要はない。直前に試みたツール呼び出しを、1 回につき 1 つだけ・前置きテキストを最小化して正しい形式で再発行し、中断した作業を継続せよ。'
    printf '%s BLOCK: parse-failure detected -> continue\n' "$(now)" >>"$log_file" 2>/dev/null || true
    printf '{"decision":"block","reason":"%s"}\n' "$reason"
    exit 0
    ;;
esac

printf '%s allow-stop: no parse-failure signature on last line\n' "$(now)" >>"$log_file" 2>/dev/null || true
allow_stop
