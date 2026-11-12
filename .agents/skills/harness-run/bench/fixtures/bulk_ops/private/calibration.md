# Bulk operations calibration

## Construction and reproduction

Synthetic stdlib-only package: 40 independent modules, 80 distinct functions, eight public spec volumes of ten functions and an 80-entry signature index. Each function has one public example and one hidden file containing four parametrized cases. Inputs and expected values are authored literals in build.py, never obtained by running the reference. No upstream/cache source, symlink or hardlink is included in workspace. No uv_with is required.

Run `uv run --no-project private/build.py` to regenerate the fixture. Run `uv run --no-project private/calibrate.py` to execute this calibration. The script logs per-suite counts and time, stores JUnit XML and stdout/stderr in disposable grading directories, and checks every area including unchanged areas. This report records executed acceptance checks; results.json contains exact commands, per-case outcomes, seeds and timings.

Latest evidence directory: `/home/coil398/.ai-pir-runs/benchv2/bulk-ops-calibration-wdns18os`.

All calibration grading commands use `uv run --offline -q --no-project --with pytest python -m pytest -q <targets> --junitxml=<path>` from a fresh pristine workspace copy overlaid with reference function bodies and private tests copied to tests_hidden/. Reference and baseline public/hidden commands run separately. Imports inside every hidden test function isolate collection from broken candidate modules. Package imports require stdlib only and pytest is the only test dependency. No network, sleeping, wall-clock scoring, random test data or performance area is used.

## Scores

| Variant | Public | Hidden | Score |
|---|---:|---:|---:|
| Reference | 80/80 | 320/320 | 1.00 |
| Baseline | 0/80 | 0/320 | 0.00 |
| 20 restored | — | 80/320 | 0.25 |
| 40 restored | — | 160/320 | 0.50 |
| 60 restored | — | 240/320 | 0.75 |
| One function restored | — | 4/320 | 0.0125 |
| One syntactically broken module | — | 312/320 | 0.975 |

Reference JUnit verifies exactly 80 areas × 4 cases. Baseline imports all 40 modules successfully offline (exit 0), collects all 320 cases and fails at call time with NotImplementedError, with zero collection errors or skips. Partial restorations restore units in index order. The additional one-function restoration verifies a partially restored two-function module. A syntax error in m01 fails only its eight function cases; the other 312 still pass, with no collection errors.

## Mutation isolation

Each row is an independent fresh reference with exactly that function body replaced by `raise NotImplementedError`. All four cases of the selected area fail; all 316 cases of the other 79 areas pass. Every row below was executed against the entire hidden suite.

