import json
from pathlib import Path
import pytest
from .support import check, edit

CASES=json.loads(Path(__file__).with_name('rename_cases.json').read_text())

@pytest.mark.parametrize('source,path,new,expected',CASES)
def test_rename_golden(source,path,new,expected):
    check(source,[edit('rename',path,new_key=new)],expected)
