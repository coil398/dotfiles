import pytest
import policy

def test_nested_arguments_once_in_order():
    seen=[]
    def f(*args): seen.append(args); return args[0] if len(args)==1 else args
    result=policy.evaluate('f(f(1),f(2),3)',{},functions={'f':f})
    assert result == (1,2,3) and seen == [(1,),(2,),(1,2,3)]

def test_resolution_before_arguments():
    trace=[]
    with pytest.raises(NameError): policy.evaluate('unknown(missing)',{},trace=trace)
    assert trace == []
    with pytest.raises(NameError): policy.evaluate('f()',{'f':lambda:1})

def test_callback_error_identity_and_trace():
    error=RuntimeError('sentinel'); trace=[]
    def fail(a): raise error
    with pytest.raises(RuntimeError) as caught: policy.evaluate('fail(x)',{'x':2},trace=trace,functions={'fail':fail})
    assert caught.value is error
    assert trace == [('name','x'),('call','fail')]

def test_noncallable_after_arguments():
    for value in [None, 0]:
        trace=[]
        with pytest.raises(TypeError): policy.evaluate('f(x)',{'x':2},trace=trace,functions={'f':value})
        assert trace == [('name','x'),('call','f')]

def test_function_map_and_return_identity():
    marker=[]; functions={'f':lambda a,b:marker}; saved=functions.copy(); trace=[]
    assert policy.evaluate('f(1,2)',{},trace=trace,functions=functions) is marker
    assert functions == saved and trace == [('call','f'),('result',marker)]
