import json
from pathlib import Path
from ._graphs import graph, transcript
from . import _upstream_test_core as core
from . import _upstream_test_jsonschema as schemas

EXPECTED = json.loads(Path(__file__).with_name('_expected.json').read_text())
UPSTREAM = {
    'pointer': [(core.TestResource, 'test_pointer_to_mapping'), (core.TestResource, 'test_pointer_to_array'), (core.TestResource, 'test_root_pointer'), (core.TestResolver, 'test_lookup_non_existent_pointer'), (core.TestResolver, 'test_lookup_non_existent_pointer_to_array_index'), (core.TestResolver, 'test_lookup_pointer_to_empty_string'), (core.TestResolver, 'test_lookup_non_existent_pointer_to_empty_string'), (core.TestResolver, 'test_lookup_invalid_JSON_pointerish_anchor')],
    'base_uri': [(core.TestResolver, 'test_in_subresource'), (core.TestResolver, 'test_in_pointer_subresource'), (core.TestResource, 'test_subresource_with_different_specification')],
    'dynamic': [(None, 'test_lookup_trivial_dynamic_ref'), (None, 'test_multiple_lookup_trivial_dynamic_ref'), (None, 'test_multiple_lookup_dynamic_ref_to_nondynamic_ref')],
    'recursive': [(None, 'test_lookup_trivial_recursive_ref'), (None, 'test_lookup_recursive_ref_to_bool'), (None, 'test_multiple_lookup_recursive_ref_to_bool'), (None, 'test_multiple_lookup_recursive_ref_with_nonrecursive_ref')],
    'sequential': [(core.TestResolver, 'test_dynamic_scope'), (core.TestResolver, 'test_repeated_lookup_from_retrieved_resource'), (core.TestResolver, 'test_repeated_anchor_lookup_from_retrieved_resource')],
}


def check(area, seed):
    for variant in range(12):
        actual = transcript(graph(area, seed, variant))
        expected = EXPECTED[area][seed][variant]
        if area in ('pointer', 'base_uri'):
            actual = [{k: v for k, v in step.items() if k != 'scope'} for step in actual]
            expected = [{k: v for k, v in step.items() if k != 'scope'} for step in expected]
        assert actual == expected, (area, seed, variant)
    for cls, method in UPSTREAM[area]:
        getattr(schemas if cls is None else cls(), method)()
    if area == 'base_uri':
        core.TestRegistry().test_crawl_finds_a_subresource()
        core.TestResource().test_subresources_delegates_to_specification()
        core.TestResolver().test_lookup_subresource()
        for thing in core.TestOpaqueSpecification.THINGS:
            core.TestOpaqueSpecification().test_no_subresources(thing)
        for specification in (schemas.referencing.jsonschema.DRAFT202012, schemas.referencing.jsonschema.DRAFT201909, schemas.referencing.jsonschema.DRAFT7, schemas.referencing.jsonschema.DRAFT6):
            for value in (True, False):
                schemas.test_subresources_of_bool(specification, value)
