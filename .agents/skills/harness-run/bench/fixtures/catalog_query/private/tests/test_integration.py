import json
import subprocess
import sys
import pytest
from catalog import Catalog, Query

@pytest.mark.parametrize('scenario', ['cli_page','cli_plain','cli_errors','ownership','reuse'])
def test_integration(scenario, tmp_path):
    rows=[{'id':0,'name':'日本','m':{'n':2}},{'id':1,'name':'other','m':{'n':1}},{'id':2,'name':'日本','m':{'n':3}}]
    path=tmp_path/'catalog.json'
    path.write_text(json.dumps(rows),encoding='utf-8')
    def run(*args):
        return subprocess.run([sys.executable,'-m','catalog',str(path),*args],capture_output=True,text=True)
    if scenario == 'cli_page':
        result=run('name:"日本"','--sort=-m.n','--offset','1','--limit','1','--page')
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == {'items':[rows[0]],'total':2,'offset':1,'limit':1}
    elif scenario == 'cli_plain':
        result=run('(m.n>=2 AND name:"日本")','--sort=-id','--limit','1')
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == [rows[2]]
    elif scenario == 'cli_errors':
        for args in [('name:',), ('','--offset','-1'), ('','--sort','a..b'), ('','--limit','-1')]:
            result=run(*args)
            assert result.returncode == 2
            assert result.stdout == ''
            assert result.stderr
        path.write_text('[1]')
        assert run().returncode == 2
    elif scenario == 'ownership':
        c=Catalog(iter(rows))
        rows[0]['m']['n']=99
        assert c.search('m.n:2')[0]['id'] == 0
        result=c.search('')
        result[0]['m']['n']=88
        c.records[0]['m']['n']=77
        page=c.search_page('')
        page['items'][0]['m']['n']=66
        assert c.search('m.n:2')[0]['id'] == 0
    else:
        q=Query.parse('m.n>=2')
        c=Catalog(rows+rows[:1])
        assert c.search(q) == [rows[0],rows[2],rows[0]]
        assert Catalog(rows[1:]).search(q) == [rows[2]]
        assert c.search(q,limit=0) == []
        assert c.search(q,offset=1) == [rows[2],rows[0]]
        assert c.search('   ') == rows+rows[:1]
