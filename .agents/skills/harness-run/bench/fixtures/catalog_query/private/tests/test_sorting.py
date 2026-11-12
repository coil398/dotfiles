import pytest
from catalog import Catalog

@pytest.mark.parametrize('rows,sort,ids', [
    ([{'id':0,'a':1,'b':1},{'id':1,'a':0,'b':0},{'id':2,'a':1,'b':2},{'id':3,'a':1,'b':2}], 'a,-b', [1,2,3,0]),
    ([{'id':0,'a':1},{'id':1,'a':1},{'id':2,'a':2}], '-a', [2,0,1]),
    ([{'id':0},{'id':1,'a':None},{'id':2,'a':'a'},{'id':3,'a':2},{'id':4,'a':False}], 'a', [1,4,3,2,0]),
    ([{'id':0},{'id':1,'a':None},{'id':2,'a':'a'},{'id':3,'a':2},{'id':4,'a':False}], '-a', [0,2,3,4,1]),
    ([{'id':0,'m':{'a':2}},{'id':1,'m':{'a':1}},{'id':2,'m':{'a':1}}], ['m.a','-id'], [2,1,0]),
])
def test_stable_sort(rows, sort, ids):
    catalog = Catalog(rows)
    assert [r['id'] for r in catalog.search('',sort=sort)] == ids
    assert list(catalog.records) == rows
    assert [r['id'] for r in catalog.search('',sort=sort)] == ids
