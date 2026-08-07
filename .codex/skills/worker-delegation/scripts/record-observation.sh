#!/bin/sh

# Append-only run observability helper.  The runner owns provenance values;
# callers may only provide job/evidence metadata.  Keep all files private by
# default and fail closed on paths or values that could change TSV structure.
umask 077
set -eu

SCRIPT_NAME=$(basename "$0")
ARTIFACT_SUBDIR='.ai-pir-runs'

WORKER_HEADER='schema_version	record_type	record_id	run_id	job_id	attempt_id	attempt_seq	actor	actual_model	actual_effort	started_at_utc	ended_at_utc	duration_ms	result	exit_code	validation_status	self_report_result	sol_measurement_result	mismatch	mismatch_reason	escalation_from	escalation_to	escalation_reason	effort_escalation_from	effort_escalation_to	automatic_fallback	insufficiency_class	input_sufficient	measured_insufficiency_ref	task_ref	requirements_ref	report_ref	changed_files_ref	verification_ref	observed_at_utc	notes'
ACCEPTANCE_HEADER='schema_version	record_type	record_id	run_id	job_id	attempt_id	acceptance_id	requirement_id	verdict	evidence_ref	evidence_summary	acceptance_basis	worker_self_report_result	worker_exit_code	sol_observed_at_utc	notes'
VERDICT_HEADER='schema_version	record_type	record_id	run_id	target_attempt_id	verdict_id	cycle	source_role	actual_model	actual_effort	started_at_utc	ended_at_utc	verdict	evidence_ref	evidence_summary	sol_acceptance_ref	notes'
PROVENANCE_HEADER=$(printf 'started_at_utc\tended_at_utc\tduration_ms\tactor\tmodel\teffort\tcodex_exit\tvalidation_status')
TAB_CHAR=$(printf '\t')
CR_CHAR=$(printf '\r')
NEWLINE_CHAR=$(printf '\nX')
NEWLINE_CHAR=${NEWLINE_CHAR%X}

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 2
}

usage() {
    cat >&2 <<EOF
Usage:
  $SCRIPT_NAME init --run-dir DIR
  $SCRIPT_NAME worker --run-dir DIR --raw-output FILE --provenance FILE --job-id ID --index ATTEMPT_KEY --status completed|blocked|failed --sol-measurement-result accepted|rejected|blocked --mismatch match|mismatch|not_comparable --mismatch-reason TEXT --escalation-from none|luna|terra|sol --escalation-to none|terra|sol --effort-escalation-from none|high|max --effort-escalation-to none|high|max --escalation-reason TEXT --insufficiency-class CLASS --input-sufficient yes|no|not_applicable --measured-insufficiency-ref REF [options]
  $SCRIPT_NAME acceptance --run-dir DIR --job-id ID --index N --requirement-id Rn --verdict PASS|FAIL --evidence-ref PATH [options]
  $SCRIPT_NAME verdict --run-dir DIR --job-id ID --target-attempt-index ATTEMPT_KEY --cycle REVIEW_INDEX|TEST_INDEX --role correctness|consistency|quality|security|architecture|tester --verdict PASS|FAIL --report-ref PATH --model MODEL --effort high|max --evidence-ref PATH [options]

All commands write below the real, non-symlink \$HOME/.ai-pir-runs artifact root.
EOF
    exit 2
}

command_name=${1-}
[ -n "$command_name" ] || usage
shift

contains_unsafe_value() {
    case "$1" in
        *"$TAB_CHAR"*|*"$NEWLINE_CHAR"*|*"$CR_CHAR"*|*'\\t'*) return 0 ;;
        *) return 1 ;;
    esac
}

safe_value() {
    [ -n "$2" ] || die "$1 must not be empty"
    contains_unsafe_value "$2" && die "$1 must not contain tab, newline, or CR"
    return 0
}

