import importlib.util
import json
import sys
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('bench', Path(__file__).resolve().parents[1] / 'bench.py')
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    root = tmp_path / 'fixtures'
    task = root / 'toy'
    for folder in ('workspace/tests', 'workspace/pkg', 'private/tests', 'private/reference/pkg'):
        (task / folder).mkdir(parents=True)
    (task / 'fixture.json').write_text(json.dumps(dict(name='toy', axes=['difficulty', 'complexity'],
                                                     suite='capability', allowed=['pkg/', 'exact.py'],
                                                     public_tests=['tests/'], grading_timeout_s=10)))
    (task / 'task.md').write_text('Fix pkg only')
    (task / 'workspace/pkg/__init__.py').write_text('value = 0\n')
    (task / 'workspace/exact.py').write_text('x = 0\n')
    (task / 'workspace/tests/test_public.py').write_text('def test_public():\n    assert True\n')
    (task / 'private/reference/pkg/__init__.py').write_text('value = 2\n')
    (task / 'private/tests/test_alpha.py').write_text(
        'import pytest\nfrom pkg import value\n'
        '@pytest.mark.parametrize("n", [1, 2])\ndef test_value(n):\n    assert value >= n\n')
    (task / 'private/tests/test_beta.py').write_text(
        'from pkg import value\ndef test_one():\n    assert value == 2\n'
        'def test_two():\n    assert value == 2\n')
    monkeypatch.setattr(bench, 'FIXTURES', root)
    runner = tmp_path / 'fake.py'
    runner.write_text('''import json, os, sys, time
from pathlib import Path
ws = Path(sys.argv[2])
assert not (ws / 'tests_hidden').exists()
assert not (ws / 'private').exists()
assert not (ws / 'fixture.json').exists()
assert not (ws / 'task.md').exists()
mode = os.environ.get('FAKE_MODE', 'good')
(ws / 'pkg/__init__.py').write_text('value = ' + ('1' if mode in ('partial', 'timeout_partial') else '2') + '\\n')
if mode == 'outside': (ws / 'exact.py.bak').write_text('oops')
if mode == 'tamper': (ws / 'tests/test_public.py').write_text('def test_fake(): assert False')
if mode == 'delete': (ws / 'pkg/__init__.py').unlink()
if mode.startswith('timeout'): time.sleep(30)
print(json.dumps({'status': 'completed', 'effort_applied': 'high', 'usage': {'requests': 3, 'total_input': 90, 'output': 10}}))
''')
    monkeypatch.setenv('BENCH_RUNNER_OVERRIDE', str(runner))
    cfg = bench.parse_config('pi:fake:high')
    return task, cfg, tmp_path


def expected(fixture):
    task, _, tmp = fixture
    ref = bench.grade_ref('toy', tmp / 'ref-log')
    return {area: v['total'] for area, v in ref['areas'].items()}


@pytest.mark.parametrize('mode, valid, raw, eligible', [
    ('good', True, 1, 1), ('outside', False, 1, 0), ('tamper', False, 1, 0),
    ('partial', True, .25, .25), ('timeout', True, 1, 1),
    ('timeout_partial', True, .25, .25), ('delete', True, 0, 0)])
def test_trial(fixture, monkeypatch, mode, valid, raw, eligible):
    _, cfg, tmp = fixture
    denom = expected(fixture)
    assert denom == {'alpha': 2, 'beta': 2}  # Includes parametrized cases.
    monkeypatch.setenv('FAKE_MODE', mode)
    r = bench.run_trial(cfg, 0, 'toy', 1, tmp, 1, denom, budget_s=60)
    assert r['valid'] == valid
    assert r['raw_score'] == raw
    assert r['eligible_score'] == eligible
    assert r['status'] == ('timeout' if mode.startswith('timeout') else 'completed')
    assert r['success'] == (mode == 'good')
    assert r['within_budget'] == (mode == 'good')
    assert r['budget_s'] == 60
    assert r['axes'] == ['difficulty', 'complexity']
    assert json.loads((Path(r['trial_dir']) / 'result.json').read_text())['axes'] == r['axes']
    assert not r['grading_infra_failure']
    if mode == 'partial':
        assert r['areas']['alpha']['score'] == .5
        assert r['areas']['beta']['score'] == 0
    if mode == 'tamper':
        assert r['tampered'] == ['tests/test_public.py']
        assert r['tests']['public']['passed'] == 1  # Pristine public test.
    if mode == 'outside':
        assert not (Path(r['trial_dir']) / 'grading/exact.py.bak').exists()
    if not mode.startswith('timeout'):
        assert r['effort_applied'] == 'high'
        assert r['usage']['requests'] == 3
    assert r['duration_s'] >= 0 and r['grading_duration_s'] > 0
    for name in ('public.stdout', 'public.stderr', 'hidden.stdout', 'hidden.stderr'):
        assert (Path(r['trial_dir']) / name).exists()