| Unit | Target | Others | Total |
|---|---:|---:|---:|
| U001 slug | 0/4 | 316/316 | 316/320 |
| U002 collapse_spaces | 0/4 | 316/316 | 316/320 |
| U003 strip_prefix | 0/4 | 316/316 | 316/320 |
| U004 strip_suffix | 0/4 | 316/316 | 316/320 |
| U005 common_prefix | 0/4 | 316/316 | 316/320 |
| U006 common_suffix | 0/4 | 316/316 | 316/320 |
| U007 mask_tail | 0/4 | 316/316 | 316/320 |
| U008 initials | 0/4 | 316/316 | 316/320 |
| U009 escape_pairs | 0/4 | 316/316 | 316/320 |
| U010 rotate_text | 0/4 | 316/316 | 316/320 |
| U011 stable_unique | 0/4 | 316/316 | 316/320 |
| U012 compress_runs | 0/4 | 316/316 | 316/320 |
| U013 chunks | 0/4 | 316/316 | 316/320 |
| U014 windows | 0/4 | 316/316 | 316/320 |
| U015 interleave | 0/4 | 316/316 | 316/320 |
| U016 flatten_once | 0/4 | 316/316 | 316/320 |
| U017 partition_even | 0/4 | 316/316 | 316/320 |
| U018 move_zeros | 0/4 | 316/316 | 316/320 |
| U019 take_until | 0/4 | 316/316 | 316/320 |
| U020 drop_until | 0/4 | 316/316 | 316/320 |
| U021 invert_groups | 0/4 | 316/316 | 316/320 |
| U022 select_keys | 0/4 | 316/316 | 316/320 |
| U023 omit_keys | 0/4 | 316/316 | 316/320 |
| U024 merge_sums | 0/4 | 316/316 | 316/320 |
| U025 rename_keys | 0/4 | 316/316 | 316/320 |
| U026 counts | 0/4 | 316/316 | 316/320 |
| U027 group_lengths | 0/4 | 316/316 | 316/320 |
| U028 pairs_last | 0/4 | 316/316 | 316/320 |
| U029 sort_values | 0/4 | 316/316 | 316/320 |
| U030 dict_delta | 0/4 | 316/316 | 316/320 |
| U031 prefix_sums | 0/4 | 316/316 | 316/320 |
| U032 differences | 0/4 | 316/316 | 316/320 |
| U033 sign_counts | 0/4 | 316/316 | 316/320 |
| U034 sum_distinct | 0/4 | 316/316 | 316/320 |
| U035 product_nonzero | 0/4 | 316/316 | 316/320 |
| U036 weighted_sum | 0/4 | 316/316 | 316/320 |
| U037 gcd_all | 0/4 | 316/316 | 316/320 |
| U038 parity_runs | 0/4 | 316/316 | 316/320 |
| U039 argmax_first | 0/4 | 316/316 | 316/320 |
| U040 nearest_zero | 0/4 | 316/316 | 316/320 |
| U041 clamp | 0/4 | 316/316 | 316/320 |
| U042 wrap | 0/4 | 316/316 | 316/320 |
| U043 ceil_div | 0/4 | 316/316 | 316/320 |
| U044 round_multiple | 0/4 | 316/316 | 316/320 |
| U045 interval_overlap | 0/4 | 316/316 | 316/320 |
| U046 split_budget | 0/4 | 316/316 | 316/320 |
| U047 pad_right | 0/4 | 316/316 | 316/320 |
| U048 trim_edges | 0/4 | 316/316 | 316/320 |
| U049 safe_get | 0/4 | 316/316 | 316/320 |
| U050 normalize_slice | 0/4 | 316/316 | 316/320 |
| U051 pluck | 0/4 | 316/316 | 316/320 |
| U052 index_last | 0/4 | 316/316 | 316/320 |
| U053 group_rows | 0/4 | 316/316 | 316/320 |
| U054 sort_rows | 0/4 | 316/316 | 316/320 |
| U055 filter_rows | 0/4 | 316/316 | 316/320 |
| U056 sum_column | 0/4 | 316/316 | 316/320 |
| U057 project_rows | 0/4 | 316/316 | 316/320 |
| U058 number_rows | 0/4 | 316/316 | 316/320 |
| U059 distinct_rows | 0/4 | 316/316 | 316/320 |
| U060 transpose_records | 0/4 | 316/316 | 316/320 |
| U061 line_numbers | 0/4 | 316/316 | 316/320 |
| U062 word_lengths | 0/4 | 316/316 | 316/320 |
| U063 join_nonempty | 0/4 | 316/316 | 316/320 |
| U064 replace_words | 0/4 | 316/316 | 316/320 |
| U065 split_first | 0/4 | 316/316 | 316/320 |
| U066 split_last | 0/4 | 316/316 | 316/320 |
| U067 truncate | 0/4 | 316/316 | 316/320 |
| U068 ascii_digits | 0/4 | 316/316 | 316/320 |
| U069 title_tokens | 0/4 | 316/316 | 316/320 |
| U070 char_counts | 0/4 | 316/316 | 316/320 |
| U071 rotate_list | 0/4 | 316/316 | 316/320 |
| U072 explicit_order | 0/4 | 316/316 | 316/320 |
| U073 intersection | 0/4 | 316/316 | 316/320 |
| U074 difference | 0/4 | 316/316 | 316/320 |
| U075 union | 0/4 | 316/316 | 316/320 |
| U076 frequencies_sorted | 0/4 | 316/316 | 316/320 |
| U077 run_lengths | 0/4 | 316/316 | 316/320 |
| U078 expand_runs | 0/4 | 316/316 | 316/320 |
| U079 zip_fill | 0/4 | 316/316 | 316/320 |
| U080 split_on | 0/4 | 316/316 | 316/320 |

## Determinism

Each run uses a fresh reference copy and independently shuffled hidden file order. Every run has public-spec literal inputs, all 320 passing hidden cases, no skips/errors, and identical sorted (area, case, status) signatures. The ten run seeds are both PYTHONHASHSEED and the file-order shuffle seed.

| Seed | Hidden |
|---|---:|
| 0 | 320/320 |
| 1 | 320/320 |
| 2 | 320/320 |
| 7 | 320/320 |
| 42 | 320/320 |
| 99 | 320/320 |
| 101 | 320/320 |
| 31337 | 320/320 |
| 65535 | 320/320 |
| 2147483647 | 320/320 |

## Assertion to public-spec mapping

Every hidden file asserts its four independent literal golden outputs and output type, preserves a deep copy of arguments (INDEX.md nonmutation rule), compares recursive dictionary insertion order (INDEX.md order rule), and verifies returned container identities are fresh (INDEX.md fresh-container rule). Per-function semantics, valid types/preconditions, empty/boundary values and duplicate/order behavior are in the sections below. Row fixtures have scalar row fields, consistent with the documented shallow-copy rule. No hidden requirement extends the public rules.

