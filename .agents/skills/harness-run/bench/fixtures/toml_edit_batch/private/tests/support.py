import copy
import tomllib
import tomlkit


def edit(op, path, **kw):
    return dict(op=op, path=path, **kw)


def check(source, edits, expected=None):
    original = tomlkit.parse(source)
    plain = tomllib.loads(source)
    # Independent value oracle: native TOML values, no TOMLKit internals.
    oracle = copy.deepcopy(plain)
    for e in edits:
        parent = oracle
        for k in e['path'][:-1]:
            parent = parent[k]
        k = e['path'][-1]
        if e['op'] == 'set':
            parent[k] = copy.deepcopy(e['value'])
        elif e['op'] == 'delete':
            del parent[k]
        else:
            old = parent.copy()
            parent.clear()
            parent.update((e['new_key'] if key == k else key, val) for key,val in old.items())
    out = tomlkit.apply_edits(original, iter(edits))
    assert isinstance(out, tomlkit.TOMLDocument)
    assert out is not original
    assert out.unwrap() == oracle
    assert tomllib.loads(out.as_string()) == oracle
    assert original.as_string() == source
    assert original.unwrap() == plain
    if expected is not None:
        assert out.as_string() == expected
    return out
