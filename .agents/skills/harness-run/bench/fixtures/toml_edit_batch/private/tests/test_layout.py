import json
from pathlib import Path
import pytest
from .support import check

CASES=json.loads(Path(__file__).with_name('layout_cases.json').read_text())

@pytest.mark.parametrize('source,edits,expected',CASES)
def test_single_operation_parity(source,edits,expected):
    check(source,edits,expected)
