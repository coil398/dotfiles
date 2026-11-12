# /// script
# dependencies = []
# ///
"""Reproduce the contract's isolated grading flow and single-site mutations."""
from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MUTATIONS = {
    'routing': ('source.py', '        self.calls.append(cursor)',
                '        cursor = cursor or None\n        self.calls.append(cursor)'),
    'duplicates': ('state.py', '        if event["id"] in self.applied_ids:\n            return False\n', ''),
    'revisions': ('state.py', 'if revision <=', 'if revision <'),
    'tombstones': ('state.py', '            self.values.pop(key, None)',
                   '            self.values.pop(key, None)\n            self.revisions.pop(key, None)'),
    'failures': ('sink.py', '        if self.calls == self.fail_at:\n            raise',
                 '        if self.calls == self.fail_at:\n            self.sink.apply(event)\n            raise'),
    'checkpoints': ('engine.py', '            for event in events:',
                    '            self.checkpoint.save(next_cursor)\n            for event in events:'),
    'ownership': ('sink.py', 'return deepcopy(self._state.values.get(key))',
                  'return self._state.values.get(key)'),
    'restart_terminal': ('engine.py', '            self.checkpoint.save(next_cursor)',
                         '            if next_cursor is not None:\n                self.checkpoint.save(next_cursor)'),
}


def measure(directory, target, label, output):
    report = output / (label + '.xml')
    command = ['uv', 'run', '-q', '--no-project', '--with', 'pytest', 'python',
               '-m', 'pytest', '-q', target, '--junitxml=' + str(report)]
    result = subprocess.run(command, cwd=directory, capture_output=True, text=True, timeout=300)
    (output / (label + '.log')).write_text(result.stdout + result.stderr)
    root = ET.parse(report).getroot()
    areas = {}; outcomes = []
    for case in root.iter('testcase'):
        name = case.attrib['classname'].rsplit('.', 1)[-1].removeprefix('test_')
        passed = not any(case.find(tag) is not None for tag in ('failure', 'error', 'skipped'))
        counts = areas.setdefault(name, [0, 0]); counts[0] += passed; counts[1] += 1
        outcomes.append((case.attrib['classname'], case.attrib['name'], passed))
    assert result.returncode in (0, 1), (label, result.returncode, result.stdout[-2000:])
    return {'exit': result.returncode, 'areas': areas,
            'passed': sum(x[0] for x in areas.values()),
            'total': sum(x[1] for x in areas.values()), 'outcomes': sorted(outcomes)}


def prepare(directory, reference):
    shutil.copytree(ROOT / 'workspace', directory)
    if reference:
        shutil.copytree(ROOT / 'private/reference', directory, dirs_exist_ok=True)
    shutil.copytree(ROOT / 'private/tests', directory / 'tests_hidden')


def main():
    output = ROOT / 'private/results'
    output.mkdir(exist_ok=True)
    results = {}
    with tempfile.TemporaryDirectory(prefix='.grading-', dir=ROOT/'private') as temporary:
        base = Path(temporary)
        ref = base/'reference'; prepare(ref, True)
        results['reference_public'] = measure(ref, 'tests', 'reference_public', output)
        results['reference_hidden'] = measure(ref, 'tests_hidden', 'reference_hidden', output)
        print('reference', results['reference_public']['passed'], results['reference_hidden']['passed'], flush=True)
        assert results['reference_public']['passed'] == results['reference_public']['total'] == 10
        assert results['reference_hidden']['passed'] == results['reference_hidden']['total'] == 40
        assert len(results['reference_hidden']['areas']) == 8
        assert all(total == 5 for passed, total in results['reference_hidden']['areas'].values())
        baseline = base/'baseline'; prepare(baseline, False)
        results['baseline_public'] = measure(baseline,'tests','baseline_public',output)
        results['baseline_hidden'] = measure(baseline,'tests_hidden','baseline_hidden',output)
        print('baseline', results['baseline_hidden']['areas'], flush=True)
        assert 0.1 <= results['baseline_hidden']['passed']/40 <= 0.4
        results['mutations'] = {}
        for area, (name, old, new) in MUTATIONS.items():
            directory = base/area; prepare(directory, True)
            path = directory/'sync_replay'/name
            text = path.read_text(); assert text.count(old) == 1, (area, old)
            path.write_text(text.replace(old,new))
            result = measure(directory,'tests_hidden/test_'+area+'.py','mutation_'+area,output)
            assert result['total'] == 5 and result['passed'] < 5, area
            result['mutation'] = {'file': name, 'old': old, 'new': new}
            results['mutations'][area] = result
            print('mutation', area, result['passed'], '/5', flush=True)
        results['determinism'] = []
        for index in range(10):
            directory = base/('repeat'+str(index)); prepare(directory,True)
            result = measure(directory,'tests_hidden','determinism_'+str(index+1),output)
            assert result['outcomes'] == results['reference_hidden']['outcomes']
            results['determinism'].append([result['passed'],result['total']])
        print('determinism', results['determinism'], flush=True)
    (output/'summary.json').write_text(json.dumps(results,indent=2)+'\n')


if __name__ == '__main__':
    main()
