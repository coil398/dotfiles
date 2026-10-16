#!/bin/sh

set -eu

log_dir="${HOME}/Library/Logs"
log_file="$log_dir/go-cache-trim.log"
mkdir -p "$log_dir"
run_id="$(date '+%Y%m%dT%H%M%S%z')-$$"
started_epoch="$(date '+%s')"

log() {
    level=$1
    shift
    printf '%s %s go-cache-trim %s run_id=%s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$level" "$*" "$run_id" | tee -a "$log_file" >&2
}

if [ "${GOCACHE+x}" = x ] && [ "$GOCACHE" = off ]; then
    log INFO "skip reason=cache_disabled cache_source=environment"
    exit 0
elif [ "${GOCACHE+x}" = x ] && [ -n "$GOCACHE" ]; then
    cache_dir="$GOCACHE"
    cache_source=environment
elif command -v go >/dev/null 2>&1; then
    cache_dir="$(go env GOCACHE 2>/dev/null || true)"
    cache_source=go_env
    if [ -z "$cache_dir" ]; then
        cache_dir="${HOME}/Library/Caches/go-build"
        cache_source=default
    fi
else
    cache_dir="${HOME}/Library/Caches/go-build"
    cache_source=default
fi

if [ "$cache_dir" = off ]; then
    log INFO "skip reason=cache_disabled cache_source=$cache_source"
    exit 0
fi
case "$cache_dir" in
    /*) ;;
    *)
        log INFO "skip reason=cache_path_not_absolute cache_dir=$cache_dir cache_source=$cache_source"
        exit 0
        ;;
esac
[ -d "$cache_dir" ] || {
    log INFO "skip reason=cache_directory_missing cache_dir=$cache_dir cache_source=$cache_source"
    exit 0
}

readme="$cache_dir/README"
if [ ! -f "$readme" ]; then
    log INFO "skip reason=cache_readme_missing cache_dir=$cache_dir cache_source=$cache_source"
    exit 0
fi
if [ ! -r "$readme" ]; then
    log INFO "skip reason=cache_readme_unreadable cache_dir=$cache_dir cache_source=$cache_source"
    exit 0
fi
readme_header=''
IFS= read -r readme_header < "$readme" || true
case "$readme_header" in
    'This directory holds cached build artifacts from the Go build system.'*) ;;
    *)
        log INFO "skip reason=cache_readme_unrecognized cache_dir=$cache_dir cache_source=$cache_source"
        exit 0
        ;;
esac

directory_bytes() {
    du -sk "$1" 2>/dev/null | awk '{print $1 * 1024}'
}

count_lines() {
    if [ -n "$1" ]; then
        printf '%s\n' "$1" | wc -l | tr -d ' '
    else
        printf '0\n'
    fi
}

max_age_minutes=${GO_CACHE_TRIM_MAX_AGE_MINUTES-120}
case "$max_age_minutes" in
    ''|*[!0-9]*)
        log WARN "invalid_max_age_minutes value=$max_age_minutes reason=not_positive_integer using=120"
        max_age_minutes=120
        ;;
    *)
        if [ "$max_age_minutes" -lt 60 ]; then
            log WARN "invalid_max_age_minutes value=$max_age_minutes reason=below_minimum_60 using=120"
            max_age_minutes=120
        fi
        ;;
esac

log INFO "start cache_dir=$cache_dir cache_source=$cache_source max_age_minutes=$max_age_minutes"
before_bytes="$(directory_bytes "$cache_dir")"
removed_files=0
removed_dirs=0

for shard in "$cache_dir"/*; do
    [ -d "$shard" ] || continue
    shard_name="${shard##*/}"
    case "$shard_name" in
        [0-9a-f][0-9a-f]) ;;
        *) continue ;;
    esac

    if deleted_files="$(find "$shard" -mindepth 1 -maxdepth 1 -type f -mmin +"$max_age_minutes" ! -name trim.txt ! -name README -exec sh -c 'rm -f -- "$@"; s=0; for f; do if [ -e "$f" ] || [ -L "$f" ]; then s=1; else printf "%s\n" "$f"; fi; done; exit "$s"' sh {} + 2>>"$log_file")"; then
        count="$(count_lines "$deleted_files")"
        removed_files=$((removed_files + count))
    else
        count="$(count_lines "$deleted_files")"
        removed_files=$((removed_files + count))
        log WARN "find_failed kind=files shard=$shard"
    fi

    if deleted_dirs="$(find "$shard" -mindepth 1 -maxdepth 1 -type d -name '*-d' -mmin +"$max_age_minutes" -exec sh -c 'rm -rf -- "$@"; s=0; for f; do if [ -e "$f" ] || [ -L "$f" ]; then s=1; else printf "%s\n" "$f"; fi; done; exit "$s"' sh {} + 2>>"$log_file")"; then
        count="$(count_lines "$deleted_dirs")"
        removed_dirs=$((removed_dirs + count))
    else
        count="$(count_lines "$deleted_dirs")"
        removed_dirs=$((removed_dirs + count))
        log WARN "find_failed kind=directories shard=$shard"
    fi
done

after_bytes="$(directory_bytes "$cache_dir")"
freed_bytes=$((before_bytes - after_bytes))
[ "$freed_bytes" -ge 0 ] || freed_bytes=0
log INFO "trimmed removed_files=$removed_files removed_dirs=$removed_dirs before_bytes=$before_bytes after_bytes=$after_bytes freed_bytes=$freed_bytes"
finished_epoch="$(date '+%s')"
elapsed_s=$((finished_epoch - started_epoch))
log INFO "done cache_dir=$cache_dir elapsed_s=$elapsed_s"
