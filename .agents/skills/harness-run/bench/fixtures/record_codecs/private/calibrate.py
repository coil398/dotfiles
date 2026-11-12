# /// script
# dependencies = []
# ///
"""Execute and record offline volume-fixture acceptance; no model invocation."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import importlib.util
import json
import logging
import os
import random
import shutil
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT.parents[1] / 'bench.py'
LOG = logging.getLogger('record-codecs-calibration')
CMD = ['uv', 'run', '--offline', '-q', '--no-project', '--with', 'pytest', 'python', '-m', 'pytest', '-q']
NAMES = ['encode_normal', 'decode_normal', 'missing_null', 'boundary_nonmutation']
spec = importlib.util.spec_from_file_location('fixture_build', ROOT / 'private/build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def prepare(output, label, reference=False):
    dest = output / label
    shutil.copytree(ROOT / 'workspace', dest, ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
    if reference:
        shutil.copytree(ROOT / 'private/reference', dest, dirs_exist_ok=True)
    shutil.copytree(ROOT / 'private/tests', dest / 'tests_hidden', ignore=shutil.ignore_patterns('__pycache__'))
    return dest


def run_suite(dest, label='hidden', targets=None, seed=0):
    targets = targets or ['tests_hidden']
    xml = dest / f'{label}.xml'
    command = CMD + targets + ['--tb=no', '--junitxml=' + str(xml)]
    started = time.perf_counter()
    proc = subprocess.run(command, cwd=dest, env={**os.environ, 'PYTHONHASHSEED': str(seed), 'PYTHONDONTWRITEBYTECODE': '1'}, capture_output=True, text=True, timeout=300)
    (dest / f'{label}.stdout').write_text(proc.stdout)
    (dest / f'{label}.stderr').write_text(proc.stderr)
    assert xml.exists(), (dest, proc.returncode, proc.stderr[-1000:])
    areas, signature = {}, []
    for c in ET.parse(xml).iter('testcase'):
        area = c.get('classname').split('.')[-1].removeprefix('test_')
        status = next((t for t in ['failure', 'error', 'skipped'] if c.find(t) is not None), 'passed')
        areas.setdefault(area, dict(passed=0, total=0, failed=0, errors=0, skipped=0))
        a = areas[area]
        a['total'] += 1
        a[{'passed': 'passed', 'failure': 'failed', 'error': 'errors', 'skipped': 'skipped'}[status]] += 1
        signature.append([area, c.get('name'), status])
    totals = {k: sum(a[k] for a in areas.values()) for k in ['passed', 'total', 'failed', 'errors', 'skipped']}
    if targets != ['tests']:
        assert len(areas) == 192 and all(a['total'] == 4 for a in areas.values()), (dest, totals)
    result = dict(returncode=proc.returncode, totals=totals, areas=areas, signature=sorted(signature),
                  elapsed_s=time.perf_counter()-started, hashseed=seed, command=command)
    LOG.info('graded label=%s suite=%s seed=%d totals=%s elapsed_s=%.3f', dest.name, label, seed, totals, result['elapsed_s'])
    return result


def restore(dest, n):
    path = dest / 'record_codecs' / f'group{(n-1)//6:02d}.py'
    with path.open('a') as out:
        out.write('\n' + build.unit(n))


def mutation(output, n):
    dest = prepare(output, f'mutation-r{n:03d}', reference=True)
    path = dest / 'record_codecs' / f'group{(n-1)//6:02d}.py'
    with path.open('a') as out:
        out.write('\n' + build.unit(n, stub=True))
    r = run_suite(dest)
    assert r['returncode'] == 1
    assert r['areas'][f'r{n:03d}']['failed'] == 4, (n, r['areas'][f'r{n:03d}'])
    assert r['totals'] == dict(passed=764, total=768, failed=4, errors=0, skipped=0), (n, r['totals'])
    return n, r


def main():
    output = Path(tempfile.mkdtemp(prefix='record-codecs-calibration-', dir='/home/coil398/.ai-pir-runs/benchv2'))
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
                        handlers=[logging.StreamHandler(), logging.FileHandler(output / 'calibrate.log')])
    LOG.info('start root=%s output=%s units=192 cases=768', ROOT, output)
    results = {'output': str(output), 'command': CMD}
    # Execute the exact required harness check after the final fixture generation.
    command = ['python3', str(BENCH), '--self-check', '--tasks', 'record_codecs', '--out', str(output / 'self-check')]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=300)
    (output / 'self-check.stdout').write_text(proc.stdout)
    (output / 'self-check.stderr').write_text(proc.stderr)
    assert proc.returncode == 0, proc.stderr[-2000:]
    results['self_check'] = dict(command=command, returncode=proc.returncode, table=(output / 'self-check/self-check.md').read_text())
    reference = prepare(output, 'reference', reference=True)
    public = run_suite(reference, label='public', targets=['tests'])
    assert public['returncode'] == 0 and public['totals']['passed'] == 194
    results['public'] = public
    runs = []
    for i, seed in enumerate([0, 1, 2, 3, 17, 42, 99, 101, 65535, 4294967295]):
        targets = [f'tests_hidden/test_r{n:03d}.py::test_{name}' for n in range(1,193) for name in NAMES]
        random.Random(seed).shuffle(targets)
        r = run_suite(reference, label=f'determinism-{i:02d}', targets=targets, seed=seed)
        assert r['returncode'] == 0 and r['totals']['passed'] == 768
        if runs:
            assert r['signature'] == runs[0]['signature']
        runs.append(r)
    results['determinism'] = runs
    baseline = prepare(output, 'baseline')
    import_command = ['uv', 'run', '--offline', '-q', '--no-project', '--with', 'pytest', 'python', '-c',
                      'import importlib, pytest; import record_codecs as c; '
                      '[importlib.import_module("record_codecs.group%02d" % i) for i in range(32)]; '
                      'assert len(c.FORMATS)==192; print("offline imports: 32 modules, 192 formats")']
    offline = subprocess.run(import_command, cwd=baseline, capture_output=True, text=True, timeout=60)
    assert offline.returncode == 0, offline.stderr
    results['offline_import'] = dict(command=import_command, returncode=offline.returncode, stdout=offline.stdout)
    r = run_suite(baseline)
    assert r['totals'] == dict(passed=0, total=768, failed=768, errors=0, skipped=0)
    results['baseline'] = r
    partial = []
    for count in [48, 96, 144]:
        dest = prepare(output, f'partial-{count}')
        for n in range(1, count+1):
            restore(dest, n)
        r = run_suite(dest)
        assert r['totals'] == dict(passed=count*4, total=768, failed=(192-count)*4, errors=0, skipped=0)
        assert all(a['passed'] == (4 if int(area[1:]) <= count else 0) for area, a in r['areas'].items())
        partial.append(dict(restored=count, score=r['totals']['passed']/768, result=r))
    results['partial_restoration'] = partial
    # Run every mutation against all areas, not just its own file.
    mutations = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(mutation, output, n) for n in range(1,193)]
        for job in as_completed(jobs):
            n, result = job.result()
            mutations[f'r{n:03d}'] = result
    results['mutations'] = mutations
    broken = prepare(output, 'syntax-isolation', reference=True)
    (broken / 'record_codecs/group00.py').write_text('def broken(:\n')
    r = run_suite(broken)
    assert r['totals'] == dict(passed=744, total=768, failed=24, errors=0, skipped=0)
    results['syntax_isolation'] = r
    (output / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    report = '# record_codecs calibration\n\n'
    report += f'Artifacts: `{output}`. Reproduce with `uv run {ROOT}/private/calibrate.py`.\n\n'
    report += 'Construction source: `private/build.py`; regenerate with `uv run private/build.py` from the fixture root. The private source emits workspace docs, stubs, reference and literal tests. No candidate implementation is used to compute any expected value.\n\n'
    report += '## Harness self-check\n\n`' + ' '.join(command) + '`\n\n' + results['self_check']['table'] + '\n'
    report += '## Offline grading and structure\n\nAll manual grading runs copy pristine workspace, overlay reference only where requested, then copy private/tests into tests_hidden. Both suites use the harness command with `--offline` added (and `--tb=no` for concise failures). No external runtime dependency; pytest resolves from the local uv cache.\n\n'
    report += '- Reference public: 194/194 (192 graded-format examples plus two worked examples).\n- Reference hidden: 192 areas × 4 cases = 768/768, JUnit verified on every run.\n- Baseline hidden: 0/768, 768 call-time NotImplementedError failures, zero collection errors/skips.\n- Offline import: all 32 baseline group modules and pytest imported successfully.\n- Syntax isolation: corrupt group00 yields 24 failed cases in r001–r006, other 744 pass, zero collection errors.\n- 768 field rows in 32 public tables; 192 entries and signatures in docs/INDEX.md. Dispatch is complete and lazy. Primitives and two additional worked examples are implemented. No executable field registry, private material or upstream/cache copies in workspace.\n\n'
    report += '## Partial restoration\n\n| Restored units | Hidden passed/total | Score |\n|---|---:|---:|\n'
    for p in partial:
        report += f'| {p["restored"]}/192 | {p["result"]["totals"]["passed"]}/768 | {p["score"]:.2f} |\n'
    report += '\nEvery restored area passes 4/4; every remaining area fails 4/4.\n\n## Determinism\n\n| Run | PYTHONHASHSEED | Passed/total | Order |\n|---|---:|---:|---|\n'
    for i,r in enumerate(runs):
        report += f'| {i+1} | {r["hashseed"]} | 768/768 | shuffled all 768 node IDs with seed {r["hashseed"]} |\n'
    report += '\nAll ten complete (area, test name, outcome) signatures are identical.\n\n## Per-unit mutation isolation\n\nEach mutation independently replaces both functions of the named unit with call-time NotImplementedError stubs in a fresh reference workspace. The entire 768-case suite runs each time.\n\n| Unit | Target failed | Other cases passed | Collection errors/skips |\n|---|---:|---:|---:|\n'
    for n in range(1,193):
        report += f'| r{n:03d} | 4/4 | 764/764 | 0/0 |\n'
    report += '\n## Assertion → public specification mapping\n\nAll four cases per unit import the target within the test function. Normal encode/decode use independent literal goldens rather than round trips. The golden construction uses formatting/slicing/integer arithmetic and explicit maps without importing reference or primitives.\n\n| Area | Field table | Assertion mapping |\n|---|---|---|\n'
    for n in range(1,193):
        report += f'| r{n:03d} | docs/group{(n-1)//6:02d}.md#r{n:03d} (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |\n'
    report += '\n## Constraints and remaining uncertainty\n\nThe original contract addendum names other fixtures and requests 5–10 cases there; the volume design and assigned task explicitly require 4 cases here, so record_codecs has exactly four. The volume acceptance overrides the original baseline 10–40% band with 0.0–0.05; measured baseline is 0.0. No network, sleep, wall-clock assertion or third-party runtime package is used. Per-run elapsed time is recorded only as calibration metadata, not a score. No actual model trial or ability discrimination is measured by this fixture acceptance. All requested fixture checks executed; nothing unverified within the requested checks.\n'
    (ROOT / 'private/calibration.md').write_text(report)
    LOG.info('done output=%s reference=1 baseline=0 partial=0.25,0.50,0.75 mutations=%d determinism_runs=10', output, len(mutations))


if __name__ == '__main__':
    main()
