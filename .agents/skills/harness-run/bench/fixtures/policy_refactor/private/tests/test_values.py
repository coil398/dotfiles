import pytest
import policy

def test_membership_directions():
    for src,ctx in [('2 in xs',{'xs':[1,2]}),('xs contains 2',{'xs':[2]}),("text contains '日'",{'text':'日本'}),("'x' in data",{'data':{'x':None}})]:
        assert policy.evaluate(src,ctx) is True

def test_type_errors_keep_trace_prefix():
    for expr in ['x < y','x in y','x contains y']:
        trace=[]
        with pytest.raises(TypeError): policy.evaluate(expr,{'x':1,'y':None},trace=trace)
        assert trace == [('name','x'),('name','y')]

def test_equality_and_ordering_python_values():
    for expr, expected in [('1 == true',True),('null != false',True),('2 <= 2',True),("'b' > 'a'",True)]:
        assert policy.evaluate(expr,{}) is expected

def test_operand_types_preserved():
    for value in [[],{},False,None,0,'', [1]]:
        assert policy.evaluate('x and y',{'x':True,'y':value}) is value
        assert policy.evaluate('x or y',{'x':False,'y':value}) is value

def test_comparison_operand_order():
    seen=[]
    def f(x): seen.append(x); return x
    assert policy.evaluate('f(1) < f(2)',{},functions={'f':f}) is True
    assert seen == [1,2]
