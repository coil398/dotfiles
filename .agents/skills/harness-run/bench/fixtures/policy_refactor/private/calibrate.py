# /// script
# dependencies = []
# ///
"""Reproduce grading isolation, mutations and ten independent reference runs."""
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
PRIVATE=ROOT/'private'
AREAS=['calls','compat','lexical','names','precedence','shortcircuit','trace','values']
MUTATIONS={
 'calls': ('evaluator.py','args = [visit(child) for child in node.children]', 'args = [visit(child) for child in reversed(node.children)]'),
 'compat': ('legacy.py','return api.evaluate(source, context, trace=trace, functions=functions)', 'return bool(api.evaluate(source, context, trace=trace, functions=functions))'),
 'lexical': ('lexer.py','if char == "#":','if char == "~":'),
 'names': ('evaluator.py','value = context[node.value]','value = context[node.value]\n            if value is None: raise NameError(node.value)'),
 'precedence': ('parser.py','left = self.logic_and()','left = self.negation()'),
 'shortcircuit': ('evaluator.py','return left if left else visit(node.children[1])','return bool(left) if left else bool(visit(node.children[1]))'),
 'trace': ('evaluator.py','trace.append(("result", value))','trace.insert(0, ("result", value))'),
 'values': ('operators.py','"contains": lambda left, right: right in left','"contains": lambda left, right: left in right'),
}


def prepare(path, reference):
    shutil.copytree(ROOT/'workspace',path,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
    if reference: shutil.copytree(PRIVATE/'reference',path,dirs_exist_ok=True)
    shutil.copytree(PRIVATE/'tests',path/'tests_hidden',ignore=shutil.ignore_patterns('__pycache__'))


def run(path,label,target):
    evidence=PRIVATE/'evidence'
    evidence.mkdir(exist_ok=True)
    xml=evidence/(label+'.xml')
    command=['uv','run','-q','--no-project','--with','pytest','python','-m','pytest','-q',target,'--junitxml='+str(xml)]
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    result=subprocess.run(command,cwd=path,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=300)
    (evidence/(label+'.log')).write_text(result.stdout)
    cases=ET.parse(xml).findall('.//testcase')
    counts={}
    signature=[]
    for case in cases:
        area=case.attrib['classname'].split('.')[-1].removeprefix('test_')
        state='pass' if not any(case.find(tag) is not None for tag in ['failure','error','skipped']) else 'fail'
        counts.setdefault(area,{'passed':0,'total':0})
        counts[area]['total']+=1
        counts[area]['passed']+=state=='pass'
        signature.append((area,case.attrib['name'],state))
    logging.info('run label=%s target=%s exit=%s passed=%s total=%s',label,target,result.returncode,sum(c['passed'] for c in counts.values()),len(cases))
    return {'exit':result.returncode,'areas':counts,'signature':signature}


def main():
    logging.basicConfig(level=logging.INFO,format='%(levelname)s %(message)s')
    results={}
    # Each invocation gets a fresh directory; artifacts are private to the fixture.
    with tempfile.TemporaryDirectory(dir=PRIVATE,prefix='.grading-') as tmp:
        base=Path(tmp)
        for mode in ['reference','baseline']:
            path=base/mode; prepare(path,mode=='reference')
            results[mode]={target:run(path,mode+'-'+target,target) for target in ['tests','tests_hidden']}
        audit = """
from tests_hidden.oracle import cases, render, run
from policy.legacy import evaluate_legacy
for tree in cases():
    expected=run(tree,{'a':0,'b':4,'c':[]})
    actual=evaluate_legacy(render(tree),{'a':0,'b':4,'c':[]})
    assert type(actual) is type(expected) and actual==expected
for source in ['x == not y','1 < 2 < 3','false and f(1,)','not','true false']:
    trace=[]
    try: evaluate_legacy(source,{},trace=trace)
    except SyntaxError: pass
    else: raise AssertionError(source)
    assert trace==[]
trace=[]; seen=[]
def f(*args): seen.append(args); return args
assert evaluate_legacy('f(a,b)',{'a':1,'b':2},trace=trace,functions={'f':f})==(1,2)
assert trace==[('name','a'),('name','b'),('call','f'),('result',(1,2))]
assert seen==[(1,2)]
for value in [None,0]:
    trace=[]
    try: evaluate_legacy('f(a)',{'a':1},trace=trace,functions={'f':value})
    except TypeError: pass
    else: raise AssertionError(value)
    assert trace==[('name','a'),('call','f')]
print('legacy audit: 64 generated trees, 5 syntax failures, nested traces and noncallables PASS')
"""
        proc=subprocess.run(['python3','-B','-c',audit],cwd=base/'baseline',capture_output=True,text=True,timeout=300)
        (PRIVATE/'evidence/legacy-audit.log').write_text(proc.stdout+proc.stderr)
        assert proc.returncode==0,proc.stderr
        results['legacy_audit']={'exit':proc.returncode,'generated_trees':64,'syntax_errors':5}
        for area,(file,old,new) in MUTATIONS.items():
            path=base/('mutation-'+area); prepare(path,True)
            p=path/'policy'/file; s=p.read_text()
            assert old in s,(area,old)
            p.write_text(s.replace(old,new,1))
            results['mutation-'+area]=run(path,'mutation-'+area,'tests_hidden')
            assert results['mutation-'+area]['areas'][area]['passed'] < 5,area
        results['determinism']=[]
        for index in range(10):
            path=base/('determinism-'+str(index)); prepare(path,True)
            result=run(path,'determinism-'+str(index),'tests_hidden')
            results['determinism'].append(result)
    (PRIVATE/'evidence/results.json').write_text(json.dumps(results,indent=2)+'\n')
    ref=results['reference']['tests_hidden']
    assert results['reference']['tests']['exit']==0
    assert ref['exit']==0 and all(c=={'passed':5,'total':5} for c in ref['areas'].values()) and len(ref['areas'])==8
    baseline=results['baseline']['tests_hidden']
    total=sum(c['passed'] for c in baseline['areas'].values())
    assert 4<=total<=16,total
    assert all(r['signature']==ref['signature'] for r in results['determinism'])
    logging.info('acceptance passed baseline=%s/40 determinism=10/10',total)

if __name__=='__main__': main()
