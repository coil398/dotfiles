import pytest
import tomlkit
from .support import edit


@pytest.mark.parametrize('case',range(8))
def test_invalid_batches(case):
    d=tomlkit.parse('x={a=[1,2], b=3}\ntext="abc"\n')
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
        assert d.as_string()=='x={a=[1,2], b=3}\ntext="abc"\n'
    if case==7:
        for bad in ['x=1',{},None]:
            with pytest.raises(TypeError): tomlkit.apply_edits(bad,[])
