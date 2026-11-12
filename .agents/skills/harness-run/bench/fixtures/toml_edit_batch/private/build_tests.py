# /// script
# dependencies = []
# ///
from pathlib import Path
import json
import subprocess
import sys
F=Path(__file__).resolve().parents[1]
T=F/'private/tests'
T.mkdir(exist_ok=True)
def put(n,s): (T/n).write_text(s)
put('support.py','''import copy
import tomllib
import tomlkit


def edit(op, path, **kw):
    return dict(op=op, path=path, **kw)


def check(source, edits, expected=None):
    original = tomlkit.parse(source)
    plain = tomllib.loads(source)
    # Independent value oracle: native TOML values, no TOMLKit internals.
    oracle = copy.deepcopy(plain)
    for e in edits:
        parent = oracle
        for k in e['path'][:-1]:
            parent = parent[k]
        k = e['path'][-1]
        if e['op'] == 'set':
            parent[k] = copy.deepcopy(e['value'])
        elif e['op'] == 'delete':
            del parent[k]
        else:
            old = parent.copy()
            parent.clear()
            parent.update((e['new_key'] if key == k else key, val) for key,val in old.items())
    out = tomlkit.apply_edits(original, iter(edits))
    assert isinstance(out, tomlkit.TOMLDocument)
    assert out is not original
    assert out.unwrap() == oracle
    assert tomllib.loads(out.as_string()) == oracle
    assert original.as_string() == source
    assert original.unwrap() == plain
    if expected is not None:
        assert out.as_string() == expected
    return out
''')
# Eight generated histories, each covering 40 documents and independent values.
put('test_semantics.py','''import random
import pytest
from .support import check, edit


@pytest.mark.parametrize('seed', [61, 98, 181, 293, 409, 587, 661, 809])
def test_histories(seed):
    rng = random.Random(seed)
    for n in range(40):
        key = rng.choice(['literal.dot', '', 'snow雪', 'quote"key', 'ordinary'])
        source = 'root = {slot = [1, 2, 3], old = {x = 4}}\\n[[rows]]\\nid=1\\n[[rows]]\\nid=2\\n'
        edits = [edit('rename',['root','old'],new_key=key),
                 edit('set',['root',key,'x'],value=rng.randrange(-10000,10000)),
                 edit('delete',['root','slot',rng.randrange(3)]),
                 edit('set',['root','slot',1],value=rng.choice([False,7,'literal'])),
                 edit('rename',['rows',1,'id'],new_key='changed'),
                 edit('set',['rows',1,'changed'],value=n),
                 edit('set',['rows',0,'extra'],value={'a':[n,n+1]}),
                 edit('delete',['rows',0]),
                 edit('set',['new'],value=[{'n':n},{'n':n+1}])]
        check(source, edits)
''')
renames=[
 ('# lead\na  = 0xFF # attached\nb=2\n',['a'],'x.y','# lead\n"x.y"  = 0xFF # attached\nb=2\n'),
 ("'old.key'\t= 'raw' # yes\nnext=2\n",['old.key'],'space name',"\"space name\"\t= 'raw' # yes\nnext=2\n"),
 ('a.b = 1\na.c = 2\n',['a'],'z','z.b = 1\nz.c = 2\n'),
 ('a.b = 1\na.c = 2\n',['a','b'],'x.y','a."x.y" = 1\na.c = 2\n'),
 ('v={a=1, b = 2, c=3} # end\n',['v','b'],'q.q','v={a=1, "q.q" = 2, c=3} # end\n'),
 ('""=true\nlast=8\n',[''],'雪','"雪"=true\nlast=8\n'),
 ('a=1\r\nb = 2 # crlf\r\n',['b'],'B','a=1\r\nB = 2 # crlf\r\n'),
 ('[a] # head\nx = 1\n[a.sub]\ny=2\n[b]\nz=3\n',['a'],'a.dot','["a.dot"] # head\nx = 1\n["a.dot".sub]\ny=2\n[b]\nz=3\n'),
]
put('rename_cases.json',json.dumps(renames,ensure_ascii=False,indent=2)+'\n')
put('test_rename.py','''import json
from pathlib import Path
import pytest
from .support import check, edit

CASES=json.loads(Path(__file__).with_name('rename_cases.json').read_text())

@pytest.mark.parametrize('source,path,new,expected',CASES)
def test_rename_golden(source,path,new,expected):
    check(source,[edit('rename',path,new_key=new)],expected)
''')
fragments=[
 ('[a.x]\nv=1\n[b]\nz=9\n[a.y]\nv=2\n',['a'],'r','[r.x]\nv=1\n[b]\nz=9\n[r.y]\nv=2\n'),
 ('[a.x]\nv=1\n[b]\nz=9\n[a.y]\nv=2\n',['a','x'],'X','[a.X]\nv=1\n[b]\nz=9\n[a.y]\nv=2\n'),
 ('[[rows]] # one\nid=1\n[rows.meta]\nx=2\n[[rows]] # two\nid=3\n[rows.meta]\nx=4\n',['rows'],'entries','[[entries]] # one\nid=1\n[entries.meta]\nx=2\n[[entries]] # two\nid=3\n[entries.meta]\nx=4\n'),
 ('[[rows]]\n[rows.meta]\nx=2\n[[rows]]\n[rows.meta]\nx=4\n',['rows',1,'meta'],'info','[[rows]]\n[rows.meta]\nx=2\n[[rows]]\n[rows.info]\nx=4\n'),
 ('[a.x]\nv=1\n[b]\nz=9\n[a.y]\nv=2\n',['a'],'r.r','["r.r".x]\nv=1\n[b]\nz=9\n["r.r".y]\nv=2\n'),
 ('a.b=1\na.c=2\n[other]\nk=3\n[a.deep]\nv=4\n',['a'],'r','r.b=1\nr.c=2\n[other]\nk=3\n[r.deep]\nv=4\n'),
 ('[a.x] # c1\r\nv=1\r\n[b]\r\nz=9\r\n[a.y] # c2\r\nv=2\r\n',['a'],'r','[r.x] # c1\r\nv=1\r\n[b]\r\nz=9\r\n[r.y] # c2\r\nv=2\r\n'),
 ('[a.x]\nv=1\n[[a.rows]]\nid=2\n[b]\nz=9\n[a.y]\nv=3\n',['a'],'r','[r.x]\nv=1\n[[r.rows]]\nid=2\n[b]\nz=9\n[r.y]\nv=3\n'),
]
put('fragment_cases.json',json.dumps(fragments,indent=2)+'\n')
put('test_fragments.py','''import json
from pathlib import Path
import pytest
from .support import check, edit

CASES=json.loads(Path(__file__).with_name('fragment_cases.json').read_text())

@pytest.mark.parametrize('source,path,new,expected',CASES)
def test_fragment_histories(source,path,new,expected):
    edits=[edit('rename',path,new_key=new),edit('rename',path[:-1]+[new],new_key='final')]
    # The first spelling has a hand-written byte golden; later edits use the native-value oracle.
    check(source,[edits[0]],expected)
    check(source,edits)
    out=check(source,[edits[0]])
    # Follow rename with a normal mutation through the reconstructed mapping.
    target=path[:-1]+['final']+([0] if path==['rows'] else [])+['added']
    check(source,edits+[edit('set',target,value=77)])
''')
# pristine single-edit oracle at fixture construction, kept out of candidate workspace
layouts=[
 ('# heading\na = 0xFF # keep\nb=2\n',[{'op':'set','path':['a'],'value':12}]),
 ('a=1\r\n# untouched\r\nb = 2 # c\r\n',[{'op':'set','path':['b'],'value':False}]),
 ('v={a=1, b=2, c=3} # t\n',[{'op':'delete','path':['v','b']}]),
 ('a = [\n  1, # one\n  2, # two\n  3,\n]\n',[{'op':'delete','path':['a',1]},{'op':'set','path':['a',0],'value':9}]),
 ('a=1\nb=2\n[other]\nx=3\n',[{'op':'set','path':['a'],'value':{'sub':4}}]),
 ('[one]\nx=1\n[two]\ny=2\n',[{'op':'set','path':['two'],'value':5}]),
 ('[a.x]\nv=1\n[b]\nz=8\n[a.y]\nv=2\n',[{'op':'set','path':['a','y','v'],'value':7},{'op':'delete','path':['a','x','v']}]),
 ('[[r]]\nx=1 # c\n[[r]]\nx=2\n',[{'op':'delete','path':['r',0]},{'op':'set','path':['r',0,'x'],'value':9}]),
]
code='''import json,sys,tomlkit
source,edits=json.load(sys.stdin)
d=tomlkit.parse(source)
for e in edits:
 p=d
 for k in e['path'][:-1]: p=p[k]
 if e['op']=='set': p[e['path'][-1]]=e['value']
 else: del p[e['path'][-1]]
print(json.dumps(d.as_string()))
'''
layoutcases=[]
for source,edits in layouts:
    out=subprocess.run([sys.executable,'-c',code],input=json.dumps([source,edits]),text=True,capture_output=True,cwd=F/'private/upstream',check=True)
    layoutcases.append([source,edits,json.loads(out.stdout)])
