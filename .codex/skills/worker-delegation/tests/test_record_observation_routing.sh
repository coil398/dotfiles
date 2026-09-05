#!/usr/bin/env bash

set -euo pipefail
umask 077

TEST_DIR="$(cd -- "$(dirname -- "$0")" && pwd -P)"
HELPER="$TEST_DIR/../scripts/record-observation.sh"
TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/worker-observation-routing.XXXXXX")"
export HOME="$TEST_ROOT/home"
mkdir -p "$HOME/.ai-pir-runs"
chmod 700 "$HOME" "$HOME/.ai-pir-runs"
HOME="$(cd -P "$HOME" && pwd -P)"
export HOME

cleanup() {
    if [ -n "${TEST_ROOT:-}" ] && [ -d "$TEST_ROOT" ]; then
        rm -rf "$TEST_ROOT"
    fi
}
trap cleanup EXIT HUP INT TERM

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    exit 1
}

RUN_DIR="$HOME/.ai-pir-runs/direct-sol"
"$HELPER" init --run-dir "$RUN_DIR"

write_attempt() {
    attempt_index="$1"
    attempt_model="$2"
    attempt_effort="$3"
    raw_output="$RUN_DIR/worker-output-${attempt_index}.md"
    provenance="$raw_output.provenance.tsv"
    printf '%s\n' \
        'ACTOR: sol' \
        "ACTUAL_MODEL: $attempt_model" \
        "ACTUAL_EFFORT: $attempt_effort" \
        'STATUS: completed' \
        'CHANGED_FILES: .codex/skills/example.md' \
        'OBSERVED_RESULTS: focused routing fixture' \
        'BLOCKERS: none' \
        'ESCALATION_REASON: measured local reasoning evidence' > "$raw_output"
    {
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
            started_at_utc ended_at_utc duration_ms actor model effort codex_exit validation_status
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
            2026-09-05T00:00:00Z 2026-09-05T00:00:01Z 1000 sol "$attempt_model" "$attempt_effort" 0 validated
    } > "$provenance"
}

record_attempt() {
    attempt_index="$1"
    escalation_from="$2"
    escalation_to="$3"
    escalation_reason="$4"
    insufficiency_class="$5"
    input_sufficient="$6"
    measured_ref="$7"
    write_attempt "$attempt_index" gpt-5.6-sol high
    raw_output="$RUN_DIR/worker-output-${attempt_index}.md"
    "$HELPER" worker \
        --run-dir "$RUN_DIR" \
        --raw-output "$raw_output" \
        --provenance "$raw_output.provenance.tsv" \
        --job-id routing --index "$attempt_index" --status completed \
        --sol-measurement-result accepted --mismatch match --mismatch-reason none \
        --escalation-from "$escalation_from" --escalation-to "$escalation_to" \
        --effort-escalation-from none --effort-escalation-to none \
        --escalation-reason "$escalation_reason" \
        --insufficiency-class "$insufficiency_class" \
        --input-sufficient "$input_sufficient" \
        --measured-insufficiency-ref "$measured_ref" \
        --task-ref task.md --requirements-ref requirements.md \
        --report-ref "implementation-${attempt_index}.md" \
        --changed-files-ref changed-files-${attempt_index}.txt \
        --verification-ref verification-${attempt_index}.txt
}

# expert can be selected directly by Astra without a preceding worker attempt.
record_attempt 01 none none none none not_applicable none

# A measured local-reasoning failure may route Luna directly to Sol.
record_attempt 02 luna sol measured-luna-local-reasoning local-reasoning yes evidence/luna-01.md

ledger="$RUN_DIR/worker-observations-v1.tsv"
awk -F '\t' '
    NR == 1 { for (i = 1; i <= NF; i++) column[$i] = i; next }
    NR == 2 && $(column["actor"]) == "sol" && $(column["actual_model"]) == "gpt-5.6-sol" &&
      $(column["actual_effort"]) == "high" && $(column["escalation_from"]) == "none" &&
      $(column["escalation_to"]) == "none" && $(column["automatic_fallback"]) == "no" { direct = 1 }
    NR == 3 && $(column["actor"]) == "sol" && $(column["escalation_from"]) == "luna" &&
      $(column["escalation_to"]) == "sol" && $(column["insufficiency_class"]) == "local-reasoning" &&
      $(column["input_sufficient"]) == "yes" && $(column["automatic_fallback"]) == "no" { measured = 1 }
    END { exit !(direct && measured) }
' "$ledger" || {
    sed -n '1,8p' "$ledger" >&2
    fail 'direct Sol selection or Luna-to-Sol routing was not recorded'
}

# The helper must reject an unsupported actor transition instead of inventing
# a fallback route or another ledger name.
write_attempt 03 gpt-5.6-sol high
invalid_error="$TEST_ROOT/invalid-transition.stderr"
if "$HELPER" worker \
    --run-dir "$RUN_DIR" \
    --raw-output "$RUN_DIR/worker-output-03.md" \
    --provenance "$RUN_DIR/worker-output-03.md.provenance.tsv" \
    --job-id routing --index 03 --status completed \
    --sol-measurement-result accepted --mismatch match --mismatch-reason none \
    --escalation-from sol --escalation-to sol \
    --effort-escalation-from none --effort-escalation-to none \
    --escalation-reason invalid-route --insufficiency-class local-reasoning \
    --input-sufficient yes --measured-insufficiency-ref evidence/invalid.md \
    --task-ref task.md --requirements-ref requirements.md \
    --report-ref implementation-03.md --changed-files-ref changed-files-03.txt \
    --verification-ref verification-03.txt 2>"$invalid_error"; then
    fail 'unsupported Sol-to-Sol transition unexpectedly succeeded'
fi

grep -Fq 'luna-to-sol' "$invalid_error" \
    || fail 'unsupported transition did not report the direct-routing validation rule'

[ "$(awk 'END { print NR }' "$ledger")" -eq 3 ] || fail 'invalid transition appended a ledger row'
printf '%s\n' 'OK: direct Sol selection and Luna-to-Sol routing are observed without fallback'
