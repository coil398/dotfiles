import random
import pytest
from .support import check, edit


@pytest.mark.parametrize('seed', [61, 98, 181, 293, 409, 587, 661, 809])
def test_histories(seed):
    rng = random.Random(seed)
    for n in range(40):
        key = rng.choice(['literal.dot', '', 'snow雪', 'quote"key', 'ordinary'])
        source = 'root = {slot = [1, 2, 3], old = {x = 4}}\n[[rows]]\nid=1\n[[rows]]\nid=2\n'
        edits = [edit('rename',['root','old'],new_key=key),
                 edit('set',['root',key,'x'],value=rng.randrange(-10000,10000)),
                 edit('delete',['root','slot',rng.randrange(3)]),
                 edit('set',['root','slot',1],value=rng.choice([False,7,'literal'])),
                 edit('rename',['rows',1,'id'],new_key='changed'),
                 edit('set',['rows',1,'changed'],value=n),
                 edit('set',['rows',0,'extra'],value={'a':[n,n+1]}),
                 edit('delete',['rows',0]),
                 edit('set',['new'],value=[{'n':n},{'n':n+1}])]
        check(source, edits)
