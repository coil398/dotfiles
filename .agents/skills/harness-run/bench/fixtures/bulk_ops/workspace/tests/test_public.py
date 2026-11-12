"""One public golden example per independent operation."""

def test_slug():
    from ops.m01 import slug
    assert slug(*['Hello World!']) == 'hello-world'

def test_collapse_spaces():
    from ops.m01 import collapse_spaces
    assert collapse_spaces(*[' a  b ']) == 'a b'

def test_strip_prefix():
    from ops.m02 import strip_prefix
    assert strip_prefix(*['prepreX', 'pre']) == 'preX'

def test_strip_suffix():
    from ops.m02 import strip_suffix
    assert strip_suffix(*['Xxx', 'x']) == 'Xx'

def test_common_prefix():
    from ops.m03 import common_prefix
    assert common_prefix(*['flower', 'flow']) == 'flow'

def test_common_suffix():
    from ops.m03 import common_suffix
    assert common_suffix(*['testing', 'ring']) == 'ing'

def test_mask_tail():
    from ops.m04 import mask_tail
    assert mask_tail(*['abcdef', 2]) == '****ef'

def test_initials():
    from ops.m04 import initials
    assert initials(*['ada lovelace']) == 'AL'

def test_escape_pairs():
    from ops.m05 import escape_pairs
    assert escape_pairs(*['a|b']) == 'a\\|b'

def test_rotate_text():
    from ops.m05 import rotate_text
    assert rotate_text(*['abcd', 1]) == 'bcda'

def test_stable_unique():
    from ops.m06 import stable_unique
    assert stable_unique(*[[3, 1, 3, 2]]) == [3, 1, 2]

def test_compress_runs():
    from ops.m06 import compress_runs
    assert compress_runs(*[[1, 1, 2, 2, 1]]) == [1, 2, 1]

def test_chunks():
    from ops.m07 import chunks
    assert chunks(*[[1, 2, 3], 2]) == [[1, 2], [3]]

def test_windows():
    from ops.m07 import windows
    assert windows(*[[1, 2, 3], 2]) == [[1, 2], [2, 3]]

def test_interleave():
    from ops.m08 import interleave
    assert interleave(*[[1, 2], [8, 9, 10]]) == [1, 8, 2, 9, 10]

def test_flatten_once():
    from ops.m08 import flatten_once
    assert flatten_once(*[[[1, 2], [3]]]) == [1, 2, 3]

def test_partition_even():
    from ops.m09 import partition_even
    assert partition_even(*[[3, 2, 1, 4]]) == [[2, 4], [3, 1]]

def test_move_zeros():
    from ops.m09 import move_zeros
    assert move_zeros(*[[0, 2, 0, 1]]) == [2, 1, 0, 0]

def test_take_until():
    from ops.m10 import take_until
    assert take_until(*[[1, 2, 3], 2]) == [1]

def test_drop_until():
    from ops.m10 import drop_until
    assert drop_until(*[[1, 2, 3], 2]) == [2, 3]

def test_invert_groups():
    from ops.m11 import invert_groups
    assert invert_groups(*[{'a': 'x', 'b': 'y', 'c': 'x'}]) == {'x': ['a', 'c'], 'y': ['b']}

def test_select_keys():
    from ops.m11 import select_keys
    assert select_keys(*[{'a': 1, 'b': 2}, ['b', 'c', 'a']]) == {'b': 2, 'a': 1}

def test_omit_keys():
    from ops.m12 import omit_keys
    assert omit_keys(*[{'a': 1, 'b': 2}, ['a']]) == {'b': 2}

def test_merge_sums():
    from ops.m12 import merge_sums
    assert merge_sums(*[{'a': 2}, {'a': 3, 'b': 1}]) == {'a': 5, 'b': 1}

def test_rename_keys():
    from ops.m13 import rename_keys
    assert rename_keys(*[{'a': 1, 'b': 2}, {'a': 'x'}]) == {'x': 1, 'b': 2}

def test_counts():
    from ops.m13 import counts
    assert counts(*[['b', 'a', 'b']]) == {'b': 2, 'a': 1}

