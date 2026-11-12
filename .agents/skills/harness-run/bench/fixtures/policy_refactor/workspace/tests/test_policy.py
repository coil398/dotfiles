import pytest
import policy

def test_public_pipeline_and_calls():
    toks=policy.tokenize("x >= 2 and ready")
    tree=policy.parse(toks)
    assert policy.evaluate(tree,{"x":3,"ready":True}) is True
    assert policy.evaluate("twice(4)",{},functions={"twice":lambda x:x*2})==8

def test_precedence_and_operand_values():
    assert policy.evaluate("a or b and c",{"a":0,"b":"yes","c":7})==7
    assert policy.evaluate("a and b",{"a":0,"b":2})==0

def test_trace_order():
    trace=[]
    assert policy.evaluate("f(x) == 3",{"x":3},trace=trace,functions={"f":lambda x:x})
    assert trace==[("name","x"),("call","f"),("result",True)]

def test_legacy_is_wired():
    assert policy.check("x == 2",{"x":2}) is True

def test_missing_and_present_null():
    assert policy.evaluate("x == null",{"x":None})
    with pytest.raises(NameError): policy.evaluate("x",{})

def test_invalid_source_errors():
    with pytest.raises(SyntaxError): policy.parse("(true")
    with pytest.raises(SyntaxError): policy.parse("true false")

def test_compile_reusable():
    p=policy.compile_policy("x > 0")
    assert policy.evaluate(p,{"x":1})
    assert not policy.evaluate(p,{"x":-1})

def test_short_circuit_and_type_errors():
    assert policy.evaluate("false and missing",{}) is False
    with pytest.raises(TypeError): policy.evaluate("1 < 'x'",{})


def test_token_offsets_and_comma():
    tokens=policy.tokenize('f(1,2)')
    assert [t.value for t in tokens] == ['f','(',1,',',2,')',None]
    assert tokens[-1].offset == 6


def test_not_comparison():
    assert policy.evaluate('not x == 2',{'x':0}) is True


def test_membership():
    assert policy.evaluate('xs contains 2',{'xs':[1,2]}) is True


def test_literal_word():
    assert policy.evaluate("'not'",{}) == 'not'
