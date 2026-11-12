import pytest
from catalog import Catalog, Query

@pytest.mark.parametrize('offset,limit,ids', [(0,2,[3,5]),(1,2,[5,1]),(2,0,[]),(9,2,[]),(1,20,[5,1])])
def test_pipeline(offset, limit, ids):
    rows=[{'id':0,'kind':'skip','n':0}, {'id':1,'kind':'keep','n':9},
          {'id':2,'kind':'skip','n':1}, {'id':3,'kind':'keep','n':2},
          {'id':4,'kind':'skip','n':3}, {'id':5,'kind':'keep','n':4}]
    catalog = Catalog(rows)
    query = Query.parse('kind:keep')
    page = catalog.search_page(query,sort='n',offset=offset,limit=limit)
    assert page == {'items':[rows[i] for i in ids], 'total':3, 'offset':offset, 'limit':limit}
    assert catalog.search(query,sort='n',offset=offset,limit=limit) == page['items']
    assert catalog.search(query) == [rows[i] for i in (1,3,5)]