def test_group_lengths():
    from ops.m14 import group_lengths
    assert group_lengths(*[['aa', 'b', 'cc']]) == {2: ['aa', 'cc'], 1: ['b']}

def test_pairs_last():
    from ops.m14 import pairs_last
    assert pairs_last(*[[['a', 1], ['b', 2]]]) == {'a': 1, 'b': 2}

def test_sort_values():
    from ops.m15 import sort_values
    assert sort_values(*[{'a': 3, 'b': 1}]) == ['b', 'a']

def test_dict_delta():
    from ops.m15 import dict_delta
    assert dict_delta(*[{'a': 1}, {'a': 2, 'b': 3}]) == {'a': 2, 'b': 3}

def test_prefix_sums():
    from ops.m16 import prefix_sums
    assert prefix_sums(*[[1, 2, 3]]) == [1, 3, 6]

def test_differences():
    from ops.m16 import differences
    assert differences(*[[2, 5, 4]]) == [3, -1]

def test_sign_counts():
    from ops.m17 import sign_counts
    assert sign_counts(*[[-1, 0, 2]]) == [1, 1, 1]

def test_sum_distinct():
    from ops.m17 import sum_distinct
    assert sum_distinct(*[[1, 2, 1]]) == 3

def test_product_nonzero():
    from ops.m18 import product_nonzero
    assert product_nonzero(*[[2, 0, 3]]) == 6

def test_weighted_sum():
    from ops.m18 import weighted_sum
    assert weighted_sum(*[[1, 2], [3, 4]]) == 11

def test_gcd_all():
    from ops.m19 import gcd_all
    assert gcd_all(*[[12, 18]]) == 6

def test_parity_runs():
    from ops.m19 import parity_runs
    assert parity_runs(*[[2, 4, 1, 3, 2]]) == 3

def test_argmax_first():
    from ops.m20 import argmax_first
    assert argmax_first(*[[1, 4, 2]]) == 1

def test_nearest_zero():
    from ops.m20 import nearest_zero
    assert nearest_zero(*[[-4, 2, 3]]) == 2

def test_clamp():
    from ops.m21 import clamp
    assert clamp(*[5, 0, 3]) == 3

def test_wrap():
    from ops.m21 import wrap
    assert wrap(*[8, 0, 5]) == 3

def test_ceil_div():
    from ops.m22 import ceil_div
    assert ceil_div(*[7, 3]) == 3

def test_round_multiple():
    from ops.m22 import round_multiple
    assert round_multiple(*[7, 5]) == 5

def test_interval_overlap():
    from ops.m23 import interval_overlap
    assert interval_overlap(*[1, 5, 3, 7]) == 2

def test_split_budget():
    from ops.m23 import split_budget
    assert split_budget(*[8, 3]) == [3, 3, 2]

def test_pad_right():
    from ops.m24 import pad_right
    assert pad_right(*[[1], 3, 0]) == [1, 0, 0]

def test_trim_edges():
    from ops.m24 import trim_edges
    assert trim_edges(*[[0, 1, 0, 2, 0], 0]) == [1, 0, 2]

def test_safe_get():
    from ops.m25 import safe_get
    assert safe_get(*[[4, 5], 1, 9]) == 5

def test_normalize_slice():
    from ops.m25 import normalize_slice
    assert normalize_slice(*[5, -3, 9]) == [2, 5]

def test_pluck():
    from ops.m26 import pluck
    assert pluck(*[[{'x': 1}, {'y': 2}], 'x', 0]) == [1, 0]

def test_index_last():
    from ops.m26 import index_last
    assert index_last(*[[{'id': 'a', 'n': 1}, {'id': 'b', 'n': 2}], 'id']) == {'a': {'id': 'a', 'n': 1}, 'b': {'id': 'b', 'n': 2}}

def test_group_rows():
    from ops.m27 import group_rows
    assert group_rows(*[[{'k': 'a'}, {'k': 'b'}, {'k': 'a'}], 'k']) == {'a': [{'k': 'a'}, {'k': 'a'}], 'b': [{'k': 'b'}]}

def test_sort_rows():
    from ops.m27 import sort_rows
    assert sort_rows(*[[{'n': 2}, {'n': 1}], 'n']) == [{'n': 1}, {'n': 2}]

