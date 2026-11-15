#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -P "${SCRIPT_DIR}/.." && pwd)"
RESERVE="${REPO_ROOT}/.agents/skills/pir2/scripts/reserve-run-dir.sh"
CLEANER="${REPO_ROOT}/bin/clean-ai-runs"
SESSION_SYNC="${REPO_ROOT}/.claude/lib/dotfiles-session-sync.sh"

TEST_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEST_ROOT"' EXIT

pass=0
fail=0

ok() {
	printf 'PASS: %s\n' "$1"
	pass=$((pass + 1))
}

bad() {
	printf 'FAIL: %s\n' "$1" >&2
	fail=$((fail + 1))
}

assert_eq() {
	local label="$1" actual="$2" expected="$3"
	if [ "$actual" = "$expected" ]; then
		ok "$label"
	else
		bad "$label (expected='$expected', actual='$actual')"
	fi
}

assert_contains() {
	local label="$1" haystack="$2" needle="$3"
	if printf '%s' "$haystack" | grep -qF -- "$needle"; then
		ok "$label"
	else
		bad "$label (missing '$needle')"
	fi
}

assert_not_contains() {
	local label="$1" haystack="$2" needle="$3"
	if ! printf '%s' "$haystack" | grep -qF -- "$needle"; then
		ok "$label"
	else
		bad "$label (unexpectedly contained '$needle')"
	fi
}

assert_dir() {
	local label="$1" path="$2"
	if [ -d "$path" ] && [ ! -L "$path" ]; then
		ok "$label"
	else
		bad "$label (not a real dir: $path)"
	fi
}

assert_missing() {
	local label="$1" path="$2"
	if [ ! -e "$path" ] && [ ! -L "$path" ]; then
		ok "$label"
	else
		bad "$label (still exists: $path)"
	fi
}

assert_mode_0700() {
	local label="$1" path="$2"
	local mode
	mode="$(python3 -c 'import os,sys; print(oct(os.stat(sys.argv[1]).st_mode & 0o777))' "$path")"
	assert_eq "$label" "$mode" "0o700"
}

kv_get() {
	local output="$1" key="$2"
	printf '%s\n' "$output" | sed -n "s/^${key}=//p" | head -n 1
}

set_mtime_age_seconds() {
	local path="$1" age_s="$2"
	python3 - "$path" "$age_s" <<'PY'
import os, sys, time
p = sys.argv[1]
t = time.time() - int(sys.argv[2])
os.utime(p, (t, t))
PY
}

# ---------------------------------------------------------------------------
# 1. reserve-run-dir.sh tests
# ---------------------------------------------------------------------------
proj="${TEST_ROOT}/work/my_repo.v1"
mkdir -p "$proj/sub"
git -C "$proj" init -q

run_root="${TEST_ROOT}/runs"
fake_bin="${TEST_ROOT}/fake-bin"
mkdir -p "$fake_bin"
cat > "${fake_bin}/date" <<'SH'
#!/bin/sh
printf '20261116-010203\n'
SH
chmod +x "${fake_bin}/date"

out1="$(PATH="${fake_bin}:$PATH" sh "$RESERVE" --cwd "$proj/sub" --slug "Feature_Test! Long Slug Name Exceeding Forty Chars" --run-root "$run_root")"
proj_root1="$(kv_get "$out1" PROJECT_ROOT)"
run_dir1="$(kv_get "$out1" RUN_DIR)"
proj_run_root1="$(kv_get "$out1" PROJECT_RUN_ROOT)"
handoff1="$(kv_get "$out1" HANDOFF_PATH)"

canon_proj="$(cd -P "$proj" && pwd -P)"
expected_bucket="$(printf '%s' "$canon_proj" | sed 's|[^a-zA-Z0-9]|-|g')"
assert_eq "reserve resolves git toplevel as PROJECT_ROOT" "$proj_root1" "$canon_proj"
assert_eq "reserve builds sanitized_cwd bucket" "$(basename "$proj_run_root1")" "$expected_bucket"
assert_eq "reserve normalizes slug <=40 chars" "$(basename "$run_dir1")" "20261116-010203-feature-test-long-slug-name-exceeding-fo"
assert_eq "reserve sets HANDOFF_PATH inside bucket" "$handoff1" "${proj_run_root1}/handoff.md"
assert_dir "reserve creates RUN_DIR" "$run_dir1"
assert_mode_0700 "RUN_ROOT has mode 0700" "$run_root"
assert_mode_0700 "PROJECT_RUN_ROOT has mode 0700" "$proj_run_root1"
assert_mode_0700 "RUN_DIR has mode 0700" "$run_dir1"

