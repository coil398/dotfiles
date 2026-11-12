"""JSON catalog command line adapter; library imports never configure logging."""
import argparse
import json
import logging
from pathlib import Path
from .engine import Catalog

logger = logging.getLogger(__name__)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Query a JSON catalog')
    parser.add_argument('path')
    parser.add_argument('query', nargs='?', default='')
    parser.add_argument('--sort')
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--page', action='store_true')
    args = parser.parse_args(argv)
    try:
        records = json.loads(Path(args.path).read_text(encoding='utf-8'))
        if not isinstance(records, list) or any(not isinstance(row, dict) for row in records):
            raise ValueError('catalog input must be an array of objects')
        catalog = Catalog(records)
        method = catalog.search_page if args.page else catalog.search
        result = method(args.query, sort=args.sort, offset=args.offset, limit=args.limit)
    except (ValueError, OSError) as exc:
        logger.error('query_failed error=%s', exc)
        return 2
    logger.info('query_done input_rows=%d output_rows=%d', len(records), len(result['items'] if args.page else result))
    print(json.dumps(result, ensure_ascii=False))
    return 0
