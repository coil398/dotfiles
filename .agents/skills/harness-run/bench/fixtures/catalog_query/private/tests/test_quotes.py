import pytest
from catalog import Catalog, parse

@pytest.mark.parametrize('query,value', [
    ('name:"AND (x:y) OR z>=2"', 'AND (x:y) OR z>=2'),
    (r"name:'it\'s \\\\ ok'", "it's \\\\ ok"),
    (r'''name:"a\"b\\c"''', 'a"b\\c'),
    ('name:"日本 語 ☃"', '日本 語 ☃'),
    ("name:''", ''),
])
def test_quoted_values(query, value):
    rows = [{'id':0,'name':value},{'id':1,'name':value+'x'}, {'id':2,'name':'other'}]
    catalog = Catalog(rows)
    assert catalog.search(parse(query)) == [rows[0]]
    assert catalog.search('(' + query + ') OR name:other') == [rows[0], rows[2]]