put('layout_cases.json',json.dumps(layoutcases,indent=2)+'\n')
put('test_layout.py','''import json
from pathlib import Path
import pytest
from .support import check

CASES=json.loads(Path(__file__).with_name('layout_cases.json').read_text())

@pytest.mark.parametrize('source,edits,expected',CASES)
def test_single_operation_parity(source,edits,expected):
    check(source,edits,expected)
''')
put('test_isolation.py','''import pytest
import tomlkit
from .support import edit


@pytest.mark.parametrize('case',range(8))
def test_isolation(case):
    source='# start\\r\\nx={a=[1,2]} # c\\r\\n[[rows]]\\r\\nid=1\\r\\n'
    d=tomlkit.parse(source)
    if case==0:
        out=tomlkit.apply_edits(d,[])
        assert out is not d and out.as_string()==source
        out['x']['a'][0]=88
        assert d['x']['a']==[1,2]
    elif case==1:
        value={'nest':[1,2]}
        out=tomlkit.apply_edits(d,[edit('set',['x','new'],value=value)])
        value['nest'].append(3)
        assert out['x']['new']['nest']==[1,2]
        out['x']['new']['nest'].append(4)
        assert value=={'nest':[1,2,3]}
    elif case==2:
        value=tomlkit.parse('v={nest=[1,2]}')['v']
        out=tomlkit.apply_edits(d,[edit('set',['x','new'],value=value)])
        out['x']['new']['nest'].append(9)
        assert value['nest']==[1,2]
        value['nest'][0]=7
        assert out['x']['new']['nest'][0]==1
    elif case==3:
        with pytest.raises(KeyError):
            tomlkit.apply_edits(d,[edit('rename',['x'],new_key='z'),edit('set',['rows',0,'id'],value=9),edit('delete',['missing'])])
    elif case==4:
        marker=RuntimeError('producer')
        def generate():
            yield edit('set',['x','a',0],value=9)
            raise marker
        with pytest.raises(RuntimeError) as exc:
            tomlkit.apply_edits(d,generate())
        assert exc.value is marker
    elif case==5:
        seen=[]
        def generate():
            seen.append(0)
            yield edit('delete',['missing'])
            seen.append(1)
            yield edit('delete',['x'])
        with pytest.raises(KeyError): tomlkit.apply_edits(d,generate())
        assert seen==[0]
    elif case==6:
        first=tomlkit.apply_edits(d,[edit('rename',['x'],new_key='y')])
        second=tomlkit.apply_edits(d,[])
        first['rows'][0]['id']=33
        assert second.as_string()==source
    else:
        edits=[edit('set',['x','a'],value=[7,8]),edit('rename',['x'],new_key='y')]
        import copy
        before=copy.deepcopy(edits)
        out=tomlkit.apply_edits(d,iter(edits))
        out['y']['a'][0]=90
        assert edits==before
    assert d.as_string()==source
    assert d.unwrap()=={'x':{'a':[1,2]},'rows':[{'id':1}]}
''')
put('test_validation.py','''import pytest
import tomlkit
from .support import edit


@pytest.mark.parametrize('case',range(8))
def test_invalid_batches(case):
    d=tomlkit.parse('x={a=[1,2], b=3}\\ntext="abc"\\n')
    groups=[
      [(edit('delete',[]),ValueError),(edit('set',['x','a',-1],value=1),ValueError)],
      [(edit('delete',['x','a',True]),TypeError),(edit('delete',['x',None]),TypeError),(edit('delete','x'),TypeError)],
      [(edit('delete',['text',0]),TypeError),(edit('set',['x','a','s'],value=2),TypeError),(edit('delete',['x',0]),TypeError)],
      [(edit('rename',['x','a',0],new_key='z'),ValueError),(edit('rename',['x','b'],new_key=7),TypeError)],
      [(edit('rename',['x','a'],new_key='b'),ValueError),(edit('rename',['x','a'],new_key='a'),ValueError)],
      [(edit('delete',['no']),KeyError),(edit('set',['no','child'],value=1),KeyError),(edit('rename',['no'],new_key='z'),KeyError)],
      [(edit('delete',['x','a',2]),IndexError),(edit('set',['x','a',2],value=1),IndexError)],
      [({'op':'unknown','path':['x']},(TypeError,ValueError)),({'op':'set','path':['x']},(TypeError,ValueError)),({'op':'delete','path':['x'],'value':1},(TypeError,ValueError)),([], (TypeError,ValueError))],
    ]
    for bad,error in groups[case]:
        with pytest.raises(error):
            tomlkit.apply_edits(d,[edit('set',['x','b'],value=999),bad])
        assert d.as_string()=='x={a=[1,2], b=3}\\ntext="abc"\\n'
    if case==7:
        for bad in ['x=1',{},None]:
            with pytest.raises(TypeError): tomlkit.apply_edits(bad,[])
''')
put('__init__.py','')
print('hidden areas: 6 x 8 cases')