def test_diff_boundaries_add_delete_commit_and_ignored(fixture):
    _, _, tmp = fixture
    ws = tmp / 'ws'
    base = bench.prepare_workspace('toy', ws)
    (ws / 'exact.py').unlink()
    for rel in ('pkg/new.py', 'pkg_extra.py', 'exact.py.bak', 'tests/new.py', 'ignored.txt'):
        (ws / rel).write_text('x=1')
    (ws / '.gitignore').write_text('ignored.txt\n')
    bench.git(ws, 'add', 'pkg/new.py')
    bench.git(ws, 'commit', '-qm', 'agent')
    changed, tampered, outside = bench.check_diff('toy', ws, base)
    assert 'exact.py' in changed and 'pkg/new.py' in changed
    assert tampered == ['tests/new.py']
    assert set(outside) == {'.gitignore', 'pkg_extra.py', 'exact.py.bak', 'ignored.txt'}
    grading = bench.prepare_grading_workspace('toy', ws, changed, tmp / 'grading')
    assert not (grading / 'exact.py').exists()
    assert (grading / 'pkg/new.py').exists()


def test_skips_errors_uncollected_and_infra(fixture, monkeypatch):
    task, _, tmp = fixture
    denom = expected(fixture)
    (task / 'private/tests/test_alpha.py').write_text(
        'import pytest\n@pytest.mark.skip(reason="skip")\ndef test_skip(): pass\n'
        '@pytest.fixture\ndef broken(): raise ValueError("boom")\ndef test_error(broken): pass\n')
    (task / 'private/tests/test_beta.py').write_text('raise ImportError("agent broke package")\n')
    ws = bench.prepare_grading_workspace('toy', task / 'workspace', [], tmp / 'grade')
    r = bench.run_tests(ws, tmp / 'logs', 'toy', denom)
    assert r['hidden']['total'] == 4 and r['hidden']['passed'] == 0
    assert not r['infra_errors']  # Collection errors are artifact failures.
    # Run without collection abort to verify skip and setup error counters too.
    (ws / 'tests_hidden/test_beta.py').write_text('def test_ok(): assert True\n')
    r = bench.run_tests(ws, tmp / 'logs2', 'toy', denom)
    assert r['hidden']['total'] == 4 and r['hidden']['passed'] == 1
    assert r['areas']['alpha']['skipped'] == 1 and r['areas']['alpha']['errors'] == 1
    monkeypatch.setattr(bench, 'TEST_CMD', ['/nonexistent/bench-test-command'])
    r = bench.run_trial(fixture[1], 0, 'toy', 1, tmp, 2, denom)
    assert r['grading_infra_failure']
    assert r['raw_score'] is None and r['eligible_score'] is None and not r['success']


def test_bad_reference_aborts(fixture):
    task, _, tmp = fixture
    (task / 'private/reference/pkg/__init__.py').write_text('value = 0\n')
    with pytest.raises(RuntimeError, match='reference grading failed: toy'):
        bench.grade_ref('toy', tmp / 'bad-ref')


