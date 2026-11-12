import json
import pytest
from configlayers import load


def test_non_object_root_rejected(tmp_path):
    p=tmp_path/'c.json'; p.write_text('[]')
    with pytest.raises(ValueError, match='object'): load(p)


def test_include_wrong_type_rejected(tmp_path):
    p=tmp_path/'c.json'; p.write_text('{"$include":3}')
    with pytest.raises(ValueError): load(p)


def test_missing_file_remains_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError): load(tmp_path/'absent.json')


def test_input_document_is_not_mutated(tmp_path):
    p=tmp_path/'c.json'; text='{"$include":[],"a":{"b":1}}'; p.write_text(text)
    assert load(p)=={'a':{'b':1}}
    assert json.loads(p.read_text())=={'$include':[],'a':{'b':1}}
