import pytest
from tagged_regex import compile, search, fullmatch, ParseError


def test_literal():
    m = search('ab', 'zabz')
    assert m.span() == (1, 3)
    assert m.group() == 'ab'
    assert fullmatch('ab', 'zabz') is None


def test_empty():
    assert search('', 'x').span() == (0, 0)
    assert fullmatch('', '').groups() == ()


def test_choices():
    p = compile('(a|aa)')
    assert p.search('aa').groups() == ('a',)
    assert p.fullmatch('aa').groups() == ('aa',)


def test_lazy():
    assert search('(a+?)(a*)', 'aaa').groups() == ('a', 'aa')


def test_history():
    m = fullmatch('(a(b)?)+', 'aba')
    assert m.groups() == ('a', 'b')
    assert m.span(2) == (1, 2)


def test_nullable():
    assert fullmatch('(a?)*', 'a').groups() == ('',)


def test_class():
    assert fullmatch('[^a-c]+', 'z\n').span() == (0, 2)
    assert search('.', '\n') is None


def test_parser():
    with pytest.raises(ParseError):
        compile('(?=a)')
