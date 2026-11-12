# /// script
# dependencies = []
# ///
"""Reproduce fixture acceptance in disposable grading copies, without models."""
import json
import logging
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

F = Path(__file__).resolve().parents[1]
ROOT = Path('/home/coil398/.ai-pir-runs/benchv2')
LOG = logging.getLogger('toml_edit_batch.calibrate')
MUTATIONS = {
    'semantics': ('parent[target] = deepcopy(edit["value"])', 'parent[target] = 0'),
    'rename': ('replacement._original = leading + replacement.as_string() + trailing', 'replacement._original = replacement.as_string()'),
    'fragments': ('enumerate(body._body)', 'enumerate(body._body[:1])'),
    'layout': ('return result\n', 'return parse(__import__("tomlkit").dumps(result.unwrap()))\n'),
    'isolation': ('result = deepcopy(document)', 'result = document'),
    'validation': ('if isinstance(part, int) and part < 0:', 'if False:'),
}


def counts(path):
    rows = {}
    signature = []
    for case in ET.parse(path).getroot().iter('testcase'):
        area = case.attrib.get('classname', '').split('.')[-1].removeprefix('test_')
        state = next((s for s in ('failure', 'error', 'skipped') if case.find(s) is not None), 'passed')
        row = rows.setdefault(area, dict(passed=0, total=0, failed=0, errors=0, skipped=0))
        row['total'] += 1
        row[{'failure':'failed', 'error':'errors'}.get(state, state)] += 1
        signature.append((area, case.attrib['name'], state))
    return rows, sorted(signature)


def run(label, reference=True, mutation=None, public=False, offline=False):
    with tempfile.TemporaryDirectory(prefix='toml-cal-', dir=ROOT) as tmp:
        ws = Path(tmp)
        shutil.copytree(F/'workspace', ws, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        if reference:
            shutil.copytree(F/'private/reference', ws, dirs_exist_ok=True)
        shutil.copytree(F/'private/tests', ws/'tests_hidden', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        if mutation:
            before, after = MUTATIONS[mutation]
            target = ws/'tomlkit/batch.py'
            source = target.read_text()
            assert source.count(before) == 1, (mutation, source.count(before))
            target.write_text(source.replace(before, after))
        command = ['uv','run'] + (['--offline'] if offline else []) + ['-q','--no-project','--with','pytest','python','-m','pytest','-q','tests/' if public else 'tests_hidden','--junitxml=result.xml']
        proc = subprocess.run(command,cwd=ws,text=True,capture_output=True,timeout=300)
        xml = ws/'result.xml'
        assert xml.exists(), proc.stderr[-2000:]
        rows, signature = counts(xml)
        LOG.info('graded label=%s passed=%s total=%s status=%s',label,sum(r['passed'] for r in rows.values()),sum(r['total'] for r in rows.values()),proc.returncode)
        if reference and not mutation and proc.returncode:
            raise RuntimeError(proc.stdout[-6000:])
        return dict(areas=rows, status=proc.returncode, signature=signature)


def main():
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    results = {'public':run('public',public=True), 'baseline':run('baseline',reference=False), 'runs':[], 'mutations':{}}
    for i in range(10):
        results['runs'].append(run(f'reference-{i+1}'))
    assert all(r['signature']==results['runs'][0]['signature'] for r in results['runs'])
    assert all(r['passed']==8 and r['total']==8 for r in results['runs'][0]['areas'].values())
    for area in MUTATIONS:
        result = run(f'mutation-{area}',mutation=area)
        assert result['areas'][area]['passed'] < 8, area
        results['mutations'][area]=result
    results['offline']=run('offline-public',public=True,offline=True)
    with tempfile.TemporaryDirectory(prefix='toml-offline-', dir=ROOT) as tmp:
        shutil.copytree(F/'workspace',tmp,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        proc=subprocess.run(['uv','run','--offline','-q','--no-project','--with','pytest','python','-c','import tomlkit,pytest; assert tomlkit.__version__ == "0.15.2"; assert callable(tomlkit.apply_edits); print(tomlkit.__version__)'],cwd=tmp,text=True,capture_output=True,timeout=60,check=True)
        results['offline_import']=proc.stdout.strip()
    (F/'private/results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n')
    print('Acceptance completed; results saved to private/results.json')


if __name__=='__main__':
    main()
