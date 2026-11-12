# /// script
# dependencies = []
# ///
"""Reproduce reference, baseline, determinism and independent mutation checks."""
import json
import logging
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET

FIXTURE = Path(__file__).resolve().parents[1]
RUNROOT = Path('/home/coil398/.ai-pir-runs/benchv2')
COMMAND = ['uv', 'run', '-q', '--no-project', '--with', 'pytest', 'python', '-m', 'pytest', '-q']


def prepare(root, reference):
    shutil.copytree(FIXTURE / 'workspace', root)
    if reference:
        shutil.copytree(FIXTURE / 'private/reference', root, dirs_exist_ok=True)
    shutil.copytree(FIXTURE / 'private/tests', root / 'tests_hidden')


def grade(root, target, label):
    xml = root.parent / (label + '.xml')
    result = subprocess.run(COMMAND + [target, '--junitxml=' + str(xml)], cwd=root,
                            capture_output=True, text=True, timeout=300)
    (root.parent / (label + '.stdout')).write_text(result.stdout)
    (root.parent / (label + '.stderr')).write_text(result.stderr)
    cases = ET.parse(xml).findall('.//testcase')
    scores = {}
    signature = []
    for case in cases:
        area = case.attrib['classname'].split('.')[-1].removeprefix('test_')
        passed = not any(case.find(x) is not None for x in ('failure','error','skipped'))
        row = scores.setdefault(area, [0,0])
        row[0] += int(passed)
        row[1] += 1
        signature.append((area, case.attrib['name'], passed))
    logging.info('graded label=%s exit=%s scores=%s', label, result.returncode, scores)
    return scores, sorted(signature)


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    out = Path(tempfile.mkdtemp(prefix='sat-calibration-', dir=RUNROOT))
    records = {'output':str(out), 'command':COMMAND, 'runs':[]}
    ref = out / 'reference' / 'workspace'
    ref.parent.mkdir()
    prepare(ref, True)
    records['public'], _ = grade(ref, 'tests', 'public')
    records['reference'], signature = grade(ref, 'tests_hidden', 'hidden')
    assert all(p == t == 6 for p,t in records['reference'].values())
    timings = []
    for case in range(6):
        t = time.monotonic()
        result = subprocess.run(['uv','run','--offline','-q','--no-project','python','-c',
            f'from tests_hidden.support import workload; workload({case})'], cwd=ref,
            capture_output=True, text=True, timeout=8)
        elapsed = time.monotonic()-t
        assert result.returncode == 0, result.stderr
        timings.append(elapsed)
    records['performance_seconds'] = timings
    records['performance_deadline_s'] = 8
    assert 8 >= 10 * max(timings), timings
    logging.info('performance timings_s=%s deadline_s=8', timings)
    records['runs'].append(records['reference'])
    for i in range(1,10):
        root = out / f'repeat-{i}' / 'workspace'
        root.parent.mkdir()
        prepare(root, True)
        scores, sig = grade(root, 'tests_hidden', 'hidden')
        assert sig == signature
        records['runs'].append(scores)
    root = out / 'baseline' / 'workspace'
    root.parent.mkdir()
    prepare(root, False)
    records['baseline_public'], _ = grade(root, 'tests', 'public')
    records['baseline'], _ = grade(root, 'tests_hidden', 'hidden')
    mutations = {
        'sat': ('search.py', 'return {v: values[v] > 0 for v in range(1, nvars + 1)}',
                'return {v: False for v in range(1, nvars + 1)}'),
        'unsat': ('search.py', 'if not limits:\n                return None',
                  'if not limits:\n                return {v: False for v in range(1, nvars + 1)}'),
        'assumptions': ('api.py', 'tuple(self._clauses), self.nvars, assumptions',
                       'tuple(self._clauses), self.nvars, ()'),
        'incremental': ('api.py', 'self._clauses.append(clause)',
                        'self._clauses[:] = [clause]'),
        'performance': ('search.py', None, None),
    }
    records['mutations'] = {}
    for area, (file, old, new) in mutations.items():
        root = out / ('mutation-' + area) / 'workspace'
        root.parent.mkdir()
        prepare(root, True)
        target = root / 'incremental_sat' / file
        if old is None:
            target.write_text((FIXTURE / 'workspace/incremental_sat/search.py').read_text())
        else:
            src = target.read_text()
            assert src.count(old) == 1
            target.write_text(src.replace(old,new))
        scores, _ = grade(root, 'tests_hidden/test_' + area + '.py', 'hidden')
        assert scores[area][0] < scores[area][1]
        records['mutations'][area] = {'scores':scores, 'file':file,'old':old,'new':new}
    offline = subprocess.run(['uv','run','--offline','-q','--no-project','--with','pytest',
        'python','-c','import pytest, incremental_sat; assert incremental_sat.Solver().solve() == {}'],
        cwd=ref, capture_output=True, text=True)
    assert offline.returncode == 0, offline.stderr
    records['offline'] = 'passed: pytest and package imported, empty solver executed'
    (out / 'results.json').write_text(json.dumps(records, indent=2))
    logging.info('done results=%s', out / 'results.json')


if __name__ == '__main__':
    main()
