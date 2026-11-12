import pytest
from catalog import Catalog

ROWS = [{'id':0}, {'id':1,'meta':None}, {'id':2,'meta':{'x':None}},
        {'id':3,'meta':{'x':'null'}}, {'id':4,'meta':{'x':0}},
        {'id':5,'meta.x':None}, {'id':6,'meta':{'x':False}}]

@pytest.mark.parametrize('query,ids', [
    ('meta.x:null',[2]),
    ('meta.x!=null',[3,4,6]),
    ('meta.x:"null"',[3]),
    ('meta.x:null OR meta.x:false',[2,6]),
    ('meta.x!=0 AND meta.x!=false',[2,3]),
])
def test_path_and_null(query, ids):
    assert [r['id'] for r in Catalog(ROWS).search(query)] == ids
    assert Catalog(ROWS).search_page(query, limit=0)['total'] == len(ids)
