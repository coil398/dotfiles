"""Independent CPython oracle; never copied into the candidate workspace."""
import random
import re
import sys
import subprocess
from tagged_regex import compile


def check(pattern, text):
    candidate, oracle = compile(pattern), re.compile(pattern)
    assert candidate.groups == oracle.groups, pattern
    for method in ('search', 'fullmatch'):
        actual = getattr(candidate, method)(text)
        expected = getattr(oracle, method)(text)
        assert (actual is None) == (expected is None), (pattern, text, method, actual, expected)
        if expected is not None:
            assert actual.string == text
            assert actual.groups() == expected.groups(), (pattern, text, method, actual.groups(), expected.groups())
            assert actual.groups('missing') == expected.groups('missing')
            for group in range(oracle.groups + 1):
                assert actual.span(group) == expected.span(group), (pattern, text, method, group, actual.span(group), expected.span(group))
                assert actual.group(group) == expected.group(group)


def generated(seed, category):
    rng = random.Random(40000 + seed)
    atoms = ['a', 'b', '.', '[ab]', '[^b]', '[a-c]']
    def ast(depth):
        if not depth or rng.random() < .3:
            return rng.choice(atoms)
        kind = rng.randrange(4)
        if kind == 0:
            return '(' + ast(depth-1) + '|' + ast(depth-1) + ')'
        if kind == 1:
            return '(' + ast(depth-1) + ast(depth-1) + ')'
        return '(' + ast(depth-1) + ')' + rng.choice(['*', '+', '?', '*?', '+?', '??'])
    for _ in range(35):
        if category == 'atoms':
            pattern = ''.join(rng.choice(atoms) for _ in range(rng.randrange(5)))
        elif category == 'priority':
            left, right = rng.choice(['a', 'ab', '', 'b']), rng.choice(['aa', 'a', 'b', ''])
            pattern = '(' + left + '|' + right + ')' + rng.choice(['a?', 'b*', '', '.*?'])
        elif category == 'captures':
            pattern = rng.choice(['((a)|(b))*', '(a(b)?)+', '((a|ab)+)(b?)', '((a)?b)*', '(a|(b))*', '((a)+|b)+'])
        elif category == 'nullable':
            pattern = rng.choice(['(a?)*', '(a*)*', '(a*?)*?', '((a?)*)*', '(|a)+', '(a??)*', '((a*)?)+', '(a?|b)*?b?'])
        else:
            pattern = ast(3)
        text = ''.join(rng.choice('aabc\n') for _ in range(rng.randrange(8)))
        for sample in (text, "", "a", "aa", "ab", "aba", "baab", "aaaa"):
            check(pattern, sample)


# Large inputs have analytic answers; CPython's backtracker is not run here.
PERF = [
    ('(a|aa)*b', 'a'*12000, None),
    ('(a|aa)+b', 'a'*12000, None),
    ('(a|aa)*?b', 'a'*12000, None),
    ('(a?)*b', 'a'*12000, None),
    ('(a??)*?b', 'a'*12000, None),
    ('(a|aa)*b', 'a'*12000+'b', (0,12001)),
    ('a*?', 'a'*12000, (0,0)),
    ('[ab]*c', 'a'*12000, None),
    ('(a|aa)+?b', 'a'*12000+'b', (0,12001)),
    ('ab'*90, 'x'*11000+'ab'*90, (11000,11180)),
]


def performance(case):
    # 8 seconds is >=10x the slowest calibrated reference workload, including
    # interpreter startup. The child imports the candidate from the grading cwd.
    source = '''
from tagged_regex import compile
p = compile(PATTERN)
m = p.search(TEXT)
assert (None if m is None else m.span()) == EXPECTED
if EXPECTED is not None and EXPECTED[0] == 0 and EXPECTED[1] > 0:
    assert p.fullmatch(TEXT).span() == EXPECTED
'''
    pattern, text, expected = PERF[case]
    source = source.replace('PATTERN', repr(pattern)).replace('TEXT', repr(text)).replace('EXPECTED', repr(expected))
    result = subprocess.run([sys.executable, '-c', source], capture_output=True, text=True, timeout=8)
    assert result.returncode == 0, result.stderr[-2000:]
