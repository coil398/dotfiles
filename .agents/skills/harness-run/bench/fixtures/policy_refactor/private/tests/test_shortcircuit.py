import pytest
import policy

def test_skip_runtime_failures():
    for src, expected in [('false and absent',False), ("'ok' or absent",'ok'), ('true or bad()',True)]:
        assert policy.evaluate(src,{}) == expected

def test_selected_operand_identity():
    for left,right in [([],{'x':1}), ([1],[]), (None,0), (0,'word')]:
        for op in ['and','or']:
            expected = (right if left else left) if op=='and' else (left if left else right)
            assert policy.evaluate('a '+op+' b',{'a':left,'b':right}) is expected

def test_nested_callbacks_exactly_once():
    seen=[]
    def f(x): seen.append(x); return x
    assert policy.evaluate('f(0) or f(2) and f(3)',{},functions={'f':f}) == 3
    assert seen == [0,2,3]

def test_skipped_comparison_and_call():
    assert policy.evaluate('false and 1 < null or 8',{}) == 8
    assert policy.evaluate('true or missing(x)',{}) is True

def test_deterministic_independent_oracle():
    from tests_hidden.oracle import cases, render, run
    for tree in cases():
        expected=run(tree,{'a':0,'b':4,'c':[]})
        actual=policy.evaluate(render(tree),{'a':0,'b':4,'c':[]})
        assert type(actual) is type(expected) and actual == expected
