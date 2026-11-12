import pytest
import policy

def test_logic_mix():
    for source, expected in [('false or true and 7',7), ('true or false and missing',True), ('0 and missing or 8',8)]:
        assert policy.evaluate(source, {}) == expected

def test_not_comparison_and_repeated_not():
    for src, ctx, expected in [('not x == 2',{'x':0},True), ('not not x == 2',{'x':2},True), ('not x in xs',{'x':2,'xs':[1]},True)]:
        assert policy.evaluate(src,ctx) is expected

def test_parentheses_and_quoted_operators():
    assert policy.evaluate("('and' == 'and') and (false or 9)", {}) == 9
    assert policy.evaluate('(1 < 2) == true',{}) is True
    assert policy.evaluate('not (false or true)',{}) is False

def test_invalid_grammar_is_eager():
    for source in ['1 < 2 < 3', 'false and (1 < 2 < 3)', 'f(1,)', '', 'true false', 'not', 'and', 'x == not y']:
        trace=[]; calls=[]
        with pytest.raises(SyntaxError): policy.evaluate(source,{},trace=trace,functions={'f':lambda *a:calls.append(a)})
        assert trace == [] and calls == []

def test_ast_shape_and_token_input():
    from policy.model import Node
    tokens=list(policy.tokenize('a or b and not c'))
    saved=tokens[:]
    tree=policy.parse(tokens)
    assert tree == Node('binary','or',(Node('name','a'),Node('binary','and',(Node('name','b'),Node('unary','not',(Node('name','c'),))))))
    assert tokens == saved
