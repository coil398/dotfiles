import pytest
from catalog import Catalog

@pytest.mark.parametrize('query,expected', [
    ('v=2',[0,1]),
    ('v>=+2e0 AND v<3',[0,1]),
    ('v:"2"',[2]),
    ('v:true',[3]),
    ('v>"A" AND v<"z"',[5,6]),
])
def test_typed_comparisons(query, expected):
    rows=[{'id':i,'v':v} for i,v in enumerate([2,2.0,'2',True,None,'Z','a',False,1,[],{}])]
    assert [r['id'] for r in Catalog(rows).search(query)] == expected
    # Type-sensitive inequality must be the complement over present values.
    if query == 'v=2':
        assert [r['id'] for r in Catalog(rows).search('v!=2')] == list(range(2,11))
