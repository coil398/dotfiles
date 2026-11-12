from rpds import HashTrieMap
import pytest
from referencing import Anchor, Registry, Resource, Specification, exceptions
from referencing.jsonschema import DRAFT202012
ID_AND_CHILDREN = Specification(name='id-and-children', id_of=lambda contents: contents.get('ID'), subresources_of=lambda contents: contents.get('children', []), anchors_in=lambda specification, contents: [Anchor(name=name, resource=specification.create_resource(contents=each)) for name, each in contents.get('anchors', {}).items()], maybe_in_subresource=lambda segments, resolver, subresource: resolver.in_subresource(subresource) if not len(segments) % 2 and all((each == 'children' for each in segments[::2])) else resolver)

def blow_up(uri):
    """
    A retriever suitable for use in tests which expect it never to be used.
    """
    raise RuntimeError('This retrieve function expects to never be called!')

class TestRegistry:

    def test_crawl_finds_a_subresource(self):
        child_id = 'urn:child'
        root = ID_AND_CHILDREN.create_resource({'ID': 'urn:root', 'children': [{'ID': child_id, 'foo': 12}]})
        registry = root @ Registry()
        with pytest.raises(LookupError):
            registry[child_id]
        expected = ID_AND_CHILDREN.create_resource({'ID': child_id, 'foo': 12})
        assert registry.crawl()[child_id] == expected

class TestResource:

    def test_subresources_delegates_to_specification(self):
        resource = ID_AND_CHILDREN.create_resource({'children': [{}, 12]})
        assert list(resource.subresources()) == [ID_AND_CHILDREN.create_resource(each) for each in [{}, 12]]

    def test_subresource_with_different_specification(self):
        schema = {'$schema': 'https://json-schema.org/draft/2020-12/schema'}
        resource = ID_AND_CHILDREN.create_resource({'children': [schema]})
        assert list(resource.subresources()) == [DRAFT202012.create_resource(schema)]

    def test_pointer_to_mapping(self):
        resource = Resource.opaque(contents={'foo': 'baz'})
        resolver = Registry().resolver()
        assert resource.pointer('/foo', resolver=resolver).contents == 'baz'

    def test_pointer_to_array(self):
        resource = Resource.opaque(contents={'foo': {'bar': [3]}})
        resolver = Registry().resolver()
        assert resource.pointer('/foo/bar/0', resolver=resolver).contents == 3

    def test_root_pointer(self):
        contents = {'foo': 'baz'}
        resource = Resource.opaque(contents=contents)
        resolver = Registry().resolver()
        assert resource.pointer('', resolver=resolver).contents == contents

