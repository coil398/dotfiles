# /// script
# dependencies = []
# ///
"""Construct vendored fixture and split upstream tests; run once from this directory."""
import ast
import difflib
import json
import logging
from pathlib import Path
import shutil

log = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('/home/coil398/.cache/uv/archive-v0/kBnNMtxDik3AFlAwvSTKH/lib/python3.13/site-packages')


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    log.info('start source=%s destination=%s', SOURCE, ROOT)
    package = SOURCE / 'referencing'
    for dest in [ROOT/'private/upstream/referencing', ROOT/'workspace/referencing', ROOT/'private/reference/referencing']:
        shutil.copytree(package, dest, ignore=shutil.ignore_patterns('__pycache__', 'tests'), dirs_exist_ok=True)
    shutil.copytree(package/'tests', ROOT/'private/upstream/referencing/tests', ignore=shutil.ignore_patterns('__pycache__'), dirs_exist_ok=True)
    meta = SOURCE/'referencing-0.37.0.dist-info'
    shutil.copytree(meta, ROOT/'private/upstream/referencing-0.37.0.dist-info', dirs_exist_ok=True)
    shutil.copy2(meta/'licenses/COPYING', ROOT/'workspace/COPYING')
    mutations = {
        'history': ('_core.py', '        if self._base_uri and (not previous or base_uri != self._base_uri):\n            previous = previous.push_front(self._base_uri)\n', ''),
        'pointer': ('_core.py', '''            last = resolver
            resolver = self._specification.maybe_in_subresource(
                segments=segments,
                resolver=resolver,
                subresource=self._specification.create_resource(contents),
            )
            if resolver is not last:
                segments = []
''', ''),
        'dynamic': ('jsonschema.py', '''        for uri, registry in resolver.dynamic_scope():
            try:
                anchor = registry.anchor(uri, self.name).value
            except exceptions.NoSuchAnchor:
                continue
            if isinstance(anchor, DynamicAnchor):
                last = anchor.resource
''', ''),
        'recursive': ('jsonschema.py', '''    if isinstance(resolved.contents, Mapping) and resolved.contents.get(
        "$recursiveAnchor",
    ):
        for uri, _ in resolver.dynamic_scope():
            next_resolved = resolver.lookup(uri)
            if not isinstance(
                next_resolved.contents,
                Mapping,
            ) or not next_resolved.contents.get("$recursiveAnchor"):
                break
            resolved = next_resolved
''', ''),
    }
    (ROOT/'private/mutations.json').write_text(json.dumps(mutations, indent=2)+'\n')
    for filename, old, new in mutations.values():
        target = ROOT/'workspace/referencing'/filename
        text = target.read_text()
        assert text.count(old) == 1
        target.write_text(text.replace(old, new))
    patch = ''
    for filename in ['_core.py', 'jsonschema.py']:
        patch += ''.join(difflib.unified_diff((ROOT/'private/reference/referencing'/filename).read_text().splitlines(True), (ROOT/'workspace/referencing'/filename).read_text().splitlines(True), fromfile='upstream/'+filename, tofile='workspace/'+filename))
    (ROOT/'private/degradation.patch').write_text(patch)
    hidden = ROOT/'private/tests'
    hidden.mkdir(exist_ok=True)
    (hidden/'__init__.py').write_text('')
    tests = ROOT/'workspace/tests'
    tests.mkdir(exist_ok=True)
    for filename in ['test_core.py', 'test_jsonschema.py']:
        tree = ast.parse((package/'tests'/filename).read_text())
        public_tree = ast.parse((package/'tests'/filename).read_text())
        def selected(name):
            return any(part in name for part in ('pointer', 'subresource', 'dynamic', 'recursive', 'repeated_lookup', 'repeated_anchor'))
        def filter_tree(t, want):
            nodes=[]
            for node in t.body:
                if isinstance(node, ast.ClassDef):
                    node.body=[n for n in node.body if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) or not n.name.startswith('test_') or selected(n.name)==want]
                    if not node.body: continue
                elif isinstance(node, ast.FunctionDef) and node.name.startswith('test_') and selected(node.name)!=want:
                    continue
                nodes.append(node)
            t.body=nodes
            return ast.unparse(t)+'\n'
        (tests/filename).write_text(filter_tree(public_tree, False))
        (hidden/('_upstream_'+filename)).write_text(filter_tree(tree, True))
    for filename in ['test_exceptions.py', 'test_retrieval.py']:
        shutil.copy2(package/'tests'/filename, tests/filename)
    (ROOT/'fixture.json').write_text(json.dumps(dict(name='reference_scope',allowed=['referencing/'],public_tests=['tests/'],grading_timeout_s=300,uv_with=['attrs==26.1.0','rpds-py==2026.9.1']), indent=2)+'\n')
    log.info('done mutations=%s upstream_tests=4', len(mutations))

if __name__ == '__main__':
    main()
