import json
import subprocess
import sys
from pathlib import Path

import pytest

from test_bench import bench, fixture  # noqa: F401

RUNNER = Path(__file__).resolve().parents[2] / 'scripts/harness-run.py'


def test_context_requires_minimal():
    with pytest.raises(SystemExit):
        bench.parse_config('pi:openai-codex/m:low:context')
    cfg = bench.parse_config('pi:openai-codex/m:low:minimal,context')
    assert cfg['flags'] == ['minimal', 'context']


def test_brief_validation_and_task_substitution(tmp_path):
    brief = tmp_path / 'b.md'
    brief.write_text('rules')
    cfg = bench.parse_config(f'pi:openai-codex/m:low:minimal,brief={brief}')
    assert bench.brief_path(cfg, 'toy') == brief
    with pytest.raises(SystemExit):
        bench.parse_config(f'pi:openai-codex/m:low:minimal,brief={tmp_path}/missing.md')
    with pytest.raises(SystemExit):
        bench.parse_config('pi:openai-codex/m:low:minimal,brief=rel.md')
    per_task = bench.parse_config(f'pi:openai-codex/m:low:minimal,brief={tmp_path}/{{task}}.md')
    assert bench.brief_path(per_task, 'toy') == tmp_path / 'toy.md'
    assert bench.brief_path(bench.parse_config('pi:openai-codex/m:low:minimal'), 'toy') is None


def test_compose_prompt(tmp_path):
    (tmp_path / 'b.md').write_text('rules')
    (tmp_path / 't.md').write_text('task')
    assert bench.compose_prompt(tmp_path / 'b.md', tmp_path / 't.md') == 'rules\n\ntask'


def test_trial_prompt_and_missing_brief(fixture, monkeypatch):
    _, _, tmp = fixture
    brief = tmp / 'briefs'
    brief.mkdir()
    (brief / 'toy.md').write_text('rules')
    seen = {}

    def fake_invoke(cfg, prompt_file, ws, work_dir, run_id, timeout):
        seen['prompt'] = Path(prompt_file).read_text()
        return {'status': 'completed', 'duration_s': 0.1}, None
    monkeypatch.setattr(bench, 'invoke', fake_invoke)
    cfg = bench.parse_config(f'pi:openai-codex/m:low:minimal,brief={brief}/{{task}}.md')
    denom = {'alpha': 2, 'beta': 2}
    bench.run_trial(cfg, 0, 'toy', 1, tmp, 1, denom)
    assert seen['prompt'] == 'rules\n\nFix pkg only'
    (brief / 'toy.md').unlink()
    seen.clear()
    r = bench.run_trial(cfg, 0, 'toy', 2, tmp, 1, denom)
    assert not seen and r['status'] == 'invocation_error' and 'brief' in r['error']


def test_flags_make_separate_matrix_rows():
    recs = [dict(config=c, task='toy', axes=['difficulty'], status='completed', success=True, valid=True,
                 eligible_score=1.0, raw_score=1.0, trial=1, grading_infra_failure=False, areas={})
            for c in ('pi:m:low:minimal', 'pi:m:low:minimal,context', 'pi:m:low:minimal,brief=/x/{task}.md')]
    assert len({bench.parse_config(r['config'], check_files=False)['spec'] for r in recs}) == 3


def dry(harness, *extra):
    out = subprocess.run([sys.executable, str(RUNNER), '--harness', harness, '--model', 'openai-codex/m',
                          '--effort', 'low', '--prompt', 'hi', '--cwd', '/tmp', '--work-dir', '/tmp',
                          '--run-id', 'ctx-test', '--dry-run', *extra], capture_output=True, text=True)
    return json.loads(out.stdout.splitlines()[-1])


@pytest.mark.parametrize('harness, dropped', [('pi', '-nc'), ('omp', '--no-context-files')])
def test_runner_keep_context_files(harness, dropped):
    assert dropped in dry(harness, '--minimal-context')['argv']
    kept = dry(harness, '--minimal-context', '--keep-context-files')['argv']
    assert dropped not in kept and ('--no-skills' in kept or '-ns' in kept)


@pytest.mark.parametrize('harness, extra', [('pi', []), ('dsh', ['--minimal-context']),
                                            ('opencode', ['--minimal-context'])])
def test_runner_keep_context_files_rejected(harness, extra):
    r = dry(harness, '--keep-context-files', *extra)
    assert r['status'] == 'invocation_error'
