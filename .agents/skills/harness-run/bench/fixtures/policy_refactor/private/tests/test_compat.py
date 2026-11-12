import pytest
import policy

def test_all_wrappers_route_dynamically(monkeypatch):
    import policy.api as api
    import policy.legacy as legacy
    seen=[]; marker=object()
    def spy(*args,**kwargs): seen.append((args,kwargs)); return marker
    monkeypatch.setattr(api,'evaluate',spy)
    trace=[]; funcs={}
    for wrapper in [policy.check, policy.evaluate_legacy, legacy.check, legacy.evaluate_legacy, api.check, api.evaluate_legacy]:
        assert wrapper('x',{'x':2},trace=trace,functions=funcs) is marker
    assert len(seen)==6
    assert all(args==('x',{'x':2}) and kw['trace'] is trace and kw['functions'] is funcs for args,kw in seen)

def test_new_api_pipeline_hooks(monkeypatch):
    import policy.api as api
    seen=[]; tree=object(); marker=object()
    monkeypatch.setattr(api,'parse',lambda src:seen.append(('parse',src)) or tree)
    def execute(t,c,tr,fn):
        assert t is tree
        seen.append(('eval',c)); return marker
    monkeypatch.setattr(api,'evaluate_tree',execute)
    assert policy.evaluate('x',{'x':1}) is marker
    assert seen == [('parse','x'),('eval',{'x':1})]

def test_compilation_parses_once_and_compiler_hook(monkeypatch):
    import policy.api as api
    import policy.compiler as compiler
    original=api.parse; seen=[]
    monkeypatch.setattr(api,'parse',lambda src:seen.append(src) or original(src))
    compiled=compiler.compile_source('x or y')
    for ctx in [{'x':1}, {'x':0,'y':2}]: policy.evaluate(compiled,ctx)
    assert seen == ['x or y']
    marker=object()
    monkeypatch.setattr(api,'compile_policy',lambda src:marker)
    assert compiler.compile_source('anything') is marker

def test_legacy_behavior_matches_expected():
    import policy.legacy as legacy
    for entry in [policy.check,policy.evaluate_legacy,legacy.check,legacy.evaluate_legacy]:
        trace=[]; calls=[]
        assert entry('x or f(2)',{'x':None},trace=trace,functions={'f':lambda x:calls.append(x) or x}) == 2
        assert calls == [2] and trace == [('name','x'),('call','f'),('result',2)]

def test_frozen_ast_and_compiled_no_state():
    from dataclasses import FrozenInstanceError
    p=policy.compile_policy('x and y'); tree=p.tree
    with pytest.raises(FrozenInstanceError): p.source = 'true'
    with pytest.raises(FrozenInstanceError): tree.children = ()
    for value in [[],[1],None,False]:
        tr=[]
        expected=4 if value else value
        result=policy.evaluate(p,{'x':value,'y':4},trace=tr)
        assert result is expected
        assert p.tree is tree
