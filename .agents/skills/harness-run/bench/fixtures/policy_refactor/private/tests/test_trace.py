import pytest
import policy

def test_success_prefix_and_one_result():
    trace=[('existing',7)]
    assert policy.evaluate('(x == 1) and f(y)',{'x':1,'y':2},trace=trace,functions={'f':lambda y:y}) == 2
    assert trace == [('existing',7),('name','x'),('name','y'),('call','f'),('result',2)]

def test_callback_sees_invocation_event():
    trace=[]
    def f(a,b):
        assert trace == [('name','x'),('name','y'),('call','f')]
        return a+b
    assert policy.evaluate('f(x,y)',{'x':1,'y':2},trace=trace,functions={'f':f}) == 3
    assert trace[-1] == ('result',3)

def test_failed_argument_prefix():
    trace=[]
    with pytest.raises(NameError): policy.evaluate('f(x,absent)',{'x':1},trace=trace,functions={'f':lambda *a:0})
    assert trace == [('name','x')]

def test_nonlist_trace_ignored_and_subclass_supported():
    for trace in [None, (), {}, object()]:
        assert policy.evaluate('x',{'x':1},trace=trace) == 1
    class Trace(list): pass
    trace=Trace(); policy.evaluate('x',{'x':1},trace=trace)
    assert trace == [('name','x'),('result',1)]

def test_shortcircuit_trace_and_reuse():
    trace=[]; compiled=policy.compile_policy('a or f(b)')
    funcs={'f':lambda x:x}
    assert policy.evaluate(compiled,{'a':4},trace=trace,functions=funcs) == 4
    assert policy.evaluate(compiled,{'a':0,'b':8},trace=trace,functions=funcs) == 8
    assert trace == [('name','a'),('result',4),('name','a'),('name','b'),('call','f'),('result',8)]
