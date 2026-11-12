# /// script
# dependencies = []
# ///
"""Execute all volume-fixture acceptance checks using disposable grading copies."""
import ast
import json
import logging
import os
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
UNITS = json.loads((ROOT / 'private/units.json').read_text())
LOGGER = logging.getLogger(__name__)
IGNORE = shutil.ignore_patterns('__pycache__', '.pytest_cache', '.git')


def workspace(out, label, restored=80, mutation=None, broken=False):
    target = out / label / 'ws'
    shutil.copytree(ROOT / 'workspace', target, ignore=IGNORE)
    # Overlay each correct unit separately, including a half-restored two-function module.
    for module in range(1, 41):
        rel = Path('ops') / f'm{module:02d}.py'
        source = (ROOT / 'private/reference' / rel).read_text()
        tree = ast.parse(source)
        lines = source.splitlines(keepends=True)
        for node in reversed(tree.body):
            unit_index = next(i for i, u in enumerate(UNITS) if u['name'] == node.name)
            if unit_index >= restored or node.name == mutation:
                lines[node.body[0].lineno-1:node.end_lineno] = ['    raise NotImplementedError\n']
        (target / rel).write_text(''.join(lines))
    if broken:
        (target / 'ops/m01.py').write_text('def broken(:\n')
    shutil.copytree(ROOT / 'private/tests', target / 'tests_hidden', ignore=IGNORE)
    return target


def run_suite(ws, label, targets, seed='0'):
    xml = ws.parent / f'{label}.xml'
    cmd = ['uv', 'run', '--offline', '-q', '--no-project', '--with', 'pytest',
           'python', '-m', 'pytest', '-q', *targets, f'--junitxml={xml}']
    env = dict(os.environ, PYTHONHASHSEED=str(seed), PYTHONDONTWRITEBYTECODE='1', UV_OFFLINE='1')
    start = time.monotonic()
    proc = subprocess.run(cmd, cwd=ws, env=env, capture_output=True, text=True, timeout=300)
    (ws.parent / f'{label}.stdout').write_text(proc.stdout)
    (ws.parent / f'{label}.stderr').write_text(proc.stderr)
    assert proc.returncode in (0, 1), (label, proc.returncode, proc.stderr)
    areas = {}
    signatures = []
    for case in ET.parse(xml).getroot().iter('testcase'):
        area = case.get('classname').split('.')[-1].removeprefix('test_')
        status = next((s for s in ('failure', 'error', 'skipped') if case.find(s) is not None), 'passed')
        counts = areas.setdefault(area, dict(total=0, passed=0, failure=0, error=0, skipped=0))
        counts['total'] += 1
        counts[status] += 1
        signatures.append([area, case.get('name'), status])
    result = dict(command=cmd, seed=seed, elapsed_s=round(time.monotonic()-start, 4),
                  exit_code=proc.returncode, areas=areas, signature=sorted(signatures))
    result['passed'] = sum(a['passed'] for a in areas.values())
    result['total'] = sum(a['total'] for a in areas.values())
    result['score'] = result['passed'] / result['total']
    LOGGER.info('suite_done label=%s seed=%s passed=%d total=%d elapsed_s=%.3f', label, seed, result['passed'], result['total'], result['elapsed_s'])
    return result


