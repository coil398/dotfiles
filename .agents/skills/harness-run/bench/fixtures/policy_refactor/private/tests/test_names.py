import pytest
import policy

def test_present_null_across_inputs():
    for expr in ['x', 'x == null', 'x or 7']:
        expected={'x':None,'x == null':True,'x or 7':7}[expr]
        assert policy.evaluate(policy.parse(expr),{'x':None}) == expected

def test_missing_and_successful_prefix():
    trace=[]
    with pytest.raises(NameError): policy.evaluate('a == absent',{'a':1},trace=trace)
    assert trace == [('name','a')]

def test_membership_before_get_and_no_mutation():
    class ReadMap(dict):
        def __contains__(self,key): events.append(('has',key)); return super().__contains__(key)
        def __getitem__(self,key): events.append(('get',key)); return super().__getitem__(key)
    events=[]; data=ReadMap(a=[1],b=[1]); before=dict(data)
    assert policy.evaluate('a == b',data) is True
    assert events == [('has','a'),('get','a'),('has','b'),('get','b')]
    assert dict(data)==before

def test_truthy_and_falsy_names():
    for value in [False, 0, [], {}, '', [1]]:
        assert policy.evaluate('x',{'x':value}) is value
        assert policy.evaluate('x or 8',{'x':value}) == (value or 8)

def test_shared_nested_values_not_changed():
    from copy import deepcopy
    value={'a':[1,{'b':2}]}; context={'x':value,'y':value}; before=deepcopy(context)
    tree=policy.parse('x == y')
    assert policy.evaluate(tree,context) is True
    assert context == before and context['x'] is value and tree==policy.parse('x == y')
