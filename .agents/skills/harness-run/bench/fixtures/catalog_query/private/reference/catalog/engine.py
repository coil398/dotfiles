from copy import deepcopy
from .parser import Query, parse
from .pagination import pagination
from .storage import RecordStore
from .matching import matches
from .sorting import ordered, sort_fields




class Catalog(RecordStore):
    def _select(self, query, sort):
        parsed = parse(query) if isinstance(query, str) else query
        if not isinstance(parsed, Query):
            raise ValueError('query must be text or Query')
        fields = sort_fields(sort)
        rows = [row for row in self._records if matches(row, parsed.tree)]
        return ordered(rows, fields)

    def search(self, query='', *, sort=None, offset=0, limit=None):
        pagination(offset, limit)
        rows = self._select(query, sort)
        return deepcopy(rows[offset:None if limit is None else offset + limit])

    def search_page(self, query='', *, sort=None, offset=0, limit=20):
        pagination(offset, limit, page=True)
        rows = self._select(query, sort)
        return {'items': deepcopy(rows[offset:offset + limit]), 'total': len(rows), 'offset': offset, 'limit': limit}