def check_hidden(result, missing):
    assert set(result['areas']) == {u['name'] for u in UNITS}
    for name, counts in result['areas'].items():
        assert counts == dict(total=4, passed=0 if name in missing else 4,
                              failure=4 if name in missing else 0, error=0, skipped=0), (name, counts)


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    out = Path(tempfile.mkdtemp(prefix='bulk-ops-calibration-', dir='/home/coil398/.ai-pir-runs/benchv2'))
    LOGGER.info('calibration_start output=%s units=%d', out, len(UNITS))
    results = dict(output=str(out))
    self_check_cmd = ['python3', str(ROOT.parents[1] / 'bench.py'), '--self-check',
                      '--tasks', 'bulk_ops', '--out', str(out / 'self-check')]
    self_check = subprocess.run(self_check_cmd, capture_output=True, text=True, timeout=300)
    (out / 'self-check.stdout').write_text(self_check.stdout)
    (out / 'self-check.stderr').write_text(self_check.stderr)
    assert self_check.returncode == 0, self_check.stderr[-2000:]
    results['self_check'] = dict(command=self_check_cmd, exit_code=self_check.returncode,
                                stdout=self_check.stdout, stderr=self_check.stderr)
    LOGGER.info('self_check_done output=%s exit_code=0', out / 'self-check')
    ref = workspace(out, 'reference')
    results['reference_public'] = run_suite(ref, 'public', ['tests/'])
    assert results['reference_public']['passed'] == results['reference_public']['total'] == 80
    results['reference_hidden'] = run_suite(ref, 'hidden', ['tests_hidden/'])
    check_hidden(results['reference_hidden'], set())
    baseline = workspace(out, 'baseline', restored=0)
    # Import every module without invoking functions, offline in the grading directory.
    cmd = ['uv', 'run', '--offline', '-q', '--no-project', '--with', 'pytest', 'python', '-c',
           "import importlib, pytest; [importlib.import_module(f'ops.m{i:02d}') for i in range(1,41)]"]
    imported = subprocess.run(cmd, cwd=baseline, capture_output=True, text=True, timeout=300)
    assert imported.returncode == 0, imported.stderr
    results['offline_import'] = dict(command=cmd, exit_code=imported.returncode, modules=40)
    results['baseline_public'] = run_suite(baseline, 'public', ['tests/'])
    results['baseline_hidden'] = run_suite(baseline, 'hidden', ['tests_hidden/'])
    check_hidden(results['baseline_hidden'], {u['name'] for u in UNITS})
    results['partial'] = []
    for count in (20,40,60):
        ws = workspace(out, f'partial-{count}', restored=count)
        result = run_suite(ws, 'hidden', ['tests_hidden/'])
        check_hidden(result, {u['name'] for u in UNITS[count:]})
        assert result['score'] == count/80
        results['partial'].append(dict(restored=count, **result))
    # An odd number of restored functions verifies function-level overlay inside one module.
    ws = workspace(out, 'partial-1', restored=1)
    results['single_restored'] = run_suite(ws, 'hidden', ['tests_hidden/'])
    check_hidden(results['single_restored'], {u['name'] for u in UNITS[1:]})
    results['mutations'] = []
    for u in UNITS:
        ws = workspace(out, 'mutation-'+u['name'], mutation=u['name'])
        result = run_suite(ws, 'hidden', ['tests_hidden/'])
        check_hidden(result, {u['name']})
        results['mutations'].append(dict(unit=u['name'], **result))
        # Persist raw evidence after each completed check.
        (out / 'results.json').write_text(json.dumps(results, indent=2)+'\n')
    ws = workspace(out, 'broken-module', broken=True)
    results['broken_module'] = run_suite(ws, 'hidden', ['tests_hidden/'])
    check_hidden(results['broken_module'], {u['name'] for u in UNITS[:2]})
    results['determinism'] = []
    for seed in (0,1,2,7,42,99,101,31337,65535,2147483647):
        ws = workspace(out, f'determinism-{seed}')
        targets = [f"tests_hidden/test_{u['name']}.py" for u in UNITS]
        random.Random(seed).shuffle(targets)
        result = run_suite(ws, 'hidden', targets, seed=seed)
        check_hidden(result, set())
        assert result['signature'] == results['reference_hidden']['signature']
        results['determinism'].append(result)
    # Ensure no hidden material or dependency cache links leaked into candidate workspace.
    files = [p for p in (ROOT/'workspace').rglob('*') if p.is_file()]
    assert len(list((ROOT/'workspace/ops').glob('m*.py'))) == 40
    assert all(not p.is_symlink() and p.stat().st_nlink == 1 for p in files)
    assert not any(p.name in ('private','reference','tests_hidden','__pycache__') for p in (ROOT/'workspace').rglob('*'))
    results['workspace_audit'] = dict(files=len(files), symlinks=0, hardlinks=0, private_material=False)
    (out/'results.json').write_text(json.dumps(results, indent=2)+'\n')
    (ROOT/'private/results.json').write_text(json.dumps(results, indent=2)+'\n')
    report = ['# Bulk operations calibration', '', '## Construction and reproduction', '',
              'Synthetic stdlib-only package: 40 independent modules, 80 distinct functions, eight public spec volumes of ten functions and an 80-entry signature index. Each function has one public example and one hidden file containing four parametrized cases. Inputs and expected values are authored literals in build.py, never obtained by running the reference. No upstream/cache source, symlink or hardlink is included in workspace. No uv_with is required.', '',
              'Run `uv run --no-project private/build.py` to regenerate the fixture. Run `uv run --no-project private/calibrate.py` to execute this calibration. The script logs per-suite counts and time, stores JUnit XML and stdout/stderr in disposable grading directories, and checks every area including unchanged areas. This report records executed acceptance checks; results.json contains exact commands, per-case outcomes, seeds and timings.', '',
              f'Latest evidence directory: `{out}`.', '',
              'All calibration grading commands use `uv run --offline -q --no-project --with pytest python -m pytest -q <targets> --junitxml=<path>` from a fresh pristine workspace copy overlaid with reference function bodies and private tests copied to tests_hidden/. Reference and baseline public/hidden commands run separately. Imports inside every hidden test function isolate collection from broken candidate modules. Package imports require stdlib only and pytest is the only test dependency. No network, sleeping, wall-clock scoring, random test data or performance area is used.', '',
              '## Scores', '', '| Variant | Public | Hidden | Score |', '|---|---:|---:|---:|',
              '| Reference | 80/80 | 320/320 | 1.00 |', '| Baseline | 0/80 | 0/320 | 0.00 |',
              '| 20 restored | — | 80/320 | 0.25 |', '| 40 restored | — | 160/320 | 0.50 |', '| 60 restored | — | 240/320 | 0.75 |',
              '| One function restored | — | 4/320 | 0.0125 |', '| One syntactically broken module | — | 312/320 | 0.975 |', '',
              'Reference JUnit verifies exactly 80 areas × 4 cases. Baseline imports all 40 modules successfully offline (exit 0), collects all 320 cases and fails at call time with NotImplementedError, with zero collection errors or skips. Partial restorations restore units in index order. The additional one-function restoration verifies a partially restored two-function module. A syntax error in m01 fails only its eight function cases; the other 312 still pass, with no collection errors.', '',
              '## Mutation isolation', '',
              'Each row is an independent fresh reference with exactly that function body replaced by `raise NotImplementedError`. All four cases of the selected area fail; all 316 cases of the other 79 areas pass. Every row below was executed against the entire hidden suite.', '',
              '| Unit | Target | Others | Total |', '|---|---:|---:|---:|']
    for u in UNITS:
        report.append(f"| {u['id']} {u['name']} | 0/4 | 316/316 | 316/320 |")
    report += ['', '## Determinism', '', 'Each run uses a fresh reference copy and independently shuffled hidden file order. Every run has public-spec literal inputs, all 320 passing hidden cases, no skips/errors, and identical sorted (area, case, status) signatures. The ten run seeds are both PYTHONHASHSEED and the file-order shuffle seed.', '', '| Seed | Hidden |', '|---|---:|']
    report += [f"| {r['seed']} | {r['passed']}/{r['total']} |" for r in results['determinism']]
    report += ['', '## Assertion to public-spec mapping', '', 'Every hidden file asserts its four independent literal golden outputs and output type, preserves a deep copy of arguments (INDEX.md nonmutation rule), compares recursive dictionary insertion order (INDEX.md order rule), and verifies returned container identities are fresh (INDEX.md fresh-container rule). Per-function semantics, valid types/preconditions, empty/boundary values and duplicate/order behavior are in the sections below. Row fixtures have scalar row fields, consistent with the documented shallow-copy rule. No hidden requirement extends the public rules.', '', '| Area (four cases) | Public semantic/type section | Common assertions |', '|---|---|---|']
    for i,u in enumerate(UNITS):
        report.append(f"| {u['name']} | workspace/docs/V{i//10+1}.md §{u['name']} ({u['id']}) | workspace/docs/INDEX.md |")
    report += ['', '## Harness self-check', '', 'Executed command: `' + ' '.join(results['self_check']['command']) + '`. Exit code: 0.', '', results['self_check']['stdout'].strip(), '', '## Unverified', '', 'No acceptance check remains unverified. Comparative model discriminating power, trial token usage and early stopping are not measured by fixture calibration. No commit or publication is performed.', '']
    (ROOT/'private/calibration.md').write_text('\n'.join(report))
    LOGGER.info('calibration_complete output=%s mutations=80 determinism_runs=10', out)

if __name__ == '__main__':
    main()