require_abs_path() {
    case "$1" in
        /*) ;;
        *) die "$2 must be an absolute path: $1" ;;
    esac
}

stat_identity() {
    if stat -c '%d %i %u %a' "$1" 2>/dev/null; then
        return 0
    fi
    stat -f '%d %i %u %Lp' "$1" 2>/dev/null || return 1
}

secure_identity() {
    secure_path=$1
    secure_label=$2
    [ ! -L "$secure_path" ] || die "$secure_label must not be a symlink: $secure_path"
    [ -e "$secure_path" ] || die "$secure_label does not exist: $secure_path"
    secure_record=$(stat_identity "$secure_path") || die "could not inspect $secure_label: $secure_path"
    secure_uid=$(printf '%s\n' "$secure_record" | awk '{ print $3 }')
    secure_mode=$(printf '%s\n' "$secure_record" | awk '{ print $4 }')
    [ "$secure_uid" = "$current_uid" ] || die "$secure_label is not owned by current UID: $secure_path"
    secure_mode_decimal=$(printf '%d' "0$secure_mode") || die "invalid mode for $secure_label: $secure_path"
    [ $((secure_mode_decimal & 18)) -eq 0 ] || die "$secure_label is group/world writable: $secure_path"
    printf '%s\n' "$secure_record"
}

secure_file_identity() {
    secure_file_path=$1
    secure_file_label=$2
    [ -f "$secure_file_path" ] || die "$secure_file_label must be a regular file: $secure_file_path"
    secure_identity "$secure_file_path" "$secure_file_label"
}

current_uid=$(id -u 2>/dev/null) || die 'could not determine current UID'
home_path=${HOME-}
[ -n "$home_path" ] || die 'HOME is required'
require_abs_path "$home_path" HOME
artifact_root="$home_path/$ARTIFACT_SUBDIR"
[ -d "$artifact_root" ] || die "standard artifact root is missing: $artifact_root"
[ ! -L "$artifact_root" ] || die "standard artifact root must not be a symlink: $artifact_root"
artifact_root_physical=$(cd -P "$artifact_root" 2>/dev/null && pwd -P) || die "could not canonicalize artifact root: $artifact_root"
[ "$artifact_root_physical" = "$artifact_root" ] || {
    # An ancestor alias (for example /var -> /private/var) is acceptable, but
    # the artifact-root entry itself must remain a real directory.
    [ -d "$artifact_root_physical" ] || die "artifact root is not a directory: $artifact_root"
}
artifact_root_identity=$(secure_identity "$artifact_root_physical" 'artifact root')

path_has_symlink_below_root() {
    candidate=$1
    root=$2
    case "$candidate" in
        "$root") remainder='' ;;
        "$root"/*) remainder=${candidate#"$root"/} ;;
        *) return 1 ;;
    esac
    current=$root
    while [ -n "$remainder" ]; do
        case "$remainder" in
            */*) component=${remainder%%/*}; remainder=${remainder#*/} ;;
            *) component=$remainder; remainder='' ;;
        esac
        [ -n "$component" ] || continue
        current="$current/$component"
        [ ! -L "$current" ] || return 0
    done
    return 1
}

path_has_symlink_into_root() {
    candidate=$1
    root_physical=$2
    remainder=${candidate#/}
    lexical_current=''
    while [ -n "$remainder" ]; do
        case "$remainder" in
            */*) component=${remainder%%/*}; remainder=${remainder#*/} ;;
            *) component=$remainder; remainder='' ;;
        esac
        [ -n "$component" ] || continue
        lexical_current="${lexical_current}/$component"
        [ ! -L "$lexical_current" ] || {
            resolved_component=$(cd -P "$lexical_current" 2>/dev/null && pwd -P) || return 0
            case "$resolved_component" in
                "$root_physical"|"$root_physical"/*) return 0 ;;
            esac
        }
    done
    return 1
}

run_dir=''
run_dir_physical=''
run_chain_records=''

capture_directory_chain() {
    chain_root=$1
    chain_leaf=$2
    case "$chain_leaf" in
        "$chain_root") chain_remainder='' ;;
        "$chain_root"/*) chain_remainder=${chain_leaf#"$chain_root"/} ;;
        *) die "run-dir is outside standard artifact root: $chain_leaf" ;;
    esac
    chain_current=$chain_root
    chain_records="$(printf '%s|%s\n' "$chain_current" "$(secure_identity "$chain_current" 'artifact root component')")"
    while [ -n "$chain_remainder" ]; do
        case "$chain_remainder" in
            */*) chain_component=${chain_remainder%%/*}; chain_remainder=${chain_remainder#*/} ;;
            *) chain_component=$chain_remainder; chain_remainder='' ;;
        esac
        [ -n "$chain_component" ] || continue
        chain_current="$chain_current/$chain_component"
        chain_records="${chain_records}
$(printf '%s|%s\n' "$chain_current" "$(secure_identity "$chain_current" 'run-dir component')")"
    done
    run_chain_records=$chain_records
}

validate_directory_chain() {
    chain_phase=$1
    artifact_actual_identity=$(secure_identity "$artifact_root_physical" "$chain_phase artifact root")
    [ "$artifact_actual_identity" = "$artifact_root_identity" ] || die "$chain_phase detected artifact-root identity change"
    while IFS='|' read -r chain_path chain_expected; do
        [ -n "$chain_path" ] || continue
        chain_actual=$(secure_identity "$chain_path" "$chain_phase run-dir component")
        [ "$chain_actual" = "$chain_expected" ] || die "$chain_phase detected run-dir identity change: $chain_path"
    done <<EOF
$run_chain_records
EOF
}

