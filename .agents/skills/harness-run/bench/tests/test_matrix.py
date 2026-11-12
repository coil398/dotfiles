import json
import sys

import pytest

from test_bench import bench


def result(config, task='a', score=1, axes=('difficulty', 'complexity'),
           applied=None, tokens=410000, wall=95, status='completed'):
    return dict(config=config, task=task, axes=list(axes), eligible_score=score,
                success=score == 1 and status == 'completed', valid=True, status=status,
                grading_infra_failure=score is None, duration_s=wall,
                total_input=tokens, output=0, requests=1, effort_applied=applied,
                areas={'one': {'score': score}})


@pytest.fixture
def matrix_records():
    return [result('dsh:demo:low'),
            result('dsh:demo:low', task='b', score=0, axes=('difficulty', 'volume'),
                   tokens=100000, wall=10),
            result('dsh:demo:low', task='b', score=.5, axes=('difficulty', 'volume'),
                   status='timeout'),
            result('dsh:demo:low', task='b', score=None, axes=('difficulty', 'volume'),
                   tokens=None, wall=None),
            result('dsh:demo:high', applied='max'),
            result('dsh:demo:max', applied='max'),
            result('pi:demo:medium:minimal', score=.75)]


def cell(matrix, name, model, effort, kind='axes'):
    table = next(t for t in matrix[kind] if t['name'] == name)
    return next(row for row in table['rows'] if row['model'] == model)['cells'][effort]


def test_matrix_weighting_mapping_missing_and_medians(matrix_records):
    matrix = bench.build_matrix(matrix_records)
    assert matrix['efforts'] == ['low', 'medium', 'max']
    d = cell(matrix, 'difficulty', 'dsh:demo', 'low')
    assert d['score'] == .625  # (1 + mean(0, .5)) / 2, excluding null.
    assert d['full_pass'] == .5  # Equal fixture weights, rather than 1/3 trials.
    assert (d['trials'], d['scored'], d['score_missing']) == (4, 3, 1)
    assert (d['total_tokens'], d['wall_s']) == (410000, 95)
    assert (d['tokens_missing'], d['wall_missing']) == (1, 1)
    assert cell(matrix, 'overall', 'dsh:demo', 'low') == d  # Multi-axis a counted once.
    assert cell(matrix, 'complexity', 'dsh:demo', 'low')['score'] == 1
    assert cell(matrix, 'volume', 'dsh:demo', 'low')['score'] == .25
    assert cell(matrix, 'overall', 'dsh:demo', 'medium') is None
    assert cell(matrix, 'overall', 'pi:demo:minimal', 'low') is None
    mapped = cell(matrix, 'overall', 'dsh:demo', 'max')
    assert mapped['trials'] == 2
    assert mapped['effort_mappings'] == ['high→max']
    assert cell(matrix, 'b', 'dsh:demo', 'low', 'fixtures')['score'] == .25
    assert cell(matrix, 'b', 'dsh:demo', 'max', 'fixtures') is None


def test_summary_matrix_render_and_json(matrix_records, tmp_path, monkeypatch):
    monkeypatch.setattr(bench, 'load_tasks', lambda: pytest.fail('report read live fixtures'))
    configs = [bench.parse_config(s) for s in sorted({r['config'] for r in matrix_records})]
    bench.write_summary(matrix_records, configs, ['a', 'b'], tmp_path)
    matrix = json.loads((tmp_path / 'matrix.json').read_text())
    assert matrix == bench.build_matrix(matrix_records)
    text = (tmp_path / 'summary.md').read_text().split('## マトリックス')[1]
    assert '| harness:model[:flags] | low | medium | max |' in text
    assert '| dsh:demo | 0.62 (50%) · 410k tok · 95s |  | 1.00 (100%) · 410k tok · 95s [high→max] |' in text
    assert '### fixture: b' in text
    assert '| dsh:demo | 0.25 |  |  |' in text


