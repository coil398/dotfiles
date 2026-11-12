import pytest
import tomlkit
from .support import edit


@pytest.mark.parametrize('case',range(8))
def test_isolation(case):
    source='# start\r\nx={a=[1,2]} # c\r\n[[rows]]\r\nid=1\r\n'
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