def test_summary_fixture_mean_and_usage_missing(fixture):
    _, cfg, tmp = fixture
    def row(task, score, tokens):
        return dict(config=cfg['spec'], task=task, axes=['difficulty'], eligible_score=score, success=score == 1,
                    valid=True, status='completed', grading_infra_failure=False,
                    duration_s=2, requests=1, total_input=tokens, output=0 if tokens is not None else None,
                    areas={'alpha': {'score': score}})
    rows = [row('a', 1, 100), row('b', 0, 100), row('b', 0, None)]
    bench.write_summary(rows, [cfg], ['a', 'b'], tmp)
    text = (tmp / 'summary.md').read_text()
    for col in ('平均eligible', 'full-pass率', 'invalid', 'timeout', 'wall中央値', 'requests中央値',
                'total_tokens中央値', 'tokens欠測', '効率', 'grading infra', 'alpha'):
        assert col in text
    overall = next(line for line in text.splitlines() if '| overall |' in line)
    assert '| 0.5000 |' in overall  # Mean of fixture means, not of all trials.
    assert overall.endswith('| - |')  # Missing token denominator is not zero.
    a = next(line for line in text.splitlines() if '| a |' in line)
    assert a.endswith('| 1000.0000 |')
    assert bench.total_tokens(rows[-1]) is None


def test_main_discovery_seed_reference_once_and_selfcheck(fixture, monkeypatch, capsys):
    task, _, tmp = fixture
    real_ref = bench.grade_ref
    calls = []
    def ref(t, out):
        calls.append(t)
        return real_ref(t, out)
    monkeypatch.setattr(bench, 'grade_ref', ref)
    def run(out):
        monkeypatch.setattr(sys, 'argv', ['bench', '--config', 'pi:a:high', '--config', 'pi:b:high',
                                        '--config', 'pi:c:high', '--repeat', '2', '--seed', '7',
                                        '--budget-s', '60', '--out', str(out)])
        bench.main()
        results = [json.loads(x) for x in (out / 'results.jsonl').read_text().splitlines()]
        assert all(r['budget_s'] == 60 and r['within_budget'] for r in results)
        return [r['config'] for r in results]
    order = run(tmp / 'run1')
    assert calls == ['toy']
    assert order == run(tmp / 'run2')
    monkeypatch.delenv('BENCH_RUNNER_OVERRIDE')
    monkeypatch.setattr(bench, 'invoke', lambda *a: pytest.fail('self-check called runner'))
    monkeypatch.setattr(sys, 'argv', ['bench', '--self-check', '--out', str(tmp / 'self')])
    bench.main()
    assert '| toy | 1/1 | 4/4 | 0/4 |' in capsys.readouterr().out
    assert list(bench.load_tasks()) == ['toy']


def test_normalize_effort_and_codex_usage():
    n = bench.normalize_runner({'status': 'completed', 'effort_applied': 'high',
                                'usage': {'input_uncached': 10, 'cache_read': 20, 'output': 5, 'reasoning': 4}}, 1)
    assert n['effort_applied'] == 'high' and bench.total_tokens(n) == 35
    assert bench.total_tokens(bench.normalize_runner({}, 1)) is None
    n = bench.normalize_codex({'wait_status': 'completed', 'done': {'exit': 0},
                              'usage': {'input_tokens': 20, 'output_tokens': 3}}, 2)
    assert n['status'] == 'completed' and bench.total_tokens(n) == 23


def test_case_with_multiple_failure_elements_never_scores_negative():
    case = bench.ET.fromstring('<testcase><failure/><error/></testcase>')
    result = bench.counts([case], 1)
    assert result == dict(passed=0, total=1, failed=1, errors=1, skipped=0)


@pytest.mark.parametrize('packages', [[], ['pytest', 'pytest>=8']])
def test_offline_dependencies_for_reference_and_trial(fixture, monkeypatch, packages):
    task, cfg, tmp = fixture
    manifest = task / 'fixture.json'
    data = json.loads(manifest.read_text())
    if packages:
        data['uv_with'] = packages
        manifest.write_text(json.dumps(data))
    real_popen = bench.subprocess.Popen
    commands = []
    def capture(cmd, *args, **kwargs):
        if cmd[0] == 'uv':
            commands.append(cmd)
        return real_popen(cmd, *args, **kwargs)
    monkeypatch.setattr(bench.subprocess, 'Popen', capture)
    denom = expected(fixture)
    result = bench.run_trial(cfg, 0, 'toy', 1, tmp, 2, denom)
    assert result['eligible_score'] == 1
    assert len(commands) == 4
    prefix = ['uv', 'run', '--offline', '-q', '--no-project', '--with', 'pytest']
    for package in packages:
        prefix += ['--with', package]
    prefix += ['python', '-m', 'pytest', '-q']
    for cmd, target in zip(commands, ['tests/', 'tests_hidden'] * 2):
        assert cmd[:-1] == prefix + [target]
        assert cmd[-1].startswith('--junitxml=')


