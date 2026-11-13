import ast
from pathlib import Path


def _public_functions():
    import shopkit.discounts as m

    tree = ast.parse(Path(m.__file__).read_text())
    fns = [n for n in tree.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")]
    assert {"discounted_price_cents", "display_price"} <= {f.name for f in fns}
    return fns


def _params(fn):
    a = fn.args
    return [p for p in a.posonlyargs + a.args + a.kwonlyargs + [x for x in (a.vararg, a.kwarg) if x]]


def test_fully_annotated():
    for fn in _public_functions():
        assert fn.returns is not None, fn.name
        assert all(p.annotation is not None for p in _params(fn)), fn.name


def test_docstring_summary_line():
    for fn in _public_functions():
        doc = ast.get_docstring(fn)
        assert doc, fn.name
        first = doc.splitlines()[0].strip()
        assert first.endswith("."), fn.name


def test_docstring_sections():
    for fn in _public_functions():
        doc = ast.get_docstring(fn)
        assert doc and "Returns:" in doc, fn.name
        if _params(fn):
            assert "Args:" in doc, fn.name