| Area (four cases) | Public semantic/type section | Common assertions |
|---|---|---|
| slug | workspace/docs/V1.md §slug (U001) | workspace/docs/INDEX.md |
| collapse_spaces | workspace/docs/V1.md §collapse_spaces (U002) | workspace/docs/INDEX.md |
| strip_prefix | workspace/docs/V1.md §strip_prefix (U003) | workspace/docs/INDEX.md |
| strip_suffix | workspace/docs/V1.md §strip_suffix (U004) | workspace/docs/INDEX.md |
| common_prefix | workspace/docs/V1.md §common_prefix (U005) | workspace/docs/INDEX.md |
| common_suffix | workspace/docs/V1.md §common_suffix (U006) | workspace/docs/INDEX.md |
| mask_tail | workspace/docs/V1.md §mask_tail (U007) | workspace/docs/INDEX.md |
| initials | workspace/docs/V1.md §initials (U008) | workspace/docs/INDEX.md |
| escape_pairs | workspace/docs/V1.md §escape_pairs (U009) | workspace/docs/INDEX.md |
| rotate_text | workspace/docs/V1.md §rotate_text (U010) | workspace/docs/INDEX.md |
| stable_unique | workspace/docs/V2.md §stable_unique (U011) | workspace/docs/INDEX.md |
| compress_runs | workspace/docs/V2.md §compress_runs (U012) | workspace/docs/INDEX.md |
| chunks | workspace/docs/V2.md §chunks (U013) | workspace/docs/INDEX.md |
| windows | workspace/docs/V2.md §windows (U014) | workspace/docs/INDEX.md |
| interleave | workspace/docs/V2.md §interleave (U015) | workspace/docs/INDEX.md |
| flatten_once | workspace/docs/V2.md §flatten_once (U016) | workspace/docs/INDEX.md |
| partition_even | workspace/docs/V2.md §partition_even (U017) | workspace/docs/INDEX.md |
| move_zeros | workspace/docs/V2.md §move_zeros (U018) | workspace/docs/INDEX.md |
| take_until | workspace/docs/V2.md §take_until (U019) | workspace/docs/INDEX.md |
| drop_until | workspace/docs/V2.md §drop_until (U020) | workspace/docs/INDEX.md |
| invert_groups | workspace/docs/V3.md §invert_groups (U021) | workspace/docs/INDEX.md |
| select_keys | workspace/docs/V3.md §select_keys (U022) | workspace/docs/INDEX.md |
| omit_keys | workspace/docs/V3.md §omit_keys (U023) | workspace/docs/INDEX.md |
| merge_sums | workspace/docs/V3.md §merge_sums (U024) | workspace/docs/INDEX.md |
| rename_keys | workspace/docs/V3.md §rename_keys (U025) | workspace/docs/INDEX.md |
| counts | workspace/docs/V3.md §counts (U026) | workspace/docs/INDEX.md |
| group_lengths | workspace/docs/V3.md §group_lengths (U027) | workspace/docs/INDEX.md |
| pairs_last | workspace/docs/V3.md §pairs_last (U028) | workspace/docs/INDEX.md |
| sort_values | workspace/docs/V3.md §sort_values (U029) | workspace/docs/INDEX.md |
| dict_delta | workspace/docs/V3.md §dict_delta (U030) | workspace/docs/INDEX.md |
| prefix_sums | workspace/docs/V4.md §prefix_sums (U031) | workspace/docs/INDEX.md |
| differences | workspace/docs/V4.md §differences (U032) | workspace/docs/INDEX.md |
| sign_counts | workspace/docs/V4.md §sign_counts (U033) | workspace/docs/INDEX.md |
| sum_distinct | workspace/docs/V4.md §sum_distinct (U034) | workspace/docs/INDEX.md |
| product_nonzero | workspace/docs/V4.md §product_nonzero (U035) | workspace/docs/INDEX.md |
| weighted_sum | workspace/docs/V4.md §weighted_sum (U036) | workspace/docs/INDEX.md |
| gcd_all | workspace/docs/V4.md §gcd_all (U037) | workspace/docs/INDEX.md |
| parity_runs | workspace/docs/V4.md §parity_runs (U038) | workspace/docs/INDEX.md |
| argmax_first | workspace/docs/V4.md §argmax_first (U039) | workspace/docs/INDEX.md |
| nearest_zero | workspace/docs/V4.md §nearest_zero (U040) | workspace/docs/INDEX.md |
| clamp | workspace/docs/V5.md §clamp (U041) | workspace/docs/INDEX.md |
| wrap | workspace/docs/V5.md §wrap (U042) | workspace/docs/INDEX.md |
| ceil_div | workspace/docs/V5.md §ceil_div (U043) | workspace/docs/INDEX.md |
| round_multiple | workspace/docs/V5.md §round_multiple (U044) | workspace/docs/INDEX.md |
| interval_overlap | workspace/docs/V5.md §interval_overlap (U045) | workspace/docs/INDEX.md |
| split_budget | workspace/docs/V5.md §split_budget (U046) | workspace/docs/INDEX.md |
| pad_right | workspace/docs/V5.md §pad_right (U047) | workspace/docs/INDEX.md |
| trim_edges | workspace/docs/V5.md §trim_edges (U048) | workspace/docs/INDEX.md |
| safe_get | workspace/docs/V5.md §safe_get (U049) | workspace/docs/INDEX.md |
| normalize_slice | workspace/docs/V5.md §normalize_slice (U050) | workspace/docs/INDEX.md |
| pluck | workspace/docs/V6.md §pluck (U051) | workspace/docs/INDEX.md |
| index_last | workspace/docs/V6.md §index_last (U052) | workspace/docs/INDEX.md |
| group_rows | workspace/docs/V6.md §group_rows (U053) | workspace/docs/INDEX.md |
| sort_rows | workspace/docs/V6.md §sort_rows (U054) | workspace/docs/INDEX.md |
| filter_rows | workspace/docs/V6.md §filter_rows (U055) | workspace/docs/INDEX.md |
| sum_column | workspace/docs/V6.md §sum_column (U056) | workspace/docs/INDEX.md |
| project_rows | workspace/docs/V6.md §project_rows (U057) | workspace/docs/INDEX.md |
| number_rows | workspace/docs/V6.md §number_rows (U058) | workspace/docs/INDEX.md |
| distinct_rows | workspace/docs/V6.md §distinct_rows (U059) | workspace/docs/INDEX.md |
| transpose_records | workspace/docs/V6.md §transpose_records (U060) | workspace/docs/INDEX.md |
| line_numbers | workspace/docs/V7.md §line_numbers (U061) | workspace/docs/INDEX.md |
| word_lengths | workspace/docs/V7.md §word_lengths (U062) | workspace/docs/INDEX.md |
| join_nonempty | workspace/docs/V7.md §join_nonempty (U063) | workspace/docs/INDEX.md |
| replace_words | workspace/docs/V7.md §replace_words (U064) | workspace/docs/INDEX.md |
| split_first | workspace/docs/V7.md §split_first (U065) | workspace/docs/INDEX.md |
| split_last | workspace/docs/V7.md §split_last (U066) | workspace/docs/INDEX.md |
| truncate | workspace/docs/V7.md §truncate (U067) | workspace/docs/INDEX.md |
| ascii_digits | workspace/docs/V7.md §ascii_digits (U068) | workspace/docs/INDEX.md |
| title_tokens | workspace/docs/V7.md §title_tokens (U069) | workspace/docs/INDEX.md |
| char_counts | workspace/docs/V7.md §char_counts (U070) | workspace/docs/INDEX.md |
| rotate_list | workspace/docs/V8.md §rotate_list (U071) | workspace/docs/INDEX.md |
| explicit_order | workspace/docs/V8.md §explicit_order (U072) | workspace/docs/INDEX.md |
| intersection | workspace/docs/V8.md §intersection (U073) | workspace/docs/INDEX.md |
| difference | workspace/docs/V8.md §difference (U074) | workspace/docs/INDEX.md |
| union | workspace/docs/V8.md §union (U075) | workspace/docs/INDEX.md |
| frequencies_sorted | workspace/docs/V8.md §frequencies_sorted (U076) | workspace/docs/INDEX.md |
| run_lengths | workspace/docs/V8.md §run_lengths (U077) | workspace/docs/INDEX.md |
| expand_runs | workspace/docs/V8.md §expand_runs (U078) | workspace/docs/INDEX.md |
| zip_fill | workspace/docs/V8.md §zip_fill (U079) | workspace/docs/INDEX.md |
| split_on | workspace/docs/V8.md §split_on (U080) | workspace/docs/INDEX.md |

## Harness self-check

Executed command: `python3 /home/coil398/dotfiles/.agents/skills/harness-run/bench/bench.py --self-check --tasks bulk_ops --out /home/coil398/.ai-pir-runs/benchv2/bulk-ops-calibration-wdns18os/self-check`. Exit code: 0.

| fixture | reference public | reference hidden | baseline hidden |
|---|---:|---:|---:|
| bulk_ops | 80/80 | 320/320 | 0/320 |

## Final source audit

All Python files parse successfully. Manifest axes is exactly `["volume"]`; workspace has 40 modules with two stubs each, private tests have 80 files, and all fixture files are regular independent files without cache artifacts or trailing whitespace. Final index table pipe escaping was regenerated from build.py; package, reference, public and hidden Python source bytes were verified unchanged after this formatting correction.

## Unverified

No acceptance check remains unverified. Comparative model discriminating power, trial token usage and early stopping are not measured by fixture calibration. No commit or publication is performed.
