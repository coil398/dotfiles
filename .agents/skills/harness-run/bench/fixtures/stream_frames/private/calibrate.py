"""Reproduce baseline, reference, single-mutant, and determinism acceptance."""
import json
import logging
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / 'private'
LOGGER = logging.getLogger('stream_frames.calibrate')
COMMAND = ['uv', 'run', '-q', '--no-project', '--with', 'pytest', 'python', '-m', 'pytest', '-q']
MUTATIONS = {
    'chunking': ('framing/storage.py', 'self._data.extend(bytes(data))', 'self._data.clear()\n        self._data.extend(bytes(data))'),
    'utf8': ('framing/wire.py', 'payload.decode("utf-8", "strict")', 'payload.decode("utf-8", "replace")'),
    'multiframe': ('framing/decoder.py', 'output.append(decode_payload(payload))', 'output.append(decode_payload(payload))\n                break'),
    'eof': ('framing/decoder.py', 'if self._expected is not None or len(self._queue):', 'if self._expected is not None:'),
    'limits': ('framing/limits.py', 'if length > maximum or length > WIRE_MAXIMUM:', 'if length >= maximum or length > WIRE_MAXIMUM:'),
    'reset': ('framing/decoder.py', 'self._queue.clear()\n        self._expected = None\n        self._failed = False\n        self._finished = False', 'self._queue.clear()'),
    'buffering': ('framing/decoder.py', 'return len(self._queue)', 'return len(self._queue) + (4 if self._expected is not None else 0)'),
    'types_encoding': ('framing/wire.py', 'return len(payload).to_bytes(HEADER_SIZE, "big") + payload', 'return len(text).to_bytes(HEADER_SIZE, "big") + payload'),
}


def replace_once(root, mutation):
    relative, old, new = mutation
    path = root / relative
    text = path.read_text()
    if text.count(old) != 1:
        raise ValueError(f'mutation anchor count for {relative}: {text.count(old)}')
    path.write_text(text.replace(old, new, 1))


def prepare(path, reference):
    shutil.copytree(ROOT/'workspace', path)
    if reference:
        shutil.copytree(PRIVATE/'reference', path, dirs_exist_ok=True)
    shutil.copytree(PRIVATE/'tests', path/'tests_hidden')


def run(path, target, label):
    report = path/'report.xml'
    result = subprocess.run(COMMAND+[target, f'--junitxml={report}'], cwd=path,
                            text=True, capture_output=True, timeout=300)
    (PRIVATE/'results'/f'{label}.log').write_text(result.stdout+result.stderr)
    tree = ET.parse(report)
    counts = {}
    cases = []
    for case in tree.iter('testcase'):
        area = case.attrib['classname'].split('.')[-1].removeprefix('test_')
        passed = not any(case.find(tag) is not None for tag in ('failure', 'error', 'skipped'))
        tally = counts.setdefault(area, {'passed': 0, 'total': 0})
        tally['passed'] += int(passed)
        tally['total'] += 1
        cases.append([area, case.attrib['name'], passed])
    info = {'exit_code': result.returncode, 'areas': counts, 'cases': sorted(cases)}
    LOGGER.info('suite label=%s exit=%d passed=%d total=%d', label, result.returncode,
                sum(v['passed'] for v in counts.values()), sum(v['total'] for v in counts.values()))
    return info


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    (PRIVATE/'results').mkdir(exist_ok=True)
    results = {}
    with tempfile.TemporaryDirectory(prefix='.calibration-', dir=PRIVATE) as temporary:
        scratch = Path(temporary)
        for name, reference in [('reference', True), ('baseline', False)]:
            path = scratch/name
            prepare(path, reference)
            results[name] = {kind: run(path, target, f'{name}-{kind}')
                             for kind, target in [('public', 'tests'), ('hidden', 'tests_hidden')]}
        reference = results['reference']
        assert reference['public']['exit_code'] == reference['hidden']['exit_code'] == 0
        assert len(reference['hidden']['areas']) == 8
        assert all(v == {'passed': 4, 'total': 4} for v in reference['hidden']['areas'].values())
        baseline = results['baseline']['hidden']
        assert baseline['exit_code'] == 1
        assert sum(v['total'] for v in baseline['areas'].values()) == 32
        assert 0.1 <= sum(v['passed'] for v in baseline['areas'].values())/32 <= 0.4
        results['mutations'] = {}
        for area, mutation in MUTATIONS.items():
            path = scratch/('mutant-'+area)
            prepare(path, True)
            replace_once(path, mutation)
            outcome = run(path, 'tests_hidden', 'mutant-'+area)
            assert outcome['exit_code'] == 1
            assert outcome['areas'][area]['total'] == 4
            assert outcome['areas'][area]['passed'] < 4
            results['mutations'][area] = {'mutation': list(mutation), 'result': outcome}
        results['determinism'] = []
        for index in range(10):
            # A fresh grading tree and interpreter each time, no stale module cache.
            path = scratch/f'determinism-{index+1}'
            prepare(path, True)
            outcome = run(path, 'tests_hidden', f'determinism-{index+1}')
            assert outcome == reference['hidden']
            results['determinism'].append(outcome)
    (PRIVATE/'results/summary.json').write_text(json.dumps(results, indent=2)+'\n')
    LOGGER.info('done reference=32/32 mutations=8 determinism=10')


if __name__ == '__main__':
    main()