def test_filter_rows():
    from ops.m28 import filter_rows
    assert filter_rows(*[[{'x': 1}, {'x': 2}, {}], 'x', 1]) == [{'x': 1}]

def test_sum_column():
    from ops.m28 import sum_column
    assert sum_column(*[[{'n': 2}, {'n': 3}, {}], 'n']) == 5

def test_project_rows():
    from ops.m29 import project_rows
    assert project_rows(*[[{'a': 1, 'b': 2}, {'b': 3}], ['b', 'a']]) == [{'b': 2, 'a': 1}, {'b': 3}]

def test_number_rows():
    from ops.m29 import number_rows
    assert number_rows(*[[{'x': 1}, {'x': 2}], 1]) == [{'x': 1, '_index': 1}, {'x': 2, '_index': 2}]

def test_distinct_rows():
    from ops.m30 import distinct_rows
    assert distinct_rows(*[[{'k': 'a', 'n': 1}, {'k': 'a', 'n': 2}, {'k': 'b'}], 'k']) == [{'k': 'a', 'n': 1}, {'k': 'b'}]

def test_transpose_records():
    from ops.m30 import transpose_records
    assert transpose_records(*[[{'a': 1}, {'b': 2}], ['b', 'a'], 0]) == {'b': [0, 2], 'a': [1, 0]}

def test_line_numbers():
    from ops.m31 import line_numbers
    assert line_numbers(*['a\nb']) == ['1: a', '2: b']

def test_word_lengths():
    from ops.m31 import word_lengths
    assert word_lengths(*['one four']) == [3, 4]

def test_join_nonempty():
    from ops.m32 import join_nonempty
    assert join_nonempty(*[['a', '', 'b'], ',']) == 'a,b'

def test_replace_words():
    from ops.m32 import replace_words
    assert replace_words(*['a b', {'a': 'x'}]) == 'x b'

def test_split_first():
    from ops.m33 import split_first
    assert split_first(*['a:b:c', ':']) == ['a', 'b:c']

def test_split_last():
    from ops.m33 import split_last
    assert split_last(*['a:b:c', ':']) == ['a:b', 'c']

def test_truncate():
    from ops.m34 import truncate
    assert truncate(*['abcdef', 5, '..']) == 'abc..'

def test_ascii_digits():
    from ops.m34 import ascii_digits
    assert ascii_digits(*['a1b2']) == '12'

def test_title_tokens():
    from ops.m35 import title_tokens
    assert title_tokens(*['hELLO wORLD']) == 'Hello World'

def test_char_counts():
    from ops.m35 import char_counts
    assert char_counts(*['aba']) == {'a': 2, 'b': 1}

def test_rotate_list():
    from ops.m36 import rotate_list
    assert rotate_list(*[[1, 2, 3], 1]) == [2, 3, 1]

def test_explicit_order():
    from ops.m36 import explicit_order
    assert explicit_order(*[['c', 'a', 'b'], ['b', 'a']]) == ['b', 'a', 'c']

def test_intersection():
    from ops.m37 import intersection
    assert intersection(*[[3, 1, 2], [2, 3]]) == [3, 2]

def test_difference():
    from ops.m37 import difference
    assert difference(*[[1, 2, 3], [2]]) == [1, 3]

def test_union():
    from ops.m38 import union
    assert union(*[[2, 1], [1, 3]]) == [2, 1, 3]

def test_frequencies_sorted():
    from ops.m38 import frequencies_sorted
    assert frequencies_sorted(*[[2, 1, 2]]) == [[2, 2], [1, 1]]

def test_run_lengths():
    from ops.m39 import run_lengths
    assert run_lengths(*[[1, 1, 2, 1]]) == [[1, 2], [2, 1], [1, 1]]

def test_expand_runs():
    from ops.m39 import expand_runs
    assert expand_runs(*[[[2, 2], [1, 1]]]) == [2, 2, 1]

def test_zip_fill():
    from ops.m40 import zip_fill
    assert zip_fill(*[[1, 2], [3], 0]) == [[1, 3], [2, 0]]

def test_split_on():
    from ops.m40 import split_on
    assert split_on(*[[1, 0, 2], 0]) == [[1], [2]]
