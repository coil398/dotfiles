import pytest
from catalog import Catalog, QueryError, parse

DATA = [{"name":"Alpha","score":4,"meta":{"tag":"blue"}}, {"name":"beta","score":2,"meta":{"tag":None}}, {"name":"gamma","score":3}]

def test_precedence():
    assert [x['name'] for x in Catalog(DATA).search('name:Alpha OR name:beta AND score:2')] == ['Alpha','beta']

def test_quotes():
    assert Catalog([{"name":"red OR blue"}]).search('name:"red OR blue"')

def test_nested_null_missing():
    c=Catalog(DATA)
    assert len(c.search('meta.tag:null')) == 1
    assert len(c.search('meta.tag!=null')) == 1

def test_sort_and_page_total():
    p=Catalog(DATA).search_page('',sort='score',offset=1,limit=1)
    assert (p['total'],p['items'][0]['name']) == (3,'gamma')

def test_parentheses_and_comparisons():
    assert len(Catalog(DATA).search('(score>3 OR name:beta) AND score>=2')) == 2

def test_invalid_syntax():
    for q in ('name:', '(name:x', 'name:x )', 'name:x AND'):
        with pytest.raises(QueryError): parse(q)

def test_stable_tie():
    rows=[{'id':'a','n':1},{'id':'b','n':1}]
    assert [x['id'] for x in Catalog(rows).search('',sort='-n')] == ['a','b']

def test_validation():
    with pytest.raises(ValueError): Catalog(DATA).search('',offset=True)
    with pytest.raises(ValueError): Catalog(DATA).search('',limit=-1)

def test_quoted_numeric_is_string():
    assert Catalog([{'n':'2'}, {'n':2}]).search('n:"2"') == [{'n':'2'}]

def test_cli(tmp_path, capsys):
    import json
    from catalog.cli import main
    path = tmp_path / 'rows.json'
    path.write_text(json.dumps(DATA))
    assert main([str(path), 'name:beta', '--page']) == 0
    assert json.loads(capsys.readouterr().out)['total'] == 1
