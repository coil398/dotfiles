import pytest
from referencing import Registry, Resource, Specification
import referencing.jsonschema

@pytest.mark.parametrize('specification', [referencing.jsonschema.DRAFT202012, referencing.jsonschema.DRAFT201909, referencing.jsonschema.DRAFT7, referencing.jsonschema.DRAFT6])
@pytest.mark.parametrize('value', [True, False])
def test_subresources_of_bool(specification, value):
    assert list(specification.subresources_of(value)) == []

def test_lookup_trivial_dynamic_ref():
    one = referencing.jsonschema.DRAFT202012.create_resource({'$dynamicAnchor': 'foo'})
    resolver = Registry().with_resource('http://example.com', one).resolver()
    resolved = resolver.lookup('http://example.com#foo')
    assert resolved.contents == one.contents

def test_multiple_lookup_trivial_dynamic_ref():
    TRUE = referencing.jsonschema.DRAFT202012.create_resource(True)
    root = referencing.jsonschema.DRAFT202012.create_resource({'$id': 'http://example.com', '$dynamicAnchor': 'fooAnchor', '$defs': {'foo': {'$id': 'foo', '$dynamicAnchor': 'fooAnchor', '$defs': {'bar': True, 'baz': {'$dynamicAnchor': 'fooAnchor'}}}}})
    resolver = Registry().with_resources([('http://example.com', root), ('http://example.com/foo/', TRUE), ('http://example.com/foo/bar', root)]).resolver()
    first = resolver.lookup('http://example.com')
    second = first.resolver.lookup('foo/')
    resolver = second.resolver.lookup('bar').resolver
    fourth = resolver.lookup('#fooAnchor')
    assert fourth.contents == root.contents

def test_multiple_lookup_dynamic_ref_to_nondynamic_ref():
    one = referencing.jsonschema.DRAFT202012.create_resource({'$anchor': 'fooAnchor'})
    two = referencing.jsonschema.DRAFT202012.create_resource({'$id': 'http://example.com', '$dynamicAnchor': 'fooAnchor', '$defs': {'foo': {'$id': 'foo', '$dynamicAnchor': 'fooAnchor', '$defs': {'bar': True, 'baz': {'$dynamicAnchor': 'fooAnchor'}}}}})
    resolver = Registry().with_resources([('http://example.com', two), ('http://example.com/foo/', one), ('http://example.com/foo/bar', two)]).resolver()
    first = resolver.lookup('http://example.com')
    second = first.resolver.lookup('foo/')
    resolver = second.resolver.lookup('bar').resolver
    fourth = resolver.lookup('#fooAnchor')
    assert fourth.contents == two.contents

def test_lookup_trivial_recursive_ref():
    one = referencing.jsonschema.DRAFT201909.create_resource({'$recursiveAnchor': True})
    resolver = Registry().with_resource('http://example.com', one).resolver()
    first = resolver.lookup('http://example.com')
    resolved = referencing.jsonschema.lookup_recursive_ref(resolver=first.resolver)
    assert resolved.contents == one.contents

def test_lookup_recursive_ref_to_bool():
    TRUE = referencing.jsonschema.DRAFT201909.create_resource(True)
    registry = Registry({'http://example.com': TRUE})
    resolved = referencing.jsonschema.lookup_recursive_ref(resolver=registry.resolver(base_uri='http://example.com'))
    assert resolved.contents == TRUE.contents

def test_multiple_lookup_recursive_ref_to_bool():
    TRUE = referencing.jsonschema.DRAFT201909.create_resource(True)
    root = referencing.jsonschema.DRAFT201909.create_resource({'$id': 'http://example.com', '$recursiveAnchor': True, '$defs': {'foo': {'$id': 'foo', '$recursiveAnchor': True, '$defs': {'bar': True, 'baz': {'$recursiveAnchor': True, '$anchor': 'fooAnchor'}}}}})
    resolver = Registry().with_resources([('http://example.com', root), ('http://example.com/foo/', TRUE), ('http://example.com/foo/bar', root)]).resolver()
    first = resolver.lookup('http://example.com')
    second = first.resolver.lookup('foo/')
    resolver = second.resolver.lookup('bar').resolver
    fourth = referencing.jsonschema.lookup_recursive_ref(resolver=resolver)
    assert fourth.contents == root.contents

def test_multiple_lookup_recursive_ref_with_nonrecursive_ref():
    one = referencing.jsonschema.DRAFT201909.create_resource({'$recursiveAnchor': True})
    two = referencing.jsonschema.DRAFT201909.create_resource({'$id': 'http://example.com', '$recursiveAnchor': True, '$defs': {'foo': {'$id': 'foo', '$recursiveAnchor': True, '$defs': {'bar': True, 'baz': {'$recursiveAnchor': True, '$anchor': 'fooAnchor'}}}}})
    three = referencing.jsonschema.DRAFT201909.create_resource({'$recursiveAnchor': False})
    resolver = Registry().with_resources([('http://example.com', three), ('http://example.com/foo/', two), ('http://example.com/foo/bar', one)]).resolver()
    first = resolver.lookup('http://example.com')
    second = first.resolver.lookup('foo/')
    resolver = second.resolver.lookup('bar').resolver
    fourth = referencing.jsonschema.lookup_recursive_ref(resolver=resolver)
    assert fourth.contents == two.contents
