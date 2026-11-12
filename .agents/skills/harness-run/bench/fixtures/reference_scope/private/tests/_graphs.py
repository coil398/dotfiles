"""Seeded graph generator and observable resolution transcript driver."""
import random

from referencing import Registry, exceptions
from referencing.jsonschema import DRAFT4, DRAFT7, DRAFT201909, DRAFT202012, lookup_recursive_ref

SPECS = {'4': DRAFT4, '7': DRAFT7, '2019': DRAFT201909, '2020': DRAFT202012}


def graph(area, seed, variant):
    rng = random.Random(71031 + seed * 199 + variant * 13)
    host = f'https://s{seed}v{variant}.example/'
    tag = 'a' + str(rng.randrange(10000000))
    steps = []
    if area in ('pointer', 'base_uri'):
        dialect = ['4', '7', '2019', '2020'][variant % 4]
        key = 'id' if dialect == '4' else '$id'
        defs = 'definitions' if dialect in ('4', '7') else '$defs'
        root = {key: host + 'root/', 'title': 'root'}
        resources = [[host + 'root/', root]]
        node, uri, pointer = root, host + 'root/', ''
        depth = 2 + rng.randrange(5)
        for i in range(depth):
            name = f'{tag}/{i}~'
            escaped = name.replace('~', '~0').replace('/', '~1')
            # Alternate keyword families, including array-valued schema containers.
            keyword = [defs, 'properties', 'allOf'][i % 3]
            child = {'title': f'node-{i}'}
            if i % 2 == 0 or area == 'base_uri':
                value = f'd{i}/'
                if area == 'base_uri' and i == depth - 1 and variant % 3 == 0:
                    value = host + 'absolute/'
                child[key] = value
                from urllib.parse import urljoin
                uri = urljoin(uri, value)
            if keyword == 'allOf':
                node[keyword] = [child]
                pointer += '/allOf/0'
            else:
                node[keyword] = {name: child}
                pointer += '/' + keyword + '/' + escaped
            node = child
        # A tempting $id in data is not a subresource boundary.
        node['enum'] = [{key: host + 'wrong/', 'title': 'data'}]
        resources.extend([[uri + 'probe', {'title': 'probe-correct'}], [host+'root/probe', {'title': 'probe-root'}]])
        steps = [{'from': 0, 'ref': '#' + pointer}, {'from': 1, 'ref': 'probe'}, {'from': 1, 'ref': '#/title'}, {'from': 0, 'ref': '#' + pointer + '/enum/0'}, {'from': 4, 'ref': 'probe'}, {'from': 1, 'ref': '#/missing'}, {'from': 0, 'ref': '#/title'}]
        return dict(dialect=dialect, resources=resources, base=host+'root/', steps=steps)
    dialect = '2019' if area == 'recursive' else '2020'
    size = 3 + rng.randrange(5)
    uris = [host + f'r{i}/' for i in range(size)]
    resources = []
    for i, uri in enumerate(uris):
        doc = {'$id': uri, 'title': f'r{i}'}
        if area == 'recursive':
            doc['$recursiveAnchor'] = not (variant % 3 == 1 and i == 1)
            if variant % 3 == 2 and i == 0:
                doc = bool(variant % 2)
        else:
            # Intervening ordinary anchors and absent anchors must be skipped.
            if i not in (0, size - 1) and (i + variant) % 3 == 0:
                doc['$anchor'] = tag
            elif i in (0, size - 1) or (i + variant) % 3 == 1:
                if variant % 4 == 3 and i == 0:
                    doc['$defs'] = {'inner': {'$id': uri+'inside/', '$dynamicAnchor': tag, 'title': 'inner'}}
                else:
                    doc['$dynamicAnchor'] = tag
        resources.append([uri, doc])
        resources.append([uri+'probe', {'title': f'probe-{i}'}])
    current = 0
    for uri in uris[1:]:
        steps.append({'from': current, 'ref': uri})
        current += 1
    steps.append({'from': current, **({'recursive': True} if area == 'recursive' else {'ref': '#'+tag})})
    resolved = current + 1
    steps.extend([{'from': resolved, 'ref': 'probe'}, {'from': current, 'ref': '#/missing'}, {'from': 0, 'ref': '#'}])
    if area == 'sequential':
        steps += [{'from': 1, 'ref': uris[1]}, {'from': 1, 'ref': uris[-1]+'#'+tag}, {'from': 0, 'ref': uris[-1]+'#'+tag}, {'from': resolved, 'ref': uris[1]}, {'from': resolved, 'ref': '#'+tag}, {'from': 0, 'ref': 'missing'}, {'from': 0, 'ref': uris[-1]}]
    return dict(dialect=dialect, resources=resources, base=uris[0], steps=steps, retrieve=area=='sequential' and variant%2==1)


def transcript(case):
    spec = SPECS[case['dialect']]
    resources = {uri: spec.create_resource(contents) for uri, contents in case['resources']}
    if case.get('retrieve'):
        def retrieve(uri):
            if uri not in resources:
                raise exceptions.NoSuchResource(ref=uri)
            return resources[uri]
        registry = Registry(retrieve=retrieve).with_resource(case['base'], resources[case['base']])
    else:
        registry = Registry().with_resources(resources.items())
    states = [registry.resolver(case['base'])]
    output = []
    for step in case['steps']:
        source = states[step['from']]
        before = [list(uri for uri, _ in resolver.dynamic_scope()) for resolver in states]
        try:
            resolved = lookup_recursive_ref(source) if step.get('recursive') else source.lookup(step['ref'])
        except exceptions.Unresolvable as error:
            output.append({'error': type(error).__name__, 'ref': error.ref, 'text': str(error), 'scope': [uri for uri, _ in source.dynamic_scope()]})
            states.append(source)
        else:
            output.append({'contents': resolved.contents, 'base': resolved.resolver._base_uri, 'scope': [uri for uri, _ in resolved.resolver.dynamic_scope()]})
            states.append(resolved.resolver)
        after = [list(uri for uri, _ in resolver.dynamic_scope()) for resolver in states[:-1]]
        assert before == after, 'A lookup mutated an existing resolver'
    return output