ensure_run_dir() {
    [ -n "$run_dir" ] || die '--run-dir is required'
    require_abs_path "$run_dir" '--run-dir'
    safe_value '--run-dir' "$run_dir"
    safe_value '--run-dir basename' "$(basename "$run_dir")"
    case "$run_dir" in
        "$artifact_root"|"$artifact_root"/*) ;;
        *)
            # Permit a physical ancestor alias while preserving the same
            # artifact-root boundary.
            candidate_parent=$(dirname "$run_dir")
            candidate_parent_physical=$(cd -P "$candidate_parent" 2>/dev/null && pwd -P) || die "run-dir parent does not exist: $candidate_parent"
            case "$candidate_parent_physical" in
                "$artifact_root_physical"|"$artifact_root_physical"/*) ;;
                *) die "run-dir must be below $artifact_root" ;;
            esac
            ;;
    esac
    path_has_symlink_below_root "$run_dir" "$artifact_root" && die "run-dir contains a symlink component: $run_dir" || true
    path_has_symlink_into_root "$run_dir" "$artifact_root_physical" && die "run-dir contains a symlink component: $run_dir" || true
    [ ! -L "$run_dir" ] || die "run-dir must not be a symlink: $run_dir"

    if [ ! -e "$run_dir" ]; then
        parent_dir=$(dirname "$run_dir")
        [ -d "$parent_dir" ] || die "run-dir parent does not exist: $parent_dir"
        [ ! -L "$parent_dir" ] || die "run-dir parent must not be a symlink: $parent_dir"
        parent_dir_physical=$(cd -P "$parent_dir" 2>/dev/null && pwd -P) || die "could not canonicalize run-dir parent: $parent_dir"
        capture_directory_chain "$artifact_root_physical" "$parent_dir_physical"
        (umask 077; mkdir "$run_dir") || die "could not create run-dir: $run_dir"
    fi
    [ -d "$run_dir" ] || die "run-dir is not a directory: $run_dir"
    [ ! -L "$run_dir" ] || die "run-dir must not be a symlink: $run_dir"
    run_dir_physical=$(cd -P "$run_dir" 2>/dev/null && pwd -P) || die "could not canonicalize run-dir: $run_dir"
    case "$run_dir_physical" in
        "$artifact_root_physical"/*) ;;
        *) die "run-dir is outside standard artifact root: $run_dir" ;;
    esac
    capture_directory_chain "$artifact_root_physical" "$run_dir_physical"
    validate_directory_chain pre-operation
}

ledger_path() {
    case "$1" in
        worker) printf '%s\n' "$run_dir_physical/worker-observations-v1.tsv" ;;
        acceptance) printf '%s\n' "$run_dir_physical/sol-acceptance-v1.tsv" ;;
        verdict) printf '%s\n' "$run_dir_physical/independent-verdicts-v1.tsv" ;;
        *) die "unknown ledger: $1" ;;
    esac
}

ensure_ledger() {
    ledger_kind=$1
    ledger_file=$(ledger_path "$ledger_kind")
    case "$ledger_kind" in
        worker) expected_header=$WORKER_HEADER ;;
        acceptance) expected_header=$ACCEPTANCE_HEADER ;;
        verdict) expected_header=$VERDICT_HEADER ;;
    esac
    if [ -e "$ledger_file" ] || [ -L "$ledger_file" ]; then
        [ ! -L "$ledger_file" ] || die "ledger must not be a symlink: $ledger_file"
        [ -f "$ledger_file" ] || die "ledger is not a regular file: $ledger_file"
        ledger_identity_before=$(secure_file_identity "$ledger_file" 'ledger')
        actual_header=$(sed -n '1p' "$ledger_file") || die "could not read ledger: $ledger_file"
        [ "$actual_header" = "$expected_header" ] || die "ledger header mismatch: $ledger_file"
        ledger_identity_after=$(secure_file_identity "$ledger_file" 'ledger')
        [ "$ledger_identity_before" = "$ledger_identity_after" ] || die "ledger identity changed while reading: $ledger_file"
    else
        (umask 077; set -C; printf '%s\n' "$expected_header" > "$ledger_file") || die "could not create ledger: $ledger_file"
        secure_file_identity "$ledger_file" 'ledger' >/dev/null
    fi
    printf '%s\n' "$ledger_file"
}

append_row() {
    destination=$1
    shift
    row=$*
    # POSIX shell double quotes do not expand ``\t``.  Row templates use that
    # readable marker, so materialize it as a literal tab exactly once before
    # validating and appending.
    row=$(printf '%s' "$row" | sed "s/\\\\t/$TAB_CHAR/g")
    case "$row" in
        *"$NEWLINE_CHAR"*|*"$CR_CHAR"*) die 'record contains newline or CR' ;;
    esac
    destination_identity_before=$(secure_file_identity "$destination" 'ledger')
    # The ledger was opened and header-checked above.  Append only; never
    # rewrite or truncate an existing run record.
    printf '%s\n' "$row" >> "$destination" || die "could not append ledger: $destination"
    destination_identity_after=$(secure_file_identity "$destination" 'ledger')
    [ "$destination_identity_before" = "$destination_identity_after" ] || die 'ledger identity changed while appending'
}

ensure_record_id_unique() {
    destination=$1
    record_id_to_check=$2
    if awk -F '\t' -v wanted="$record_id_to_check" 'NR > 1 && $3 == wanted { found = 1 } END { exit found ? 0 : 1 }' "$destination"; then
        die "record_id already exists: $record_id_to_check"
    fi
}

derive_run_id() {
    basename "$run_dir_physical"
}

validate_id() {
    value=$2
    safe_value "$1" "$value"
    case "$value" in
        *[!A-Za-z0-9._:-]*) die "$1 contains invalid identifier characters" ;;
    esac
}

# A worker attempt is keyed by its two-digit implementation index plus an
# optional explicit execution suffix.  This prevents shard/correction/unit
# reports from collapsing into their parent implementation attempt.
validate_attempt_key() {
    value=$2
    validate_id "$1" "$value"
    case "$value" in
        [0-9][0-9]|[0-9][0-9]-shard-[A-Za-z0-9._]*|[0-9][0-9]-review-fix-[A-Za-z0-9._]*|[0-9][0-9]-unit-[A-Za-z0-9._]*) ;;
        *) die "$1 must be a two-digit index or a safe -shard-/-review-fix-/-unit- attempt key" ;;
    esac
    case "$value" in *-) die "$1 suffix must not be empty" ;; esac
}

validate_cycle() {
    value=$2
    case "$value" in [0-9][0-9]) ;; *) die "$1 must be a two-digit review/test cycle" ;; esac
}

init_ledgers() {
    init_run_dir=''
    while [ "$#" -gt 0 ]; do
        case "$1" in
            --run-dir) [ "$#" -ge 2 ] || usage; init_run_dir=$2; shift 2 ;;
            *) usage ;;
        esac
    done
    run_dir=$init_run_dir
    ensure_run_dir
    ensure_ledger worker >/dev/null
    ensure_ledger acceptance >/dev/null
    ensure_ledger verdict >/dev/null
}

parse_provenance() {
    provenance_file=$1
    [ -f "$provenance_file" ] || die "provenance sidecar is missing: $provenance_file"
    [ ! -L "$provenance_file" ] || die 'provenance sidecar must not be a symlink'
    sidecar_header=$(sed -n '1p' "$provenance_file") || die 'could not read provenance sidecar'
    [ "$sidecar_header" = "$PROVENANCE_HEADER" ] || die 'provenance header mismatch'
    sidecar_row_count=$(awk 'NR > 1 { n++ } END { print n + 0 }' "$provenance_file")
    [ "$sidecar_row_count" -eq 1 ] || die 'provenance sidecar must contain exactly one attempt row'
    # Parse with awk rather than shell IFS so a malformed column count cannot
    # silently shift actor/model/effort into another field.
    sidecar_values=$(awk -F '\t' 'NR == 2 { if (NF != 8) exit 2; for (i = 1; i <= NF; i++) printf "%s%s", $i, (i == NF ? "\n" : "\034") }' "$provenance_file") || die 'provenance row must have eight TSV fields'
    old_ifs=$IFS
    IFS=$(printf '\034')
    # shellcheck disable=SC2086 # split the six fields on the private FS separator
    set -- $sidecar_values
    IFS=$old_ifs
    [ "$#" -eq 8 ] || die 'invalid provenance sidecar fields'
    provenance_started_at=$1
    provenance_ended_at=$2
    provenance_duration_ms=$3
    provenance_actor=$4
    provenance_model=$5
    provenance_effort=$6
    provenance_exit=$7
    provenance_validation=$8
    for provenance_value in "$provenance_started_at" "$provenance_ended_at" "$provenance_duration_ms" "$provenance_actor" "$provenance_model" "$provenance_effort" "$provenance_exit" "$provenance_validation"; do
        safe_value provenance "$provenance_value"
    done
    case "$provenance_started_at" in ????-??-??T??:??:??Z) ;; *) die 'provenance started_at_utc is invalid' ;; esac
    case "$provenance_ended_at" in ????-??-??T??:??:??Z) ;; *) die 'provenance ended_at_utc is invalid' ;; esac
    case "$provenance_duration_ms" in *[!0-9]*|'') die 'provenance duration_ms must be a non-negative integer' ;; esac
    case "$provenance_actor" in luna|terra|sol) ;; *) die 'provenance actor must be luna, terra, or sol' ;; esac
    case "$provenance_model" in gpt-5.6-luna|gpt-5.6-terra|gpt-5.6-sol) ;; *) die 'provenance model is invalid' ;; esac
    case "$provenance_effort" in high|max) ;; *) die 'provenance effort must be high or max' ;; esac
    case "$provenance_exit" in *[!0-9]*) die 'provenance codex_exit must be a non-negative integer' ;; esac
    case "$provenance_validation" in validated|raw_invalid|codex_failed|codex_failed_no_output) ;; *) die 'provenance validation_status is invalid' ;; esac
}

worker_command() {
    run_dir=''; provenance_file=''; job_id=''; attempt_index=''; worker_status=''
    raw_output_file=''; task_ref=none; requirements_ref=none; report_ref=none; changed_files_ref=none; verification_ref=none
    sol_result=''; mismatch_value=''; mismatch_reason=''; self_result=''; notes=none
    escalation_from=''; escalation_to=''; effort_escalation_from=''; effort_escalation_to=''; escalation_reason=''; insufficiency_class=''; input_sufficient=''; measured_insufficiency_ref=''
    while [ "$#" -gt 0 ]; do
        case "$1" in
            --run-dir) [ "$#" -ge 2 ] || usage; run_dir=$2; shift 2 ;;
            --provenance|--provenance-file|--provenance-sidecar|--sidecar) [ "$#" -ge 2 ] || usage; provenance_file=$2; shift 2 ;;
            --raw-output|--worker-raw-output) [ "$#" -ge 2 ] || usage; raw_output_file=$2; shift 2 ;;
            --job-id|--job) [ "$#" -ge 2 ] || usage; job_id=$2; shift 2 ;;
            --index|--attempt|--attempt-seq) [ "$#" -ge 2 ] || usage; attempt_index=$2; shift 2 ;;
            --status|--result) [ "$#" -ge 2 ] || usage; worker_status=$2; shift 2 ;;
            --self-report-status) [ "$#" -ge 2 ] || usage; self_result=$2; shift 2 ;;
            --sol-measurement-result|--sol-result) [ "$#" -ge 2 ] || usage; sol_result=$2; shift 2 ;;
            --mismatch) [ "$#" -ge 2 ] || usage; mismatch_value=$2; shift 2 ;;
            --mismatch-reason) [ "$#" -ge 2 ] || usage; mismatch_reason=$2; shift 2 ;;
            --escalation-from) [ "$#" -ge 2 ] || usage; escalation_from=$2; shift 2 ;;
            --escalation-to) [ "$#" -ge 2 ] || usage; escalation_to=$2; shift 2 ;;
            --effort-escalation-from) [ "$#" -ge 2 ] || usage; effort_escalation_from=$2; shift 2 ;;
            --effort-escalation-to) [ "$#" -ge 2 ] || usage; effort_escalation_to=$2; shift 2 ;;
            --escalation-reason) [ "$#" -ge 2 ] || usage; escalation_reason=$2; shift 2 ;;
            --insufficiency-class) [ "$#" -ge 2 ] || usage; insufficiency_class=$2; shift 2 ;;
            --input-sufficient) [ "$#" -ge 2 ] || usage; input_sufficient=$2; shift 2 ;;
            --measured-insufficiency-ref) [ "$#" -ge 2 ] || usage; measured_insufficiency_ref=$2; shift 2 ;;
            --task-ref|--task) [ "$#" -ge 2 ] || usage; task_ref=$2; shift 2 ;;
            --requirements-ref|--requirements) [ "$#" -ge 2 ] || usage; requirements_ref=$2; shift 2 ;;
            --report-ref|--report) [ "$#" -ge 2 ] || usage; report_ref=$2; shift 2 ;;
            --changed-files-ref|--changed-files) [ "$#" -ge 2 ] || usage; changed_files_ref=$2; shift 2 ;;
            --verification-ref|--verification) [ "$#" -ge 2 ] || usage; verification_ref=$2; shift 2 ;;
            --notes) [ "$#" -ge 2 ] || usage; notes=$2; shift 2 ;;
            *) usage ;;
        esac
    done
    ensure_run_dir
    [ -n "$job_id" ] || die '--job-id is required'
    [ -n "$attempt_index" ] || die '--index is required'
    [ -n "$worker_status" ] || die '--status is required'
    validate_id job_id "$job_id"
    validate_attempt_key index "$attempt_index"
    case "$worker_status" in completed|blocked|failed) ;; *) die '--status must be completed, blocked, or failed' ;; esac
    [ -n "$sol_result" ] || die '--sol-measurement-result is required'
    case "$sol_result" in accepted|rejected|blocked) ;; *) die '--sol-measurement-result must be accepted, rejected, or blocked' ;; esac
    [ -n "$mismatch_value" ] || die '--mismatch is required'
    case "$mismatch_value" in match|mismatch|not_comparable) ;; *) die '--mismatch must be match, mismatch, or not_comparable' ;; esac
    [ -n "$mismatch_reason" ] || die '--mismatch-reason is required'
    case "$mismatch_value:$mismatch_reason" in match:none|mismatch:?*|not_comparable:?*) ;; *) die '--mismatch-reason must be none for match and non-empty otherwise' ;; esac
    [ -n "$escalation_from" ] || die '--escalation-from is required'; [ -n "$escalation_to" ] || die '--escalation-to is required'; [ -n "$effort_escalation_from" ] || die '--effort-escalation-from is required'; [ -n "$effort_escalation_to" ] || die '--effort-escalation-to is required'; [ -n "$escalation_reason" ] || die '--escalation-reason is required'; [ -n "$insufficiency_class" ] || die '--insufficiency-class is required'; [ -n "$input_sufficient" ] || die '--input-sufficient is required'; [ -n "$measured_insufficiency_ref" ] || die '--measured-insufficiency-ref is required'
    case "$escalation_from" in none|luna|terra|sol) ;; *) die '--escalation-from is invalid' ;; esac
    case "$escalation_to" in none|terra|sol) ;; *) die '--escalation-to is invalid' ;; esac
    case "$effort_escalation_from" in none|high|max) ;; *) die '--effort-escalation-from is invalid' ;; esac
    case "$effort_escalation_to" in none|high|max) ;; *) die '--effort-escalation-to is invalid' ;; esac
    case "$insufficiency_class" in none|capability|local-reasoning|requirement-failure|unavailable) ;; *) die '--insufficiency-class is invalid' ;; esac
    case "$input_sufficient" in yes|no|not_applicable) ;; *) die '--input-sufficient is invalid' ;; esac
    actor_transition=no
    effort_transition=no
    if [ "$escalation_from" != none ] || [ "$escalation_to" != none ]; then actor_transition=yes; fi
    if [ "$effort_escalation_from" != none ] || [ "$effort_escalation_to" != none ]; then effort_transition=yes; fi
    [ "$actor_transition" = no ] || { [ "$escalation_from" != none ] && [ "$escalation_to" != none ]; } || die 'actor escalation requires both --escalation-from and --escalation-to'
    [ "$effort_transition" = no ] || { [ "$effort_escalation_from" = high ] && [ "$effort_escalation_to" = max ]; } || die 'effort escalation must be high to max'
    [ "$actor_transition" = no ] || [ "$effort_transition" = no ] || die 'actor and effort escalation cannot occur in the same attempt'
    if [ "$actor_transition" = no ] && [ "$effort_transition" = no ]; then
        [ "$escalation_reason" = none ] && [ "$insufficiency_class" = none ] && [ "$input_sufficient" = not_applicable ] && [ "$measured_insufficiency_ref" = none ] || die 'non-escalated attempt must use none/not_applicable escalation metadata'
    else
        [ "$escalation_reason" != none ] && [ "$input_sufficient" = yes ] && [ "$measured_insufficiency_ref" != none ] || die 'escalation requires reason, sufficient input, and measured insufficiency evidence'
        case "$insufficiency_class" in capability|local-reasoning) ;; *) die 'escalation requires capability or local-reasoning insufficiency' ;; esac
    fi
    [ -n "$self_result" ] || self_result=not_provided
    case "$self_result" in completed|blocked|failed|unknown|not_provided) ;; *) die 'invalid self-report status' ;; esac
    [ -n "$provenance_file" ] || die '--provenance is required'
    require_abs_path "$provenance_file" '--provenance'
    safe_value '--provenance' "$provenance_file"
    if [ -z "$raw_output_file" ]; then
        raw_output_file="$run_dir_physical/worker-output-${attempt_index}.md"
    fi
    require_abs_path "$raw_output_file" '--raw-output'
    safe_value '--raw-output' "$raw_output_file"
    expected_raw_output="$run_dir_physical/worker-output-${attempt_index}.md"
    raw_output_physical=$(cd -P "$(dirname "$raw_output_file")" 2>/dev/null && pwd -P)/$(basename "$raw_output_file") || die 'could not canonicalize raw output path'
    [ "$raw_output_physical" = "$expected_raw_output" ] || die '--raw-output must be the current run-dir worker-output for this index'
    [ "$raw_output_file" = "$expected_raw_output" ] || die '--raw-output must use the canonical current RUN_DIR spelling'
    provenance_expected="$expected_raw_output.provenance.tsv"
    [ "$provenance_file" = "$provenance_expected" ] || die '--provenance must be the expected worker raw sidecar in RUN_DIR'
    provenance_identity_before=$(secure_file_identity "$provenance_expected" 'worker provenance sidecar')
    parse_provenance "$provenance_expected"
    if [ "$actor_transition" = yes ]; then
        case "$escalation_from:$escalation_to" in luna:terra|terra:sol) ;; *) die 'actor escalation must follow luna-to-terra or terra-to-sol' ;; esac
        [ "$escalation_to" = "$provenance_actor" ] || die 'actor escalation target must match provenance actor'
    fi
    if [ "$effort_transition" = yes ]; then
        case "$provenance_actor:$provenance_effort" in terra:max|sol:max) ;; *) die 'high-to-max effort escalation is valid only for a Terra Max or Sol Max attempt' ;; esac
    fi
    provenance_identity_after=$(secure_file_identity "$provenance_expected" 'worker provenance sidecar')
    [ "$provenance_identity_before" = "$provenance_identity_after" ] || die 'worker provenance sidecar identity changed while reading'
    if [ "$provenance_validation" = validated ]; then
        raw_identity_before=$(secure_file_identity "$expected_raw_output" 'worker raw output')
        # A validated canonical raw report is the only source for self-report
        # status.  Do not substitute Sol's measured worker status here.
        extracted_self_result=$(awk '
            /^[[:space:]]*STATUS:[[:space:]]*/ { count++; value=$0; sub(/^[[:space:]]*STATUS:[[:space:]]*/, "", value); sub(/[[:space:]]+$/, "", value) }
            END { if (count == 1 && value ~ /^(completed|blocked|failed)$/) print value; else exit 1 }
        ' "$expected_raw_output") || die 'validated raw report must expose exactly one STATUS enum'
        raw_identity_after=$(secure_file_identity "$expected_raw_output" 'worker raw output')
        [ "$raw_identity_before" = "$raw_identity_after" ] || die 'worker raw output identity changed while reading'
        if [ -n "$self_result" ] && [ "$self_result" != not_provided ] && [ "$self_result" != "$extracted_self_result" ]; then die '--self-report-status does not match validated raw STATUS'; fi
        self_result=$extracted_self_result
    else
        [ ! -e "$expected_raw_output" ] && [ ! -L "$expected_raw_output" ] || secure_file_identity "$expected_raw_output" 'unvalidated worker raw output' >/dev/null
        [ "$self_result" = not_provided ] || die 'unvalidated provenance must use self-report-status not_provided'
    fi
    validate_directory_chain post-provenance
    safe_value task_ref "$task_ref"; safe_value requirements_ref "$requirements_ref"; safe_value report_ref "$report_ref"; safe_value changed_files_ref "$changed_files_ref"; safe_value verification_ref "$verification_ref"; safe_value notes "$notes"; safe_value mismatch_reason "$mismatch_reason"; safe_value escalation_reason "$escalation_reason"; safe_value measured_insufficiency_ref "$measured_insufficiency_ref"
    destination=$(ensure_ledger worker)
    validate_directory_chain pre-append
    run_id=$(derive_run_id)
    attempt_id="$run_id:$job_id:$attempt_index"
    record_id="$attempt_id"
    row="1\tactor_attempt\t$record_id\t$run_id\t$job_id\t$attempt_id\t$attempt_index\t$provenance_actor\t$provenance_model\t$provenance_effort\t$provenance_started_at\t$provenance_ended_at\t$provenance_duration_ms\t$worker_status\t$provenance_exit\t$provenance_validation\t$self_result\t$sol_result\t$mismatch_value\t$mismatch_reason\t$escalation_from\t$escalation_to\t$escalation_reason\t$effort_escalation_from\t$effort_escalation_to\tno\t$insufficiency_class\t$input_sufficient\t$measured_insufficiency_ref\t$task_ref\t$requirements_ref\t$report_ref\t$changed_files_ref\t$verification_ref\t$provenance_ended_at\t$notes"
    ensure_record_id_unique "$destination" "$record_id"
    append_row "$destination" "$row"
}

