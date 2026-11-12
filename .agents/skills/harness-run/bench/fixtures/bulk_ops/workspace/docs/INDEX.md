# Bulk operations index

Implement all 80 independent functions. Python stdlib only.

All inputs have the documented types and satisfy stated preconditions; no validation of invalid inputs is required. Integers exclude bool. Strings use Unicode code points unless an ASCII rule is specified. No function may mutate any input, including nested containers. Return fresh lists/dicts at every container level that the specification constructs; row copies are shallow. Dict insertion order is observable, including nested dictionaries. No cross-function dependence is required. Empty inputs, duplicate handling and order follow each section below. Return types are stated per function. All 80 functions start as importable stubs that raise NotImplementedError only when called.

| ID | Signature | Module | Specification |
|---|---|---|---|
| U001 | `slug(text: str) -> str` | `ops/m01.py` | [Volume 1 §slug](V1.md#slug) |
| U002 | `collapse_spaces(text: str) -> str` | `ops/m01.py` | [Volume 1 §collapse_spaces](V1.md#collapse_spaces) |
| U003 | `strip_prefix(text: str, prefix: str) -> str` | `ops/m02.py` | [Volume 1 §strip_prefix](V1.md#strip_prefix) |
| U004 | `strip_suffix(text: str, suffix: str) -> str` | `ops/m02.py` | [Volume 1 §strip_suffix](V1.md#strip_suffix) |
| U005 | `common_prefix(left: str, right: str) -> str` | `ops/m03.py` | [Volume 1 §common_prefix](V1.md#common_prefix) |
| U006 | `common_suffix(left: str, right: str) -> str` | `ops/m03.py` | [Volume 1 §common_suffix](V1.md#common_suffix) |
| U007 | `mask_tail(text: str, keep: int) -> str` | `ops/m04.py` | [Volume 1 §mask_tail](V1.md#mask_tail) |
| U008 | `initials(text: str) -> str` | `ops/m04.py` | [Volume 1 §initials](V1.md#initials) |
| U009 | `escape_pairs(text: str) -> str` | `ops/m05.py` | [Volume 1 §escape_pairs](V1.md#escape_pairs) |
| U010 | `rotate_text(text: str, offset: int) -> str` | `ops/m05.py` | [Volume 1 §rotate_text](V1.md#rotate_text) |
| U011 | `stable_unique(items: list[int]) -> list` | `ops/m06.py` | [Volume 2 §stable_unique](V2.md#stable_unique) |
| U012 | `compress_runs(items: list[int]) -> list` | `ops/m06.py` | [Volume 2 §compress_runs](V2.md#compress_runs) |
| U013 | `chunks(items: list[int], size: int) -> list` | `ops/m07.py` | [Volume 2 §chunks](V2.md#chunks) |
| U014 | `windows(items: list[int], size: int) -> list` | `ops/m07.py` | [Volume 2 §windows](V2.md#windows) |
| U015 | `interleave(left: list[int], right: list[int]) -> list` | `ops/m08.py` | [Volume 2 §interleave](V2.md#interleave) |
| U016 | `flatten_once(rows: list[list[int]]) -> list` | `ops/m08.py` | [Volume 2 §flatten_once](V2.md#flatten_once) |
| U017 | `partition_even(items: list[int]) -> list` | `ops/m09.py` | [Volume 2 §partition_even](V2.md#partition_even) |
| U018 | `move_zeros(items: list[int]) -> list` | `ops/m09.py` | [Volume 2 §move_zeros](V2.md#move_zeros) |
| U019 | `take_until(items: list[int], stop: int) -> list` | `ops/m10.py` | [Volume 2 §take_until](V2.md#take_until) |
| U020 | `drop_until(items: list[int], start: int) -> list` | `ops/m10.py` | [Volume 2 §drop_until](V2.md#drop_until) |
| U021 | `invert_groups(mapping: dict[str, str]) -> dict` | `ops/m11.py` | [Volume 3 §invert_groups](V3.md#invert_groups) |
| U022 | `select_keys(mapping: dict[str, int], keys: list[str]) -> dict` | `ops/m11.py` | [Volume 3 §select_keys](V3.md#select_keys) |
| U023 | `omit_keys(mapping: dict[str, int], keys: list[str]) -> dict` | `ops/m12.py` | [Volume 3 §omit_keys](V3.md#omit_keys) |
| U024 | `merge_sums(left: dict[str, int], right: dict[str, int]) -> dict` | `ops/m12.py` | [Volume 3 §merge_sums](V3.md#merge_sums) |
| U025 | `rename_keys(mapping: dict[str, int], names: dict[str, str]) -> dict` | `ops/m13.py` | [Volume 3 §rename_keys](V3.md#rename_keys) |
| U026 | `counts(items: list[str]) -> dict` | `ops/m13.py` | [Volume 3 §counts](V3.md#counts) |
| U027 | `group_lengths(items: list[str]) -> dict` | `ops/m14.py` | [Volume 3 §group_lengths](V3.md#group_lengths) |
| U028 | `pairs_last(pairs: list[list]) -> dict` | `ops/m14.py` | [Volume 3 §pairs_last](V3.md#pairs_last) |
| U029 | `sort_values(mapping: dict[str, int]) -> list` | `ops/m15.py` | [Volume 3 §sort_values](V3.md#sort_values) |
| U030 | `dict_delta(before: dict[str, int], after: dict[str, int]) -> dict` | `ops/m15.py` | [Volume 3 §dict_delta](V3.md#dict_delta) |
| U031 | `prefix_sums(items: list[int]) -> list` | `ops/m16.py` | [Volume 4 §prefix_sums](V4.md#prefix_sums) |
| U032 | `differences(items: list[int]) -> list` | `ops/m16.py` | [Volume 4 §differences](V4.md#differences) |
| U033 | `sign_counts(items: list[int]) -> list` | `ops/m17.py` | [Volume 4 §sign_counts](V4.md#sign_counts) |
| U034 | `sum_distinct(items: list[int]) -> int` | `ops/m17.py` | [Volume 4 §sum_distinct](V4.md#sum_distinct) |
| U035 | `product_nonzero(items: list[int]) -> int` | `ops/m18.py` | [Volume 4 §product_nonzero](V4.md#product_nonzero) |
| U036 | `weighted_sum(values: list[int], weights: list[int]) -> int` | `ops/m18.py` | [Volume 4 §weighted_sum](V4.md#weighted_sum) |
| U037 | `gcd_all(items: list[int]) -> int` | `ops/m19.py` | [Volume 4 §gcd_all](V4.md#gcd_all) |
| U038 | `parity_runs(items: list[int]) -> int` | `ops/m19.py` | [Volume 4 §parity_runs](V4.md#parity_runs) |
| U039 | `argmax_first(items: list[int]) -> int \| None` | `ops/m20.py` | [Volume 4 §argmax_first](V4.md#argmax_first) |
| U040 | `nearest_zero(items: list[int]) -> int \| None` | `ops/m20.py` | [Volume 4 §nearest_zero](V4.md#nearest_zero) |
| U041 | `clamp(value: int, low: int, high: int) -> int` | `ops/m21.py` | [Volume 5 §clamp](V5.md#clamp) |
| U042 | `wrap(value: int, low: int, high: int) -> int` | `ops/m21.py` | [Volume 5 §wrap](V5.md#wrap) |
| U043 | `ceil_div(value: int, divisor: int) -> int` | `ops/m22.py` | [Volume 5 §ceil_div](V5.md#ceil_div) |
| U044 | `round_multiple(value: int, step: int) -> int` | `ops/m22.py` | [Volume 5 §round_multiple](V5.md#round_multiple) |
| U045 | `interval_overlap(a: int, b: int, c: int, d: int) -> int` | `ops/m23.py` | [Volume 5 §interval_overlap](V5.md#interval_overlap) |
| U046 | `split_budget(total: int, count: int) -> list` | `ops/m23.py` | [Volume 5 §split_budget](V5.md#split_budget) |
| U047 | `pad_right(items: list[int], size: int, fill: int) -> list` | `ops/m24.py` | [Volume 5 §pad_right](V5.md#pad_right) |
| U048 | `trim_edges(items: list[int], value: int) -> list` | `ops/m24.py` | [Volume 5 §trim_edges](V5.md#trim_edges) |
| U049 | `safe_get(items: list[int], index: int, default: int) -> int` | `ops/m25.py` | [Volume 5 §safe_get](V5.md#safe_get) |
| U050 | `normalize_slice(length: int, start: int, stop: int) -> list` | `ops/m25.py` | [Volume 5 §normalize_slice](V5.md#normalize_slice) |
| U051 | `pluck(rows: list[dict], key: str, default: int) -> list` | `ops/m26.py` | [Volume 6 §pluck](V6.md#pluck) |
| U052 | `index_last(rows: list[dict], key: str) -> dict` | `ops/m26.py` | [Volume 6 §index_last](V6.md#index_last) |
| U053 | `group_rows(rows: list[dict], key: str) -> dict` | `ops/m27.py` | [Volume 6 §group_rows](V6.md#group_rows) |
| U054 | `sort_rows(rows: list[dict], key: str) -> list` | `ops/m27.py` | [Volume 6 §sort_rows](V6.md#sort_rows) |
| U055 | `filter_rows(rows: list[dict], key: str, value: int) -> list` | `ops/m28.py` | [Volume 6 §filter_rows](V6.md#filter_rows) |
| U056 | `sum_column(rows: list[dict], key: str) -> int` | `ops/m28.py` | [Volume 6 §sum_column](V6.md#sum_column) |
| U057 | `project_rows(rows: list[dict], keys: list[str]) -> list` | `ops/m29.py` | [Volume 6 §project_rows](V6.md#project_rows) |
| U058 | `number_rows(rows: list[dict], start: int) -> list` | `ops/m29.py` | [Volume 6 §number_rows](V6.md#number_rows) |
| U059 | `distinct_rows(rows: list[dict], key: str) -> list` | `ops/m30.py` | [Volume 6 §distinct_rows](V6.md#distinct_rows) |
| U060 | `transpose_records(rows: list[dict], keys: list[str], default: int) -> dict` | `ops/m30.py` | [Volume 6 §transpose_records](V6.md#transpose_records) |
| U061 | `line_numbers(text: str) -> list` | `ops/m31.py` | [Volume 7 §line_numbers](V7.md#line_numbers) |
| U062 | `word_lengths(text: str) -> list` | `ops/m31.py` | [Volume 7 §word_lengths](V7.md#word_lengths) |
| U063 | `join_nonempty(items: list[str], separator: str) -> str` | `ops/m32.py` | [Volume 7 §join_nonempty](V7.md#join_nonempty) |
| U064 | `replace_words(text: str, replacements: dict[str, str]) -> str` | `ops/m32.py` | [Volume 7 §replace_words](V7.md#replace_words) |
| U065 | `split_first(text: str, separator: str) -> list` | `ops/m33.py` | [Volume 7 §split_first](V7.md#split_first) |
| U066 | `split_last(text: str, separator: str) -> list` | `ops/m33.py` | [Volume 7 §split_last](V7.md#split_last) |
| U067 | `truncate(text: str, limit: int, marker: str) -> str` | `ops/m34.py` | [Volume 7 §truncate](V7.md#truncate) |
| U068 | `ascii_digits(text: str) -> str` | `ops/m34.py` | [Volume 7 §ascii_digits](V7.md#ascii_digits) |
| U069 | `title_tokens(text: str) -> str` | `ops/m35.py` | [Volume 7 §title_tokens](V7.md#title_tokens) |
| U070 | `char_counts(text: str) -> dict` | `ops/m35.py` | [Volume 7 §char_counts](V7.md#char_counts) |
| U071 | `rotate_list(items: list[int], offset: int) -> list` | `ops/m36.py` | [Volume 8 §rotate_list](V8.md#rotate_list) |
| U072 | `explicit_order(items: list[str], priority: list[str]) -> list` | `ops/m36.py` | [Volume 8 §explicit_order](V8.md#explicit_order) |
| U073 | `intersection(left: list[int], right: list[int]) -> list` | `ops/m37.py` | [Volume 8 §intersection](V8.md#intersection) |
| U074 | `difference(left: list[int], right: list[int]) -> list` | `ops/m37.py` | [Volume 8 §difference](V8.md#difference) |
| U075 | `union(left: list[int], right: list[int]) -> list` | `ops/m38.py` | [Volume 8 §union](V8.md#union) |
| U076 | `frequencies_sorted(items: list[int]) -> list` | `ops/m38.py` | [Volume 8 §frequencies_sorted](V8.md#frequencies_sorted) |
| U077 | `run_lengths(items: list[int]) -> list` | `ops/m39.py` | [Volume 8 §run_lengths](V8.md#run_lengths) |
| U078 | `expand_runs(runs: list[list[int]]) -> list` | `ops/m39.py` | [Volume 8 §expand_runs](V8.md#expand_runs) |
| U079 | `zip_fill(left: list[int], right: list[int], fill: int) -> list` | `ops/m40.py` | [Volume 8 §zip_fill](V8.md#zip_fill) |
| U080 | `split_on(items: list[int], delimiter: int) -> list` | `ops/m40.py` | [Volume 8 §split_on](V8.md#split_on) |