def test_effort_order_flags_and_all_missing():
    rows = [result(f'pi:demo:{effort}', applied=effort)
            for effort in ('max', 'high', 'low', 'xhigh', 'medium')]
    rows.append(result('pi:demo:low:minimal', score=None, tokens=None, wall=None))
    matrix = bench.build_matrix(rows)
    assert matrix['efforts'] == ['low', 'medium', 'high', 'xhigh', 'max']
    missing = cell(matrix, 'overall', 'pi:demo:minimal', 'low')
    assert missing['score'] is None and missing['full_pass'] is None
    assert missing['total_tokens'] is None and missing['wall_s'] is None
    assert missing['scored'] == 0 and missing['trials'] == 1
    assert '| pi:demo:minimal | - (-) · - tok · -s |' in '\n'.join(bench.render_matrix(matrix))


def test_report_only_merges_without_execution(matrix_records, tmp_path, monkeypatch, capsys):
    sources = [tmp_path / 'first', tmp_path / 'second']
    contents = []
    for directory, rows in zip(sources, (matrix_records[:4], matrix_records[4:])):
        directory.mkdir()
        content = ''.join(json.dumps(r) + '\n' for r in rows)
        (directory / 'results.jsonl').write_text(content)
        contents.append(content)
    def forbidden(*args, **kwargs):
        pytest.fail('report-only executed a benchmark or loaded fixtures')
    monkeypatch.setattr(bench, 'load_tasks', lambda: {})
    for name in ('grade_ref', 'invoke', 'run_trial'):
        monkeypatch.setattr(bench, name, forbidden)
    out = tmp_path / 'combined'
    monkeypatch.setattr(sys, 'argv', ['bench', '--report-only', *(str(p) for p in sources),
                                    str(sources[0] / '.'), '--out', str(out)])
    bench.main()
    assert str(out / 'summary.md') in capsys.readouterr().out
    assert json.loads((out / 'matrix.json').read_text()) == bench.build_matrix(matrix_records)
    assert not (out / 'results.jsonl').exists()
    assert [p.joinpath('results.jsonl').read_text() for p in sources] == contents


def test_report_only_fills_missing_axes_at_load_time(tmp_path, monkeypatch, caplog):
    source = tmp_path / 'source'
    source.mkdir()
    known = result('pi:demo:low', task='known')
    known.pop('axes')
    unknown = result('pi:demo:low', task='removed-task')
    unknown.pop('axes')
    (source / 'results.jsonl').write_text(json.dumps(known) + '\n' + json.dumps(unknown) + '\n')
    monkeypatch.setattr(bench, 'load_tasks', lambda: {'known': {'axes': ['volume']}})

    out = tmp_path / 'out'
    out.mkdir()
    bench.report_only([source], out)

    matrix = json.loads((tmp_path / 'out' / 'matrix.json').read_text())
    assert matrix['axes'][2]['rows'][0]['cells']['low']['trials'] == 1
    assert 'report_missing_axes_unknown_task task=removed-task' in caplog.text


def test_merge_repeated_config_trials_does_not_collapse_trial_numbers(tmp_path):
    dirs = [tmp_path / 'one', tmp_path / 'two']
    rows = [result('pi:demo:high', score=s) for s in (1, 0)]
    for directory, row in zip(dirs, rows):
        directory.mkdir()
        row['trial'] = 1
        (directory / 'results.jsonl').write_text(json.dumps(row) + '\n')
    bench.report_only(dirs, tmp_path)
    matrix = json.loads((tmp_path / 'matrix.json').read_text())
    value = cell(matrix, 'overall', 'pi:demo', 'high')
    assert value['trials'] == 2 and value['score'] == .5 and value['full_pass'] == .5


def test_empty_report(tmp_path, monkeypatch):
    (tmp_path / 'results.jsonl').write_text('')
    monkeypatch.setattr(bench, 'load_tasks', lambda: pytest.fail('loaded fixtures'))
    bench.report_only([tmp_path], tmp_path)
    matrix = json.loads((tmp_path / 'matrix.json').read_text())
    assert matrix['efforts'] == [] and matrix['fixtures'] == []
    assert all(table['rows'] == [] for table in matrix['axes'])