# Collision appends -1
out2="$(PATH="${fake_bin}:$PATH" sh "$RESERVE" --cwd "$proj" --slug "Feature_Test! Long Slug Name Exceeding Forty Chars" --run-root "$run_root")"
run_dir2="$(kv_get "$out2" RUN_DIR)"
assert_eq "reserve appends -1 on timestamp+slug collision" "$(basename "$run_dir2")" "20261116-010203-feature-test-long-slug-name-exceeding-fo-1"
assert_dir "collision RUN_DIR created" "$run_dir2"

# Non-ASCII slug falls back to task
out3="$(PATH="${fake_bin}:$PATH" sh "$RESERVE" --cwd "$proj" --slug "日本語のみ" --run-root "$run_root")"
run_dir3="$(kv_get "$out3" RUN_DIR)"
assert_eq "non-ASCII slug falls back to task" "$(basename "$run_dir3")" "20261116-010203-task"

# _bench bucket
out_bench="$(PATH="${fake_bin}:$PATH" sh "$RESERVE" --cwd "$proj" --slug "capability" --bucket _bench --run-root "$run_root")"
assert_eq "_bench bucket path" "$(basename "$(kv_get "$out_bench" PROJECT_RUN_ROOT)")" "_bench"
assert_eq "_bench HANDOFF_PATH is empty" "$(kv_get "$out_bench" HANDOFF_PATH)" ""
assert_dir "_bench RUN_DIR created" "$(kv_get "$out_bench" RUN_DIR)"

# Rejection cases
if sh "$RESERVE" --cwd "$proj" --slug "bad" --bucket custom --run-root "$run_root" >/dev/null 2>&1; then
	bad "reject invalid --bucket"
else
	ok "reject invalid --bucket"
fi

if sh "$RESERVE" --cwd "$proj" --slug "bad" --run-root "$proj/.ai-runs" >/dev/null 2>&1; then
	bad "reject run-root inside PROJECT_ROOT"
else
	ok "reject run-root inside PROJECT_ROOT"
fi
assert_missing "did not create .ai-runs inside PROJECT_ROOT on error" "$proj/.ai-runs"

sym_root="${TEST_ROOT}/sym-runs"
ln -s "$run_root" "$sym_root"
if sh "$RESERVE" --cwd "$proj" --slug "bad" --run-root "$sym_root" >/dev/null 2>&1; then
	bad "reject symlinked RUN_ROOT"
else
	ok "reject symlinked RUN_ROOT"
fi

ln -s "${TEST_ROOT}/nonexistent" "${proj_run_root1}/handoff.md"
if sh "$RESERVE" --cwd "$proj" --slug "bad" --run-root "$run_root" >/dev/null 2>&1; then
	bad "reject symlinked handoff.md"
else
	ok "reject symlinked handoff.md"
fi
rm -f "${proj_run_root1}/handoff.md"

# ---------------------------------------------------------------------------
# 2. bin/clean-ai-runs tests
# ---------------------------------------------------------------------------
# Non-existent path exits 0
out_missing="$(bash "$CLEANER" --path "${TEST_ROOT}/does-not-exist")"
assert_contains "cleaner exits 0 on missing path" "$out_missing" "存在しません"

# Rejects symlink, HOME, /
if bash "$CLEANER" --path "$sym_root" --dry-run >/dev/null 2>&1; then
	bad "cleaner rejects symlink --path"
else
	ok "cleaner rejects symlink --path"
fi
if HOME="$TEST_ROOT" bash "$CLEANER" --path "$TEST_ROOT" --dry-run >/dev/null 2>&1; then
	bad "cleaner rejects HOME itself"
else
	ok "cleaner rejects HOME itself"
fi
if bash "$CLEANER" --path "/" --dry-run >/dev/null 2>&1; then
	bad "cleaner rejects /"
else
	ok "cleaner rejects /"
fi

