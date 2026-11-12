# /// script
# dependencies = []
# ///
"""Build the synthetic fixture from private construction rules, never candidate code."""
from pathlib import Path
import json
import logging

ROOT = Path(__file__).resolve().parents[1]
KINDS = ['text', 'decimal', 'boolean', 'enum', 'scale', 'strings']


def fields(n):
    result = []
    for j in range(4):
        kind = KINDS[(n + j) % 6]
        option = {'text': None, 'decimal': None, 'boolean': ['yes', 'no'] if n % 2 else ['ON', 'OFF'],
                  'enum': {'ready': 'R' + str(n), 'held': 'H' + str(n), 'done': 'D' + str(n)},
                  'scale': [2, 5, 10, 100][(n + j) % 4], 'strings': None}[kind]
        default = {'text': 'unset', 'decimal': -7, 'boolean': False, 'enum': 'held', 'scale': 3, 'strings': ['default']}[kind]
        result.append(dict(source=f'{["title", "count", "active", "state", "amount", "labels"][(n+j)%6]}_{j}',
                           wire=f'{["v", "qty", "flag", "mode"][j]}_{n:03d}', kind=kind, option=option,
                           missing=['omit', 'default', 'required'][(n // 6 + j) % 3],
                           null=['preserve', 'omit', 'reject'][(n // 3 + j) % 3], default=default))
    return result


def golden(value, f):
    # Independent construction oracle: no import of codecs, primitives or reference.
    k, p = f['kind'], f['option']
    if k == 'text':
        return value
    if k == 'decimal':
        return format(value, 'd')
    if k == 'boolean':
        return p[0] if value else p[1]
    if k == 'enum':
        return p[value]
    if k == 'scale':
        return value * p
    return value[:]


def pair(fs, boundary=False):
    source, wire = {}, {}
    for f in fs:
        k = f['kind']
        values = ({'text': '', 'decimal': -100000000000000000003, 'boolean': False,
                   'enum': 'done', 'scale': -17, 'strings': ['', 'a', 'a', '雪']}
                  if boundary else {'text': 'snow 雪', 'decimal': 42, 'boolean': True,
                                    'enum': 'ready', 'scale': 11, 'strings': ['red', 'blue']})
        source[f['source']] = values[k]
        wire[f['wire']] = golden(values[k], f)
    return source, wire


def unit(n, stub=False):
    lines = [f'# unit r{n:03d}']
    for direction in ['encode', 'decode']:
        lines += [f'def {direction}_r{n:03d}(record: dict) -> dict:']
        if stub:
            lines += ['    raise NotImplementedError("r%03d")' % n, '']
            continue
        lines += ['    out = {}']
        for f in fields(n):
            src, dst = (f['source'], f['wire']) if direction == 'encode' else (f['wire'], f['source'])
            lines += [f'    if {src!r} not in record:']
            if f['missing'] == 'required':
                lines += [f'        raise KeyError({src!r})']
            elif f['missing'] == 'omit':
                lines += ['        pass']
            else:
                d = golden(f['default'], f) if direction == 'encode' else f['default']
                lines += [f'        out[{dst!r}] = {d!r}']
            lines += [f'    elif record[{src!r}] is None:']
            lines += {'preserve': [f'        out[{dst!r}] = None'], 'omit': ['        pass'],
                      'reject': [f'        raise ValueError({src!r})']}[f['null']]
            args = '' if f['option'] is None else ', ' + repr(f['option'])
            lines += ['    else:', f'        out[{dst!r}] = {f["kind"]}_{direction}(record[{src!r}]{args})']
        lines += ['    return out', '']
    return '\n'.join(lines) + '\n'


def write(path, text):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')


def hidden(n):
    fs = fields(n)
    normal, encoded = pair(fs)
    boundary, wire_boundary = pair(fs, True)
    module = f'record_codecs.group{(n-1)//6:02d}'
    imp = f'    from {module} import encode_r{n:03d} as encode, decode_r{n:03d} as decode\n'
    s = '"""Spec: docs/SPEC.md §§2–5 and docs/group%02d.md#r%03d."""\n' % ((n-1)//6, n)
    s += '\ndef test_encode_normal():\n' + imp
    s += f'    assert encode({dict(normal, ignored="extra")!r}) == {encoded!r}\n'
    s += '\ndef test_decode_normal():\n' + imp
    s += f'    assert decode({dict(encoded, ignored="extra")!r}) == {normal!r}\n'
    s += '\ndef test_missing_null():\n    import pytest\n' + imp
    for direction, values in [('encode', normal), ('decode', encoded)]:
        for f in fs:
            src, dst = (f['source'], f['wire']) if direction == 'encode' else (f['wire'], f['source'])
            expected = dict(encoded if direction == 'encode' else normal)
            missing_input = dict(values)
            del missing_input[src]
            if f['missing'] == 'required':
                s += f'    with pytest.raises(KeyError) as error:\n        {direction}({missing_input!r})\n    assert error.value.args == ({src!r},)\n'
            else:
                if f['missing'] == 'omit':
                    del expected[dst]
                else:
                    expected[dst] = golden(f['default'], f) if direction == 'encode' else f['default']
                s += f'    assert {direction}({missing_input!r}) == {expected!r}\n'
                if f['kind'] == 'strings' and f['missing'] == 'default':
                    s += f'    result = {direction}({missing_input!r})\n    result[{dst!r}].append("changed")\n    assert {direction}({missing_input!r}) == {expected!r}\n'
            null_input = dict(values, **{src: None})
            expected = dict(encoded if direction == 'encode' else normal)
            if f['null'] == 'reject':
                s += f'    with pytest.raises(ValueError) as error:\n        {direction}({null_input!r})\n    assert error.value.args == ({src!r},)\n'
            else:
                if f['null'] == 'omit':
                    del expected[dst]
                else:
                    expected[dst] = None
                s += f'    assert {direction}({null_input!r}) == {expected!r}\n'
    s += '\ndef test_boundary_nonmutation():\n    from copy import deepcopy\n' + imp
    for direction, inp, expected in [('encode', boundary, wire_boundary), ('decode', wire_boundary, boundary)]:
        s += f'    value = {inp!r}\n    before = deepcopy(value)\n    result = {direction}(value)\n    assert result == {expected!r}\n    assert value == before\n    assert result is not value\n'
        for f in fs:
            if f['kind'] == 'strings':
                src, dst = (f['source'], f['wire']) if direction == 'encode' else (f['wire'], f['source'])
                s += f'    assert result[{dst!r}] is not value[{src!r}]\n    result[{dst!r}].append("changed")\n    assert value == before\n'
    zero_source, zero_wire = {}, {}
    for f in fs:
        value = {'text': '', 'decimal': 0, 'boolean': False, 'enum': 'held', 'scale': 0, 'strings': []}[f['kind']]
        zero_source[f['source']] = value
        zero_wire[f['wire']] = golden(value, f)
    s += f'    assert encode({zero_source!r}) == {zero_wire!r}\n    assert decode({zero_wire!r}) == {zero_source!r}\n'
    return s


def main():
    write('fixture.json', json.dumps(dict(name='record_codecs', axes=['volume'], allowed=['record_codecs/'], public_tests=['tests/'], grading_timeout_s=300), indent=2) + '\n')
    write('task.md', '''Implement all 192 record formats in the record_codecs package, following docs/SPEC.md and the field tables linked from docs/INDEX.md. Each format provides encode_rNNN(record) and decode_rNNN(payload); the finished dispatch API is encode(format_id, record) / decode(format_id, payload). The six primitives and two additional worked examples are complete. Implement every graded format r001–r192. Generation scripts and shared implementation are permitted. Only record_codecs/ may change; do not edit docs or public tests. Run from workspace root: `uv run -q --no-project --with pytest python -m pytest -q tests/`. Do not commit. Return changed files, test results and anything unverified.
''')
    write('workspace/README.md', '''# Record codecs

Read docs/INDEX.md and docs/SPEC.md. The 32 group modules each contain six independent format pairs. record_codecs/primitives.py and record_codecs/examples.py are complete. The package dispatch imports only the requested group, and no group imports another group. All runtime code uses Python's standard library. Public tests contain one literal example per format.
''')
    write('workspace/docs/SPEC.md', '''# Record format specification

## 1. API and scope

There are 192 graded formats r001–r192, six per group module. Each has encode_rNNN(record: dict) -> dict and decode_rNNN(payload: dict) -> dict. The package API is encode(format_id, record) and decode(format_id, payload). Unknown format IDs raise KeyError. No group is imported until requested. examples.py contains two additional, ungraded formats.

## 2. Field tables

Each row in the linked group tables defines one field, giving source key, wire key, conversion, missing policy and null policy. Encode reads source keys and writes wire keys; decode reverses those keys. Only the four specified output keys may appear; unknown input keys are ignored. Field order is table order. Inputs contain valid values for the declared conversions, apart from missing or None values described below; malformed non-null values are outside this task.

## 3. Conversions

text: preserve the string exactly, including empty and Unicode strings.
decimal: encode a signed integer as its canonical base-10 string (zero is "0", no plus sign or padding); decode the canonical string to an integer. Integers have arbitrary precision.
boolean: the table supplies [true_token, false_token]; encode True/False to those exact strings, decode them to bool.
enum: the table supplies a source-to-wire map; encode by that map, decode by its inverse.
scale: the table supplies a positive integer multiplier; encode by multiplication, decode by exact integer division. Wire inputs are divisible by the multiplier. No floating point is used.
strings: copy the list of strings, preserving empty strings, Unicode, duplicates and order; an empty list stays empty.

## 4. Missing and null

Apply policies independently in both directions before conversion. missing=omit means do not emit the field; missing=required raises KeyError with the missing input key as its only argument. missing=default(value) is specified in SOURCE representation: encode emits its converted wire value, decode emits the source default. Each list default is a fresh copy on each call. None is not missing. null=preserve emits None without conversion; null=omit emits no key; null=reject raises ValueError with that direction's input key as its only argument. Process fields in table order if several errors are possible.

## 5. Ownership and boundary values

Neither direction mutates its input dictionary or any list within it. Each call returns a fresh dictionary; every emitted string list (including defaults) is independent of the input and of other calls. Negative integers, zero, arbitrarily large integers, empty strings and lists, duplicate strings, False and every listed enum member are supported.
''')
    write('workspace/record_codecs/__init__.py', '''"""Lazy, complete format dispatch; no runtime schema registry."""
from importlib import import_module

FORMATS = tuple(f"r{n:03d}" for n in range(1, 193))


def encode(format_id: str, record: dict) -> dict:
    if format_id not in FORMATS:
        raise KeyError(format_id)
    module = import_module(f".group{(int(format_id[1:]) - 1) // 6:02d}", __name__)
    return getattr(module, "encode_" + format_id)(record)


def decode(format_id: str, payload: dict) -> dict:
    if format_id not in FORMATS:
        raise KeyError(format_id)
    module = import_module(f".group{(int(format_id[1:]) - 1) // 6:02d}", __name__)
    return getattr(module, "decode_" + format_id)(payload)
''')
    write('workspace/record_codecs/primitives.py', '''"""Complete conversion primitives for valid non-null values."""
def text_encode(value):
    return value

def text_decode(value):
    return value

def decimal_encode(value):
    return str(value)

def decimal_decode(value):
    return int(value)

def boolean_encode(value, tokens):
    return tokens[0] if value else tokens[1]

def boolean_decode(value, tokens):
    return value == tokens[0]

def enum_encode(value, mapping):
    return mapping[value]

def enum_decode(value, mapping):
    return {wire: source for source, wire in mapping.items()}[value]

def scale_encode(value, multiplier):
    return value * multiplier

def scale_decode(value, multiplier):
    return value // multiplier

def strings_encode(value):
    return list(value)

def strings_decode(value):
    return list(value)
''')
    # The worked examples use the exact same four-field policy structure as graded units.
    examples = unit(193).replace('r193', 'example_a') + unit(194).replace('r194', 'example_b')
    imports = 'from .primitives import (' + ', '.join(k+'_'+d for k in KINDS for d in ['encode', 'decode']) + ')\n\n'
    write('workspace/record_codecs/examples.py', imports + examples)
    index = '# Format index\n\nSee [SPEC.md](SPEC.md) for all common policies.\n\n| ID | Signatures | Module | Field table |\n|---|---|---|---|\n'
    public = '"""One public example per graded format, plus worked-example checks."""\n'
    for group in range(32):
        nums = range(group*6+1, group*6+7)
        write(f'workspace/record_codecs/group{group:02d}.py', imports + ''.join(unit(n, True) for n in nums))
        write(f'private/reference/record_codecs/group{group:02d}.py', imports + ''.join(unit(n) for n in nums))
        doc = '# Group %02d\n\nCommon rules: [SPEC.md](SPEC.md), especially §§2–5.\n' % group
        for n in nums:
            index += f'| r{n:03d} | encode_r{n:03d}(record), decode_r{n:03d}(payload) -> dict | record_codecs/group{group:02d}.py | [r{n:03d}](group{group:02d}.md#r{n:03d}) |\n'
            doc += f'\n## r{n:03d}\n\n| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |\n|---|---|---|---|---|\n'
            for f in fields(n):
                conv = f['kind'] + ('' if f['option'] is None else ' ' + json.dumps(f['option'], ensure_ascii=False))
                missing = f['missing'] + ('(' + json.dumps(f['default']) + ')' if f['missing'] == 'default' else '')
                doc += f'| `{f["source"]}` | `{f["wire"]}` | {conv} | {missing} | {f["null"]} |\n'
            a,b = pair(fields(n))
            public += f'\ndef test_r{n:03d}():\n    from record_codecs import encode, decode\n    assert encode("r{n:03d}", {a!r}) == {b!r}\n    assert decode("r{n:03d}", {b!r}) == {a!r}\n'
            write(f'private/tests/test_r{n:03d}.py', hidden(n))
        write(f'workspace/docs/group{group:02d}.md', doc)
    write('workspace/docs/INDEX.md', index)
    for n, name in [(193, 'example_a'), (194, 'example_b')]:
        a,b = pair(fields(n))
        public += f'\ndef test_{name}():\n    from record_codecs.examples import encode_{name}, decode_{name}\n    assert encode_{name}({a!r}) == {b!r}\n    assert decode_{name}({b!r}) == {a!r}\n'
    write('workspace/tests/test_public.py', public)
    logging.info('built root=%s modules=32 units=192 fields=768 hidden_cases=768', ROOT)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    main()
