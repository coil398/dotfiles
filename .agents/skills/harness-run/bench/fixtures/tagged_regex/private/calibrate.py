# /// script
# dependencies = []
# ///
"""Reproduce fixture acceptance using the bench grading commands, without models."""
from pathlib import Path
import json
import logging
import shutil
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(tempfile.mkdtemp(prefix='tagged-calibration-', dir='/home/coil398/.ai-pir-runs/benchv2'))
LOG = logging.getLogger('tagged-calibrate')
CMD = ['uv', 'run', '-q', '--no-project', '--with', 'pytest', 'python', '-m', 'pytest', '-q']
MUTATIONS = {
    'atoms': ("return char != '\\n'", 'return True'),
    'priority': ("stack.append((inst[2], tags, marks))\n                stack.append((inst[1], tags, marks))", "stack.append((inst[1], tags, marks))\n                stack.append((inst[2], tags, marks))"),
    'captures': ("close = emit(('save', 2 * node[1] + 1, tail))", "close = tail"),
    'nullable': ("target = inst[3] if marks[inst[1]] == pos else inst[2]", 'target = inst[3] if marks[inst[1]] != pos else inst[2]'),
    'differential': ("return inside != node[1]", 'return inside == node[1]'),
    'performance': ("if not full and best is None or full and pos == 0:", 'if pos == 0:'),
}


def grade(label, reference=True, mutation=None, public=False):
    dest = OUTPUT / label
    shutil.copytree(ROOT / 'workspace', dest, ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
    if reference:
        shutil.copytree(ROOT / 'private/reference', dest, dirs_exist_ok=True)
    shutil.copytree(ROOT / 'private/tests', dest / 'tests_hidden', ignore=shutil.ignore_patterns('__pycache__'))
    if mutation:
        file = dest / 'tagged_regex/engine.py'
        old, new = MUTATIONS[mutation]
        source = file.read_text()
        assert source.count(old) == 1, mutation
        file.write_text(source.replace(old, new))
    result = {}
    for suite in (['tests', 'tests_hidden'] if public else ['tests_hidden']):
        xml = dest / (suite + '.xml')
        started = time.perf_counter()
        command = CMD + [suite, '--junitxml=' + str(xml)]
        p = subprocess.run(command, cwd=dest, capture_output=True, text=True, timeout=300)
        (dest / (suite + '.stdout')).write_text(p.stdout)
        (dest / (suite + '.stderr')).write_text(p.stderr)
        assert xml.exists(), (label, p.stderr)
        cases = ET.parse(xml).findall('.//testcase')
        counts = {}
        signature = []
        for case in cases:
            area = case.attrib['classname'].split('.')[-1].removeprefix('test_')
            status = 'passed' if len(case) == 0 else case[0].tag
            counts.setdefault(area, {'passed': 0, 'total': 0})
            counts[area]['total'] += 1
            counts[area]['passed'] += status == 'passed'
            signature.append((area, case.attrib['name'], status))
        result[suite] = {'returncode': p.returncode, 'counts': counts, 'signature': sorted(signature), 'elapsed_s': time.perf_counter()-started}
        LOG.info('graded label=%s suite=%s returncode=%s counts=%s elapsed_s=%.3f', label, suite, p.returncode, counts, result[suite]['elapsed_s'])
    return result


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)sZ %(levelname)s %(message)s', handlers=[logging.StreamHandler(), logging.FileHandler(OUTPUT / 'calibration.log')])
    logging.Formatter.converter = time.gmtime
    LOG.info('start root=%s output=%s', ROOT, OUTPUT)
    runs = [grade('reference-%02d' % i, public=(i==0)) for i in range(10)]
    assert all(r['tests_hidden']['signature'] == runs[0]['tests_hidden']['signature'] for r in runs)
    assert all(r['tests_hidden']['returncode'] == 0 for r in runs)
    assert runs[0]['tests']['returncode'] == 0
    baseline = grade('baseline', reference=False, public=True)
    mutations = {area: grade('mutation-' + area, mutation=area) for area in MUTATIONS}
    for area, result in mutations.items():
        assert result['tests_hidden']['counts'][area]['passed'] < 10, area
    dest = OUTPUT / 'reference-00'
    offline_command = ['uv','run','--offline','-q','--no-project','--with','pytest','python','-c','import tagged_regex, pytest; assert tagged_regex.fullmatch("(a?)*", "aa").groups() == ("",)']
    offline = subprocess.run(offline_command, cwd=dest, capture_output=True, text=True, timeout=60)
    assert offline.returncode == 0, offline.stderr
    # Measure the exact workload launched by each hidden performance test.
    timings = []
    for i in range(10):
        p = subprocess.run(['uv','run','-q','--no-project','--with','pytest','python','-c', f'import time; from tests_hidden.helpers import performance; t=time.perf_counter(); performance({i}); print(time.perf_counter()-t)'], cwd=dest, capture_output=True,text=True,timeout=20)
        assert p.returncode == 0, p.stderr
        timings.append(float(p.stdout))
    assert max(timings) * 10 < 8, timings
    # Additional algorithm mutation: preserve ordered semantics, remove state merging.
    mutant_dir = OUTPUT / 'mutation-backtracking'
    shutil.copytree(dest, mutant_dir, ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
    target = mutant_dir / 'tagged_regex/engine.py'
    target.write_text(target.read_text() + '\n' + (ROOT / 'private/backtracking_mutant.py').read_text())
    small = subprocess.run(CMD + ['tests', 'tests_hidden', '-k', 'not performance', '--junitxml=' + str(mutant_dir / 'small.xml')], cwd=mutant_dir, capture_output=True, text=True, timeout=30)
    assert small.returncode == 0, small.stdout[-2000:]
    # Match the grading subprocess command and limit exactly for case 0.
    interpreter = subprocess.check_output(['uv','run','-q','--no-project','--with','pytest','python','-c','import sys; print(sys._base_executable)'], cwd=dest, text=True).strip()
    probe = [interpreter,'-c', 'from tagged_regex import search; assert search("(a|aa)*b", "a"*12000) is None']
    started = time.perf_counter()
    try:
        large = subprocess.run(probe, cwd=mutant_dir, capture_output=True, text=True, timeout=8)
    except subprocess.TimeoutExpired:
        algorithm_mutation = {'small_returncode':small.returncode, 'small_cases':58, 'performance_case':0, 'status':'timeout', 'limit_s':8, 'elapsed_s':time.perf_counter()-started}
    else:
        raise AssertionError(('backtracking mutation did not time out', large.returncode))
    LOG.info('algorithm_mutation result=%s', algorithm_mutation)
    result = {'output': str(OUTPUT), 'command': CMD, 'reference_runs':runs, 'baseline':baseline, 'mutations':mutations, 'offline': {'command':offline_command,'returncode':offline.returncode}, 'performance_seconds':timings, 'performance_limit_s':8, 'algorithm_mutation':algorithm_mutation, 'oracle_python':subprocess.check_output([interpreter, '--version'], text=True).strip()}
    (ROOT / 'private/results.json').write_text(json.dumps(result, indent=2) + '\n')
    LOG.info('done reference_runs=10 baseline=%s mutation_count=%d offline=%d performance_max_s=%.4f limit_s=8', baseline['tests_hidden']['counts'],len(mutations),offline.returncode,max(timings))


if __name__ == '__main__':
    main()
