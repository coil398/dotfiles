import json
from pathlib import Path
import pytest
from .support import check, edit

CASES=json.loads(Path(__file__).with_name('fragment_cases.json').read_text())

@pytest.mark.parametrize('source,path,new,expected',CASES)
def test_fragment_histories(source,path,new,expected):
    edits=[edit('rename',path,new_key=new),edit('rename',path[:-1]+[new],new_key='final')]
    # The first spelling has a hand-written byte golden; later edits use the native-value oracle.
    check(source,[edits[0]],expected)
    check(source,edits)
    out=check(source,[edits[0]])
    # Follow rename with a normal mutation through the reconstructed mapping.
    target=path[:-1]+['final']+([0] if path==['rows'] else [])+['added']
    check(source,edits+[edit('set',target,value=77)])
