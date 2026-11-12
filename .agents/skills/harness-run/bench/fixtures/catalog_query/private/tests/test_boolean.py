import pytest
from catalog import Catalog, Query

@pytest.mark.parametrize('query, expected', [
    ('a:1 OR b:1 AND c:1', [0,2,3]),
    ('(a:1 OR b:1) AND c:1', [2,3]),
    ('((a:1 OR b:1) AND c:1) OR d:1', [1,2,3]),
    ('a:1 or b:1 aNd c:1 OR d:1', [0,1,2,3]),
    ('a:1 AND (b:1 OR (c:1 AND d:1))', [3]),
])
def test_combinations(query, expected):
    rows = [dict(id=0,a=1,b=0,c=0,d=0),dict(id=1,a=0,b=1,c=0,d=1),
            dict(id=2,a=0,b=1,c=1,d=0),dict(id=3,a=1,b=1,c=1,d=1),
            dict(id=4,a=0,b=0,c=1,d=0)]
    parsed = Query.parse(query)
    catalog = Catalog(rows)
    assert [r['id'] for r in catalog.search(parsed)] == expected
    assert catalog.search(query) == catalog.search(parsed)
    assert Catalog(reversed(rows)).search(parsed) == list(reversed(catalog.search(parsed)))
