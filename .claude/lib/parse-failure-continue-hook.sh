#!/usr/bin/env bash
#
# Stop hook: auto-continue after a tool-call parse failure.
#
# When the model emits a malformed tool_use the harness records a terminal
# error containing "could not be parsed" and the turn ends, leaving the session
# stuck. The single most common cause observed is a stray preamble token (e.g.
# the literal word "court") or other text/whitespace before the <invoke> tag;
# other causes are multiple simultaneous invokes or heredoc-bearing params.
# This hook detects that terminal error and returns a block decision so the
# model re-issues the tool call cleanly instead of stopping.
#
# Loop safety:
#   A previous version capped auto-continue at ONE attempt via stop_hook_active.
#   That was too aggressive: when the malform RECURS on the forced retry, the
#   cap gives up and the session stops anyway (the exact "court keeps stopping
#   me" symptom). Instead we COUNT recent parse-failures in the transcript tail
#   and keep forcing a clean re-issue up to MAX_RETRIES, only giving up past
#   that to avoid a genuine infinite loop.
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

# Without a readable transcript we cannot judge -> allow the stop.
if [ -z "${transcript_path:-}" ] || [ ! -f "$transcript_path" ]; then
  printf '%s allow-stop: no transcript (path=%s)\n' "$(now)" "${transcript_path:-}" >>"$log_file" 2>/dev/null || true
  allow_stop
fi

last_line="$(tail -n1 "$transcript_path" 2>/dev/null)"

# The harness records parse failures as a terminal user-role message, e.g.
#   "Your tool call was malformed and could not be parsed. Please retry."
#   "The model's tool call could not be parsed (retry also failed)."
# The cause-agnostic substring "could not be parsed" is the matcher.
signature='could not be parsed'

{
  printf '%s ---- Stop hook fired ----\n' "$(now)"
  printf '  transcript=%s\n' "$transcript_path"
  printf '  last_line=%s\n' "$last_line"
} >>"$log_file" 2>/dev/null || true

case "$last_line" in
  *"$signature"*)
    # Count recent parse-failures so a recurring malform keeps getting a forced
    # clean re-issue, while a genuinely stuck loop still terminates.
    pf_count="$(tail -n 80 "$transcript_path" 2>/dev/null | grep -c "$signature")"
    : "${pf_count:=0}"
    max_retries=15
    if [ "$pf_count" -ge "$max_retries" ]; then
      printf '%s allow-stop: %s parse-failures >= %s (give up to avoid infinite loop)\n' "$(now)" "$pf_count" "$max_retries" >>"$log_file" 2>/dev/null || true
      allow_stop
    fi
    reason='直前のターンはツール呼び出しのパースに失敗して中断した（tool call could not be parsed）。最頻原因は invoke 開始タグの前に余分なトークン（例 court）や前置きテキスト・空白が混入すること。最初からやり直す必要はない。次の規律で直前のツール呼び出しを再発行し中断作業を継続せよ: (1) 応答の先頭文字を invoke 開始タグにする。タグより前に文字も空白も単語も一切置かない。(2) 説明の地の文が必要ならツール呼び出しの後に書く。(3) 1 ターンの発行は最小限かつ正しい形式で。'
    printf '%s BLOCK: parse-failure (#%s) -> continue\n' "$(now)" "$pf_count" >>"$log_file" 2>/dev/null || true
    printf '{"decision":"block","reason":"%s"}\n' "$reason"
    exit 0
    ;;
esac

printf '%s allow-stop: no parse-failure signature on last line\n' "$(now)" >>"$log_file" 2>/dev/null || true
allow_stop