clean_root="${TEST_ROOT}/clean-root"
mkdir -p "${clean_root}/-proj-a" "${clean_root}/-proj-empty" "${clean_root}/_bench" "${clean_root}/legacy-old" "${clean_root}/legacy-active"
printf 'loose\n' > "${clean_root}/stray.txt"
ln -s "${TEST_ROOT}" "${clean_root}/stray-link"

# -proj-a: 22 runs aged 10h (exceeds keep=20 -> oldest 2 deleted), 1 run aged 20d (TTL deleted),
# 1 run whose dir is 20d old but nested file is 10m old (active protected!),
# plus stale handoff.md (35d).
for i in $(seq -w 1 22); do
	d="${clean_root}/-proj-a/20261115-1000${i}-keep"
	mkdir -p "$d"
	printf 'ok\n' > "${d}/log.txt"
	# Stagger ages: 36000s + i*100s (all > 6h and < 14d; i=21,22 are oldest)
	age=$((36000 + 10#$i * 100))
	set_mtime_age_seconds "${d}/log.txt" "$age"
	set_mtime_age_seconds "$d" "$age"
done

ttl_dir="${clean_root}/-proj-a/20261001-000000-old"
mkdir -p "$ttl_dir"
printf 'old\n' > "${ttl_dir}/log.txt"
set_mtime_age_seconds "${ttl_dir}/log.txt" $((20 * 86400))
set_mtime_age_seconds "$ttl_dir" $((20 * 86400))

active_nested="${clean_root}/-proj-a/20261001-000000-active-nested"
mkdir -p "${active_nested}/sub"
printf 'running\n' > "${active_nested}/sub/events.jsonl"
set_mtime_age_seconds "$active_nested" $((20 * 86400))
set_mtime_age_seconds "${active_nested}/sub" $((20 * 86400))
set_mtime_age_seconds "${active_nested}/sub/events.jsonl" 600

printf '# handoff\n' > "${clean_root}/-proj-a/handoff.md"
set_mtime_age_seconds "${clean_root}/-proj-a/handoff.md" $((35 * 86400))

# -proj-empty: 1 run aged 20d, no handoff -> bucket should be rmdir'd
empty_run="${clean_root}/-proj-empty/20261001-000000-only"
mkdir -p "$empty_run"
set_mtime_age_seconds "$empty_run" $((20 * 86400))

# _bench: 6 runs aged 10h (keep=5 -> oldest 1 deleted) + 1 run aged 4d (bench_days=3 -> deleted) + 1 active (5m)
for i in $(seq 1 6); do
	b="${clean_root}/_bench/20261115-10000${i}-b"
	mkdir -p "$b"
	age=$((36000 + i * 100))
	set_mtime_age_seconds "$b" "$age"
done
b_ttl="${clean_root}/_bench/20261110-000000-oldbench"
mkdir -p "$b_ttl"
set_mtime_age_seconds "$b_ttl" $((4 * 86400))
b_active="${clean_root}/_bench/20261116-000000-activebench"
mkdir -p "$b_active"
set_mtime_age_seconds "$b_active" 300

# legacy dirs: one 20d old, one 10m old
set_mtime_age_seconds "${clean_root}/legacy-old" $((20 * 86400))
set_mtime_age_seconds "${clean_root}/legacy-active" 600

# Non-interactive without -y or --dry-run must fail
if bash "$CLEANER" --path "$clean_root" </dev/null >/dev/null 2>&1; then
	bad "cleaner requires -y or --dry-run in non-interactive shell"
else
	ok "cleaner requires -y or --dry-run in non-interactive shell"
fi

# Dry-run checks warnings and does not delete
dry_out="$(bash "$CLEANER" --path "$clean_root" --dry-run)"
assert_contains "dry-run warns on stale handoff" "$dry_out" "stale handoff"
assert_contains "dry-run warns on stray file" "$dry_out" "stray.txt"
assert_contains "dry-run warns on stray symlink" "$dry_out" "stray-link"
assert_contains "dry-run warns on legacy dir" "$dry_out" "legacy-old"
assert_dir "dry-run keeps ttl_dir" "$ttl_dir"
assert_dir "dry-run keeps empty_run" "$empty_run"

# Run with -y (without --prune-legacy)
run_out="$(bash "$CLEANER" --path "$clean_root" -y </dev/null)"
assert_missing "TTL expired run deleted" "$ttl_dir"
assert_missing "keep-exceeding run 21 deleted" "${clean_root}/-proj-a/20261115-100021-keep"
assert_missing "keep-exceeding run 22 deleted" "${clean_root}/-proj-a/20261115-100022-keep"
assert_dir "newest keep run 01 kept" "${clean_root}/-proj-a/20261115-100001-keep"
assert_dir "nested-active run protected despite old parent mtime" "$active_nested"
assert_eq "handoff.md protected" "$([ -f "${clean_root}/-proj-a/handoff.md" ] && echo yes || echo no)" "yes"
assert_missing "empty bucket removed after run deletion" "${clean_root}/-proj-empty"
assert_dir "bucket with handoff kept" "${clean_root}/-proj-a"
assert_missing "_bench TTL run deleted" "$b_ttl"
assert_missing "_bench keep-exceeding run 6 deleted" "${clean_root}/_bench/20261115-100006-b"
assert_dir "_bench active run protected" "$b_active"
assert_dir "legacy dir preserved without --prune-legacy" "${clean_root}/legacy-old"
assert_eq "stray file preserved" "$([ -f "${clean_root}/stray.txt" ] && echo yes || echo no)" "yes"
assert_eq "stray symlink preserved" "$([ -L "${clean_root}/stray-link" ] && echo yes || echo no)" "yes"

# Run with --prune-legacy -y
legacy_out="$(bash "$CLEANER" --path "$clean_root" --prune-legacy -y </dev/null)"
assert_missing "legacy-old deleted with --prune-legacy" "${clean_root}/legacy-old"
assert_dir "legacy-active protected within 6h even with --prune-legacy" "${clean_root}/legacy-active"
assert_eq "stray file still preserved with --prune-legacy" "$([ -f "${clean_root}/stray.txt" ] && echo yes || echo no)" "yes"

# ---------------------------------------------------------------------------
# 3. dotfiles-session-sync.sh 24h throttle test
# ---------------------------------------------------------------------------
sync_case="${TEST_ROOT}/session-sync-clean"
fake_repo="${sync_case}/repo"
state_home="${sync_case}/state"
clean_marker="${sync_case}/clean-calls"
mkdir -p "${fake_repo}/.claude/lib" "${fake_repo}/etc" "${fake_repo}/bin" "$state_home"
cp "$SESSION_SYNC" "${fake_repo}/.claude/lib/dotfiles-session-sync.sh"
cat > "${fake_repo}/etc/dotfiles-autosync.sh" <<'SH'
#!/usr/bin/env bash
exit 0
SH
cat > "${fake_repo}/bin/clean-ai-runs" <<SH
#!/usr/bin/env bash
printf '%s\n' "\$*" >> "$clean_marker"
SH
chmod +x "${fake_repo}/etc/dotfiles-autosync.sh" "${fake_repo}/bin/clean-ai-runs"

HOME="$TEST_ROOT" XDG_STATE_HOME="$state_home" DOTFILES_AUTOSYNC_SKIP= \
	bash "${fake_repo}/.claude/lib/dotfiles-session-sync.sh" --run
assert_eq "first session-sync invokes clean-ai-runs -y" "$(wc -l < "$clean_marker" | tr -d ' ')" "1"
assert_eq "first session-sync passes -y" "$(cat "$clean_marker")" "-y"
assert_eq "stamp file created" "$([ -f "${state_home}/dotfiles-autosync/last-ai-runs-clean" ] && echo yes || echo no)" "yes"

HOME="$TEST_ROOT" XDG_STATE_HOME="$state_home" DOTFILES_AUTOSYNC_SKIP= \
	bash "${fake_repo}/.claude/lib/dotfiles-session-sync.sh" --run
assert_eq "second session-sync within 24h is throttled" "$(wc -l < "$clean_marker" | tr -d ' ')" "1"

set_mtime_age_seconds "${state_home}/dotfiles-autosync/last-ai-runs-clean" 90000
HOME="$TEST_ROOT" XDG_STATE_HOME="$state_home" DOTFILES_AUTOSYNC_SKIP= \
	bash "${fake_repo}/.claude/lib/dotfiles-session-sync.sh" --run
assert_eq "session-sync after >24h invokes clean-ai-runs again" "$(wc -l < "$clean_marker" | tr -d ' ')" "2"

printf '\nSummary: %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