class TestResolver:

    def test_lookup_subresource(self):
        root = ID_AND_CHILDREN.create_resource({'ID': 'http://example.com/', 'children': [{'ID': 'http://example.com/a', 'foo': 12}]})
        registry = root @ Registry()
        resolved = registry.resolver().lookup('http://example.com/a')
        assert resolved.contents == {'ID': 'http://example.com/a', 'foo': 12}

    def test_lookup_non_existent_pointer(self):
        resource = Resource.opaque({'foo': {}})
        resolver = Registry({'http://example.com/1': resource}).resolver()
        ref = 'http://example.com/1#/foo/bar'
        with pytest.raises(exceptions.Unresolvable) as e:
            resolver.lookup(ref)
        assert e.value == exceptions.PointerToNowhere(ref='/foo/bar', resource=resource)
        assert str(e.value) == "'/foo/bar' does not exist within {'foo': {}}"

    def test_lookup_non_existent_pointer_to_array_index(self):
        resource = Resource.opaque([1, 2, 4, 8])
        resolver = Registry({'http://example.com/1': resource}).resolver()
        ref = 'http://example.com/1#/10'
        with pytest.raises(exceptions.Unresolvable) as e:
            resolver.lookup(ref)
        assert e.value == exceptions.PointerToNowhere(ref='/10', resource=resource)

    def test_lookup_pointer_to_empty_string(self):
        resolver = Registry().resolver_with_root(Resource.opaque({'': {}}))
        assert resolver.lookup('#/').contents == {}

    def test_lookup_non_existent_pointer_to_empty_string(self):
        resource = Resource.opaque({'foo': {}})
        resolver = Registry().resolver_with_root(resource)
        with pytest.raises(exceptions.Unresolvable, match="^'/' does not exist within {'foo': {}}.*'#'") as e:
            resolver.lookup('#/')
        assert e.value == exceptions.PointerToNowhere(ref='/', resource=resource)

    def test_lookup_invalid_JSON_pointerish_anchor(self):
        resolver = Registry().resolver_with_root(ID_AND_CHILDREN.create_resource({'ID': 'http://example.com/', 'foo': {'bar': 12}}))
        valid = resolver.lookup('#/foo/bar')
        assert valid.contents == 12
        with pytest.raises(exceptions.InvalidAnchor) as e:
            resolver.lookup('#foo/bar')
        assert " '#/foo/bar'" in str(e.value)

    def test_repeated_lookup_from_retrieved_resource(self):
        """
        A (custom-)retrieved resource is added to the registry returned by
        looking it up.
        """
        resource = Resource.opaque(contents={'foo': 'baz'})
        once = [resource]

        def retrieve(uri):
            return once.pop()
        resolver = Registry(retrieve=retrieve).resolver()
        resolved = resolver.lookup('http://example.com/')
        assert resolved.contents == resource.contents
        resolved = resolved.resolver.lookup('http://example.com/')
        assert resolved.contents == resource.contents

    def test_repeated_anchor_lookup_from_retrieved_resource(self):
        resource = Resource.opaque(contents={'foo': 'baz'})
        once = [resource]

        def retrieve(uri):
            return once.pop()
        resolver = Registry(retrieve=retrieve).resolver()
        resolved = resolver.lookup('http://example.com/')
        assert resolved.contents == resource.contents
        resolved = resolved.resolver.lookup('#')
        assert resolved.contents == resource.contents

    def test_in_subresource(self):
        root = ID_AND_CHILDREN.create_resource({'ID': 'http://example.com/', 'children': [{'ID': 'child/', 'children': [{'ID': 'grandchild'}]}]})
        registry = root @ Registry()
        resolver = registry.resolver()
        first = resolver.lookup('http://example.com/')
        assert first.contents == root.contents
        with pytest.raises(exceptions.Unresolvable):
            first.resolver.lookup('grandchild')
        sub = first.resolver.in_subresource(ID_AND_CHILDREN.create_resource(first.contents['children'][0]))
        second = sub.lookup('grandchild')
        assert second.contents == {'ID': 'grandchild'}

    def test_in_pointer_subresource(self):
        root = ID_AND_CHILDREN.create_resource({'ID': 'http://example.com/', 'children': [{'ID': 'child/', 'children': [{'ID': 'grandchild'}]}]})
        registry = root @ Registry()
        resolver = registry.resolver()
        first = resolver.lookup('http://example.com/')
        assert first.contents == root.contents
        with pytest.raises(exceptions.Unresolvable):
            first.resolver.lookup('grandchild')
        second = first.resolver.lookup('#/children/0')
        third = second.resolver.lookup('grandchild')
        assert third.contents == {'ID': 'grandchild'}

    def test_dynamic_scope(self):
        one = ID_AND_CHILDREN.create_resource({'ID': 'http://example.com/', 'children': [{'ID': 'child/', 'children': [{'ID': 'grandchild'}]}]})
        two = ID_AND_CHILDREN.create_resource({'ID': 'http://example.com/two', 'children': [{'ID': 'two-child/'}]})
        registry = [one, two] @ Registry()
        resolver = registry.resolver()
        first = resolver.lookup('http://example.com/')
        second = first.resolver.lookup('#/children/0')
        third = second.resolver.lookup('grandchild')
        fourth = third.resolver.lookup('http://example.com/two')
        assert list(fourth.resolver.dynamic_scope()) == [('http://example.com/child/grandchild', fourth.resolver._registry), ('http://example.com/child/', fourth.resolver._registry), ('http://example.com/', fourth.resolver._registry)]
        assert list(third.resolver.dynamic_scope()) == [('http://example.com/child/', third.resolver._registry), ('http://example.com/', third.resolver._registry)]
        assert list(second.resolver.dynamic_scope()) == [('http://example.com/', second.resolver._registry)]
        assert list(first.resolver.dynamic_scope()) == []

class TestOpaqueSpecification:
    THINGS = [{'foo': 'bar'}, True, 37, 'foo', object()]

    @pytest.mark.parametrize('thing', THINGS)
    def test_no_subresources(self, thing):
        """
        An arbitrary thing has no subresources.
        """
        assert list(Specification.OPAQUE.subresources_of(thing)) == []