@pytest.mark.parametrize('budget, within', [(None, None), (2, True), (1.9, False)])
def test_budget_wall_boundary_and_summary(fixture, monkeypatch, budget, within):
    _, cfg, tmp = fixture
    real_normalize = bench.normalize_runner
    monkeypatch.setattr(bench, 'normalize_runner', lambda summary, wall: real_normalize(summary, 2))
    result = bench.run_trial(cfg, 0, 'toy', 1, tmp, 2, expected(fixture), budget_s=budget)
    assert result['eligible_score'] == 1 and result['success']
    assert result['within_budget'] is within
    saved = json.loads((Path(result['trial_dir']) / 'result.json').read_text())
    assert saved['within_budget'] is within and saved['budget_s'] == budget
    bench.write_summary([result], [cfg], ['toy'], tmp)
    summary = (tmp / 'summary.md').read_text()
    assert '予算内完遂' in summary
    rows = [line.split('|')[1:-1] for line in summary.splitlines() if '| toy |' in line or '| overall |' in line]
    for row in rows[:2]:
        assert row[4].strip() == ('-' if within is None else f'{int(within)}/1')


@pytest.mark.parametrize('message', ['TimeoutExpired', 'subprocess timed out after 10 seconds'])
def test_hidden_performance_timeouts(fixture, monkeypatch, message):
    task, cfg, tmp = fixture
    (task / 'private/tests/test_alpha.py').write_text(
        'import pytest\nfrom pkg import value\n'
        '@pytest.mark.parametrize("n", [1, 2])\ndef test_perf(n):\n'
        f'    assert value == 2, {message!r}\n')
    denom = expected(fixture)
    monkeypatch.setenv('FAKE_MODE', 'partial')
    result = bench.run_trial(cfg, 0, 'toy', 1, tmp, 2, denom)
    assert result['eligible_score'] == 0
    assert not result['grading_infra_failure']
    assert result['areas']['alpha']['perf_timeout'] == 2
    assert result['areas']['alpha']['failed'] == 2
    assert result['areas']['beta']['perf_timeout'] == 0
    bench.write_summary([result, result], [cfg], ['toy'], tmp)
    summary = (tmp / 'summary.md').read_text()
    assert '| perf_timeout |' in summary
    assert '| alpha | 0.0 | 4 |' in summary
    assert '| beta | 0.0 | 0 |' in summary


def test_axes_fixture_weighting_nulls_timeouts_and_volume(fixture):
    _, cfg, tmp = fixture

    def result(task, axes, score, success=False, **kwargs):
        return dict(config=cfg['spec'], task=task, axes=axes, eligible_score=score,
                    success=success, valid=kwargs.get('valid', True),
                    status=kwargs.get('status', 'completed'), grading_infra_failure=score is None,
                    duration_s=kwargs.get('wall', 2), total_input=kwargs.get('tokens', 100),
                    output=0, requests=1, areas=kwargs.get('areas', {'a': {'score': score}}))

    rows = [result('a', ['difficulty', 'complexity'], 1, True),
            result('b', ['difficulty'], 0), result('b', ['difficulty'], .5, status='timeout'),
            result('b', ['difficulty'], None, wall=None, tokens=None),
            result('b', ['difficulty'], 0, valid=False),
            result('v1', ['volume'], .5, status='timeout', areas={
                'one': {'score': 1}, 'two': {'score': 0}}),
            result('v2', ['volume'], .75, areas={
                'one': {'score': 1}, 'two': {'score': 1},
                'three': {'score': 1}, 'four': {'score': 0}}),
            result('v2', ['volume'], None, areas={
                name: {'score': None} for name in ('one', 'two', 'three', 'four')})]
    tasks = ['a', 'b', 'v1', 'v2']
    summaries = {r['axis']: r for r in bench.axis_summaries(rows, tasks, planned_trials=4)}
    d = summaries['difficulty']
    assert d['score'] == pytest.approx((1 + .5 / 3) / 2)
    assert d['full_pass'] == .5  # Fixture mean; infra null is excluded.
    assert d['fixtures'] == ['a', 'b']
    assert (d['scored'], d['planned'], d['score_missing'], d['trial_missing']) == (4, 8, 1, 3)
    assert (d['timeout'], d['invalid'], d['infra']) == (1, 1, 1)
    assert (d['wall'], d['wall_missing'], d['tokens'], d['tokens_missing']) == (2, 1, 100, 1)
    assert summaries['complexity']['score'] == 1
    assert summaries['volume']['score'] == .625  # Equal fixture weight, independent of area count.
    assert summaries['volume']['full_pass'] == 0  # Timeout partial scores remain scored trials.
    assert (summaries['volume']['areas_full'], summaries['volume']['areas_total'],
            summaries['volume']['areas_missing']) == (4, 10, 4)
    bench.write_summary(rows, [cfg], tasks, tmp, planned_trials=4)
    text = (tmp / 'summary.md').read_text()
    assert '| difficulty | a, b | 0.5833 | 0.5000 | 4/8 | 1 | 3 | 1 | 1 | 1 |' in text
    assert '| volume | v1, v2 | 0.6250 | 0.0000 | 2/8 |' in text
    assert '| 4/10 | 4 |' in text
    overall = next(line for line in text.splitlines() if '| overall |' in line)
    assert '| 0.6042 |' in overall  # Multi-axis fixture a is counted once.


