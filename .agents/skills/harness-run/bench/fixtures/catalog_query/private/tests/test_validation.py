import pytest
from catalog import Catalog, QueryError, parse

@pytest.mark.parametrize('group', ['syntax','quotes','fields','pagination','query_sort'])
def test_rejections(group):
    c = Catalog([])
    if group == 'syntax':
        for query in ('()', 'x:', '(x:1', 'x:1)', 'x:1 AND', 'x:1 OR OR y:2', 'x:1 y:2', 'x==1', 'x!1'):
            with pytest.raises(QueryError): parse(query)
    elif group == 'quotes':
        for query in ('x:"abc', "x:'abc", r'x:"a\nb"', 'x:ab"cd"', 'x:AND', 'x:"abc'+'\\'):
            with pytest.raises(QueryError): parse(query)
    elif group == 'fields':
        for field in ('a..b','.a','a.','1a','a-b'):
            with pytest.raises(QueryError): parse(field + ':1')
        for field in ('a..b','--a','+a',' a','a,',''):
            with pytest.raises(ValueError): c.search('',sort=field)
    elif group == 'pagination':
        for bad in (True,False,-1,1.5,'2'):
            with pytest.raises(ValueError): c.search('',offset=bad)
            with pytest.raises(ValueError): c.search_page('',limit=bad)
        with pytest.raises(ValueError): c.search_page('',limit=None)
    else:
        for bad in (None, {}, [], 1):
            with pytest.raises(ValueError): c.search(bad,limit=0)
            with pytest.raises(ValueError): c.search_page(bad,limit=0)
        for bad in (1,{},[''],[1],b'a'):
            with pytest.raises(ValueError): c.search('',sort=bad,limit=0)
