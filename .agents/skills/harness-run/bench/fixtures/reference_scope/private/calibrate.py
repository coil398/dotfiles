# /// script
# dependencies = []
# ///
"""Run bench-equivalent commands on fresh disposable grading workspaces."""
import argparse
import json
import logging
from pathlib import Path
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
LOG = logging.getLogger(__name__)
COMMAND = ['uv', 'run', '--offline', '-q', '--no-project', '--with', 'pytest', '--with', 'attrs==26.1.0', '--with', 'rpds-py==2026.9.1', 'python', '-m', 'pytest', '-q']


def score(path):
    areas = {}
    signature = []
    for case in ET.parse(path).getroot().iter('testcase'):
        area = case.get('classname').split('.')[-1].removeprefix('test_')
        passed = not any(case.find(tag) is not None for tag in ('failure', 'error', 'skipped'))
        row = areas.setdefault(area, {'passed': 0, 'total': 0, 'errors': 0, 'skipped': 0})
        row['passed'] += passed
        row['total'] += 1
        row['errors'] += case.find('error') is not None
        row['skipped'] += case.find('skipped') is not None
        signature.append((area, case.get('name'), passed))
    return areas, sorted(signature)


def grade(out, name, reference=True, mutation=None):
    dest = out/name
    ws = dest/'ws'
    shutil.copytree(ROOT/'workspace', ws, ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
    if reference:
        shutil.copytree(ROOT/'private/reference', ws, dirs_exist_ok=True)
    shutil.copytree(ROOT/'private/tests', ws/'tests_hidden', ignore=shutil.ignore_patterns('__pycache__'))
    if mutation:
        filename, old, new = mutation
        path = ws/'referencing'/filename
        original = path.read_text()
        assert original.count(old) == 1
        path.write_text(original.replace(old, new))
    results = {}
    for kind, target in [('public', 'tests/'), ('hidden', 'tests_hidden')]:
        xml = (dest/f'{kind}.xml').resolve()
        start = time.monotonic()
        proc = subprocess.run(COMMAND + [target, f'--junitxml={xml}'], cwd=ws, capture_output=True, text=True, timeout=300)
        (dest/f'{kind}.stdout').write_text(proc.stdout)
        (dest/f'{kind}.stderr').write_text(proc.stderr)
        assert proc.returncode in (0, 1), (name, kind, proc.returncode, proc.stdout[-2000:], proc.stderr[-500:])
        areas, signature = score(xml)
        results[kind] = dict(areas=areas, signature=signature, passed=sum(x['passed'] for x in areas.values()), total=sum(x['total'] for x in areas.values()), command=COMMAND+[target, f'--junitxml={xml}'])
        LOG.info('graded name=%s kind=%s passed=%s total=%s elapsed_s=%.3f', name, kind, results[kind]['passed'], results[kind]['total'], time.monotonic()-start)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    args.out.mkdir(parents=True, exist_ok=False)
    LOG.info('start out=%s fixture=%s', args.out, ROOT)
    result = {'reference': []}
    for i in range(10):
        run = grade(args.out, f'reference-{i}')
        assert run['public']['passed'] == run['public']['total'] == 170
        assert run['hidden']['passed'] == run['hidden']['total'] == 30
        assert all(x['total'] == 6 for x in run['hidden']['areas'].values())
        if result['reference']:
            assert run['hidden']['signature'] == result['reference'][0]['hidden']['signature']
        result['reference'].append(run)
    result['baseline'] = grade(args.out, 'baseline', reference=False)
    mutations = json.loads((ROOT/'private/mutations.json').read_text())
    mutations = {'pointer': mutations['pointer'], 'base_uri': ['_core.py', 'return evolve(self, base_uri=urljoin(self._base_uri, id))', 'return evolve(self, base_uri=id)'], 'dynamic': mutations['dynamic'], 'recursive': mutations['recursive'], 'sequential': mutations['history']}
    result['mutations'] = {}
    for area, mutation in mutations.items():
        run = grade(args.out, 'mutation-'+area, mutation=mutation)
        assert run['hidden']['areas'][area]['passed'] < 6
        result['mutations'][area] = dict(edit=mutation, result=run)
    ws = args.out/'reference-0/ws'
    command = COMMAND[:COMMAND.index('python')] + ['python', '-c', 'import pathlib, referencing, attrs, rpds; assert pathlib.Path(referencing.__file__).is_relative_to(pathlib.Path.cwd()); print("offline local import OK")']
    proc = subprocess.run(command, cwd=ws, capture_output=True, text=True, check=True)
    result['offline'] = dict(command=command, stdout=proc.stdout, returncode=proc.returncode)
    result['out'] = str(args.out)
    (args.out/'results.json').write_text(json.dumps(result, indent=2)+'\n')
    (ROOT/'private/results.json').write_text(json.dumps(result, indent=2)+'\n')
    LOG.info('done reference_runs=10 mutations=5 offline=%s', proc.stdout.strip())

if __name__ == '__main__':
    main()