acceptance_command() {
    run_dir=''; job_id=''; attempt_index=''; requirement_id=''; verdict_value=''; evidence_ref=''; evidence_summary='not provided'; acceptance_id=''; worker_self_result=unknown; worker_exit_code=na; notes=none
    while [ "$#" -gt 0 ]; do
        case "$1" in
            --run-dir) [ "$#" -ge 2 ] || usage; run_dir=$2; shift 2 ;;
            --job-id|--job) [ "$#" -ge 2 ] || usage; job_id=$2; shift 2 ;;
            --index|--attempt|--attempt-seq) [ "$#" -ge 2 ] || usage; attempt_index=$2; shift 2 ;;
            --requirement-id|--requirement|--req) [ "$#" -ge 2 ] || usage; requirement_id=$2; shift 2 ;;
            --verdict|--result) [ "$#" -ge 2 ] || usage; verdict_value=$2; shift 2 ;;
            --evidence-ref|--evidence|--evidence-path) [ "$#" -ge 2 ] || usage; evidence_ref=$2; shift 2 ;;
            --evidence-summary) [ "$#" -ge 2 ] || usage; evidence_summary=$2; shift 2 ;;
            --acceptance-id) [ "$#" -ge 2 ] || usage; acceptance_id=$2; shift 2 ;;
            --worker-self-report-result) [ "$#" -ge 2 ] || usage; worker_self_result=$2; shift 2 ;;
            --worker-exit-code) [ "$#" -ge 2 ] || usage; worker_exit_code=$2; shift 2 ;;
            --notes) [ "$#" -ge 2 ] || usage; notes=$2; shift 2 ;;
            *) usage ;;
        esac
    done
    ensure_run_dir
    [ -n "$job_id" ] || die '--job-id is required'; [ -n "$attempt_index" ] || die '--index is required'; [ -n "$requirement_id" ] || die '--requirement-id is required'; [ -n "$verdict_value" ] || die '--verdict is required'; [ -n "$evidence_ref" ] || die '--evidence-ref is required'
    validate_id job_id "$job_id"; validate_attempt_key index "$attempt_index"
    case "$requirement_id" in R[0-9]*) ;; *) die '--requirement-id must match R<number>' ;; esac
    case "$verdict_value" in PASS|FAIL) ;; *) die '--verdict must be PASS or FAIL' ;; esac
    [ -n "$acceptance_id" ] || acceptance_id="$(derive_run_id):$job_id:$attempt_index:acceptance"
    validate_id acceptance_id "$acceptance_id"
    safe_value evidence_ref "$evidence_ref"; safe_value evidence_summary "$evidence_summary"; safe_value worker_self_result "$worker_self_result"; safe_value worker_exit_code "$worker_exit_code"; safe_value notes "$notes"
    destination=$(ensure_ledger acceptance)
    validate_directory_chain pre-append
    run_id=$(derive_run_id); attempt_id="$run_id:$job_id:$attempt_index"; record_id="$acceptance_id:$requirement_id"
    timestamp=$(date -u '+%Y-%m-%dT%H:%M:%SZ') || die 'could not create timestamp'
    row="1\tsol_acceptance\t$record_id\t$run_id\t$job_id\t$attempt_id\t$acceptance_id\t$requirement_id\t$verdict_value\t$evidence_ref\t$evidence_summary\tsol_measurement\t$worker_self_result\t$worker_exit_code\t$timestamp\t$notes"
    ensure_record_id_unique "$destination" "$record_id"
    append_row "$destination" "$row"
}

