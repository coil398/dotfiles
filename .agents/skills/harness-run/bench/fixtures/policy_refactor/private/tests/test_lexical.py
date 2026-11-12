import pytest
import policy

def test_escape_values_and_offsets():
    for src, value in [(r"'a\nb'", 'a\nb'), (r'"a\tb"', 'a\tb'), (r"'a\qb'", 'aqb'), ("'日本語'", '日本語')]:
        ts = policy.tokenize('  ' + src)
        assert [(t.kind, t.value, t.offset) for t in ts] == [('literal', value, 2), ('eof', None, len(src)+2)]
        assert policy.evaluate(policy.parse(ts), {}) == value

def test_comment_and_keyword_boundaries():
    src = "true # false\nand missing"
    ts = policy.tokenize(src)
    assert ts[-1].offset == len(src)
    assert policy.evaluate(src, {}) is True
    for name in ['truex', 'contains2', '_or', 'False']:
        assert policy.evaluate(name, {name: 9}) == 9

def test_literal_operator_words():
    for value in ['not', '(', 'and', 'in', 'or', ')']:
        assert policy.evaluate(repr(value), {}) == value
        assert policy.evaluate('f(' + repr(value) + ')', {}, functions={'f': lambda x:x}) == value

def test_symbols_commas_and_tokens_immutable():
    from dataclasses import FrozenInstanceError
    src = 'f(01,2)>=2'
    ts = policy.tokenize(src)
    assert [t.value for t in ts] == ['f','(',1,',',2,')','>=',2,None]
    assert [t.offset for t in ts] == [0,1,2,4,5,6,7,9,10]
    assert isinstance(ts, tuple)
    with pytest.raises(FrozenInstanceError): ts[0].offset = 3
    assert policy.evaluate(src, {}, functions={'f': lambda x,y:x+y}) is True

def test_lexical_error_positions():
    for src, pos in [('true @',5), ('é',0), ("'bad",0), ("'bad\\",0)]:
        with pytest.raises(SyntaxError) as error: policy.tokenize(src)
        assert str(pos) in str(error.value)