def test_axis_all_infra_and_absent_fixture(fixture):
    _, cfg, tmp = fixture
    row = dict(config=cfg['spec'], task='toy', axes=['volume'], eligible_score=None,
               success=False, valid=True, status='timeout', grading_infra_failure=True,
               duration_s=None, total_input=None, output=None, requests=None,
               areas={'a': {'score': None}})
    axis = bench.axis_summaries([row], ['toy'], planned_trials=2)[0]
    assert axis['axis'] == 'volume'  # Saved axes override manifest's difficulty/complexity.
    assert axis['score'] is None and axis['full_pass'] is None
    assert axis['tokens'] is None and axis['wall'] is None
    assert (axis['scored'], axis['planned'], axis['areas_missing']) == (0, 2, 1)
    absent = bench.axis_summaries([], ['toy'], planned_trials=2)
    assert {r['axis'] for r in absent} == {'difficulty', 'complexity'}
    assert all(r['score'] is None and r['full_pass'] is None and r['trial_missing'] == 2 for r in absent)


@pytest.mark.parametrize('suite, explicit, chosen', [
    (None, None, ['cap']), ('efficiency', None, ['smoke']),
    ('archived', None, ['old']), ('efficiency', 'cap,old', ['cap', 'old'])])
def test_suite_selection(monkeypatch, tmp_path, suite, explicit, chosen):
    monkeypatch.setattr(bench, 'load_tasks', lambda: {
        'cap': {'suite': 'capability'}, 'smoke': {'suite': 'efficiency'}, 'old': {'suite': 'archived'}})
    seen = []
    def grade(task, out):
        seen.append(task)
        return {'areas': {'a': {'total': 1}}}
    monkeypatch.setattr(bench, 'grade_ref', grade)
    monkeypatch.setattr(bench, 'write_summary', lambda *args, **kwargs: None)
    args = ['bench', '--config', 'pi:fake:high', '--repeat', '0', '--out', str(tmp_path)]
    if suite:
        args += ['--suite', suite]
    if explicit:
        args += ['--tasks', explicit]
    monkeypatch.setattr(sys, 'argv', args)
    bench.main()
    assert seen == chosen


def test_grading_workspace_failure_preserves_known_area_denominator(fixture, monkeypatch):
    _, cfg, tmp = fixture
    denom = expected(fixture)
    def unavailable(*args):
        raise OSError('grading workspace unavailable')
    monkeypatch.setattr(bench, 'prepare_grading_workspace', unavailable)
    result = bench.run_trial(cfg, 0, 'toy', 1, tmp, 2, denom)
    assert result['grading_infra_failure']
    assert result['eligible_score'] is None
    assert result['areas'] == {'alpha': {'total': 2, 'score': None},
                               'beta': {'total': 2, 'score': None}}
    result['axes'] = ['volume']
    axis = bench.axis_summaries([result], ['toy'], planned_trials=1)[0]
    assert (axis['areas_full'], axis['areas_total'], axis['areas_missing']) == (0, 2, 2)
    assert axis['score'] is None and axis['full_pass'] is None