verdict_command() {
    run_dir=''; job_id=''; target_attempt_index=''; role=''; verdict_value=''; report_ref=''; cycle=''; actual_model=''; actual_effort=''; evidence_ref=''; evidence_summary='not provided'; acceptance_ref=not_available; notes=none
    while [ "$#" -gt 0 ]; do
        case "$1" in
            --run-dir) [ "$#" -ge 2 ] || usage; run_dir=$2; shift 2 ;;
            --job-id|--job) [ "$#" -ge 2 ] || usage; job_id=$2; shift 2 ;;
            --target-attempt-index) [ "$#" -ge 2 ] || usage; target_attempt_index=$2; shift 2 ;;
            --cycle) [ "$#" -ge 2 ] || usage; cycle=$2; shift 2 ;;
            --role|--source-role|--reviewer-role) [ "$#" -ge 2 ] || usage; role=$2; shift 2 ;;
            --verdict|--result) [ "$#" -ge 2 ] || usage; verdict_value=$2; shift 2 ;;
            --report-ref|--report|--report-path) [ "$#" -ge 2 ] || usage; report_ref=$2; shift 2 ;;
            --model|--actual-model) [ "$#" -ge 2 ] || usage; actual_model=$2; shift 2 ;;
            --effort|--actual-effort) [ "$#" -ge 2 ] || usage; actual_effort=$2; shift 2 ;;
            --evidence-ref|--evidence) [ "$#" -ge 2 ] || usage; evidence_ref=$2; shift 2 ;;
            --evidence-summary) [ "$#" -ge 2 ] || usage; evidence_summary=$2; shift 2 ;;
            --sol-acceptance-ref|--acceptance-ref) [ "$#" -ge 2 ] || usage; acceptance_ref=$2; shift 2 ;;
            --notes) [ "$#" -ge 2 ] || usage; notes=$2; shift 2 ;;
            *) usage ;;
        esac
    done
    ensure_run_dir
    [ -n "$job_id" ] || die '--job-id is required'; [ -n "$target_attempt_index" ] || die '--target-attempt-index is required'; [ -n "$cycle" ] || die '--cycle is required'; [ -n "$role" ] || die '--role is required'; [ -n "$verdict_value" ] || die '--verdict is required'; [ -n "$report_ref" ] || die '--report-ref is required'; [ -n "$actual_model" ] || die '--model is required'; [ -n "$actual_effort" ] || die '--effort is required'; [ -n "$evidence_ref" ] || die '--evidence-ref is required'
    validate_id job_id "$job_id"; validate_attempt_key target_attempt_index "$target_attempt_index"; validate_cycle cycle "$cycle"; safe_value role "$role"
    case "$role" in correctness|consistency|quality|security|architecture|tester) ;; *) die '--role must be a concrete reviewer role or tester' ;; esac
    case "$verdict_value" in PASS|FAIL|BLOCKED|SKIPPED) ;; *) die '--verdict must be PASS, FAIL, BLOCKED, or SKIPPED' ;; esac
    case "$actual_model" in unavailable|'') die '--model must be an observed concrete model' ;; esac
    case "$actual_effort" in high|max) ;; *) die '--effort must be observed high or max' ;; esac
    safe_value report_ref "$report_ref"; safe_value actual_model "$actual_model"; safe_value actual_effort "$actual_effort"; safe_value evidence_ref "$evidence_ref"; safe_value evidence_summary "$evidence_summary"; safe_value acceptance_ref "$acceptance_ref"; safe_value notes "$notes"
    destination=$(ensure_ledger verdict)
    validate_directory_chain pre-append
    run_id=$(derive_run_id); target_attempt_id="$run_id:$job_id:$target_attempt_index"; verdict_kind=review
    if [ "$role" = tester ]; then
        verdict_kind='test'
    fi
    verdict_id="$run_id:$job_id:$verdict_kind:$cycle:$role"; timestamp=$(date -u '+%Y-%m-%dT%H:%M:%SZ') || die 'could not create timestamp'
    row="1\tindependent_verdict\t$verdict_id\t$run_id\t$target_attempt_id\t$verdict_id\t$cycle\t$role\t$actual_model\t$actual_effort\t$timestamp\t$timestamp\t$verdict_value\t$evidence_ref\t$evidence_summary\t$acceptance_ref\t$notes"
    ensure_record_id_unique "$destination" "$verdict_id"
    append_row "$destination" "$row"
}

case "$command_name" in
    init) init_ledgers "$@" ;;
    worker) worker_command "$@" ;;
    acceptance) acceptance_command "$@" ;;
    verdict) verdict_command "$@" ;;
    *) usage ;;
esac

exit 0
