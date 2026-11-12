#!/usr/bin/env python3
"""Implementation benchmark with private, reference-calibrated grading."""
import argparse
import json
import logging
import os
import random
import re
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
SKILLS = HERE.parent.parent
RUNNER = SKILLS / "harness-run/scripts/harness-run.py"
CODEX_RUNNER = SKILLS / "codex/scripts/codex-run.py"
TEST_CMD = ["uv", "run", "--offline", "-q", "--no-project", "--with", "pytest"]
HARNESSES = ("codex", "pi", "omp", "opencode", "dsh")
SKIP_STATUSES = ("auth_not_ready", "runner_missing")
logger = logging.getLogger("bench")


def load_tasks():
    return {p.parent.name: json.loads(p.read_text()) for p in sorted(FIXTURES.glob("*/fixture.json"))}


def slug(text):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-")


def parse_config(spec):
    parts = spec.split(":")
    if len(parts) < 3 or len(parts) > 4 or parts[0] not in HARNESSES:
        raise SystemExit(f"invalid --config {spec!r}: harness:model:effort[:flags], harness in {HARNESSES}")
    flags = [f for f in (parts[3].split(",") if len(parts) == 4 else []) if f]
    for flag in flags:
        if flag != "minimal" and not flag.startswith("dsh-patch="):
            raise SystemExit(f"unknown flag {flag!r} in {spec!r}")
    return {"spec": spec, "harness": parts[0], "model": parts[1], "effort": parts[2], "flags": flags}


def run_group(cmd, cwd, timeout, grace=45):
    """timeout時にprocess group全体を止める。

    runnerは子harnessを別のprocess groupで起動するため、SIGKILLでは子が残る。
    先にSIGTERMを送り、runnerに子のgroupを止めさせてから、残りをSIGKILLする。
    """
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            start_new_session=True)
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except BaseException:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            proc.communicate(timeout=grace)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.communicate()
        raise
    return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)


def stop_codex(work_dir, run_id):
    """codex-run が detach した supervisor と helper を止める(codex-run に timeout 引数が無いため)。"""
    pids = []
    prefix = work_dir / f"codex-{run_id}-"
    for name, pattern in (("run.log", r"worker_pid=(\d+)"), ("pid", r"(\d+)")):
        try:
            pids += [int(x) for x in re.findall(pattern, Path(f"{prefix}{name}").read_text(errors="replace"))]
        except OSError:
            pass
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid in set(pids):
            for kill in (os.killpg, os.kill):
                try:
                    kill(pid, sig)
                    break
                except (ProcessLookupError, PermissionError):
                    continue
        time.sleep(3)


def git(ws, *args):
    return subprocess.run(["git", "-c", "user.name=bench", "-c", "user.email=bench@localhost", *args],
                          cwd=ws, capture_output=True, text=True, check=True).stdout


def prepare_workspace(task, ws):
    shutil.copytree(FIXTURES / task / "workspace", ws,
                    ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".git"))
    git(ws, "init", "-q")
    files = [str(p.relative_to(ws)) for p in ws.rglob("*")
             if p.is_file() and ".git" not in p.relative_to(ws).parts]
    if files:
        git(ws, "add", "--", *files)
    git(ws, "commit", "-q", "--allow-empty", "-m", "baseline")
    return git(ws, "rev-parse", "HEAD").strip()


def matches(path, entry):
    return path.startswith(entry) if entry.endswith("/") else path == entry


def check_diff(task, ws, base):
    spec = load_tasks()[task]
    changed = set(git(ws, "diff", "--name-only", "--no-renames", "-z", base).split("\0"))
    # Include ignored additions as well; ignore only interpreter/pytest caches.
    changed.update(git(ws, "ls-files", "--others", "-z").split("\0"))
    changed = sorted(p for p in changed if p and not any(
        part in ("__pycache__", ".pytest_cache") for part in Path(p).parts))
    tampered = [p for p in changed if any(matches(p, x) for x in spec["public_tests"])]
    outside = [p for p in changed if p not in tampered and not any(matches(p, x) for x in spec["allowed"])]
    return changed, tampered, outside


def normalize_codex(summary, wall):
    usage = summary.get("usage") or {}

    def num(key):
        value = usage.get(key)
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    total = num("input_tokens")
    cached = num("cached_input_tokens")
    requests = None
    events_path = (summary.get("events") or {}).get("path")
    if events_path and Path(events_path).exists():
        count = 0
        for line in Path(events_path).read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                if json.loads(line).get("method") == "thread/tokenUsage/updated":
                    count += 1
            except json.JSONDecodeError:
                continue
        requests = count or None
    if requests is None:
        calls = (summary.get("run") or {}).get("model_call_count")
        requests = calls if isinstance(calls, int) else None
    done = summary.get("done") or {}
    status = "completed" if summary.get("wait_status") == "completed" and done.get("exit") == 0 else None
    if status is None:
        status = {"invocation_error": "invocation_error", "timeout": "timeout", "timed_out": "timeout"}.get(summary.get("wait_status"), "failed")
    return {
        "status": status,
        "error": summary.get("error"),
        "requests": requests,
        "total_input": total,
        "cache_read": cached,
        "cache_write": None,
        "input_uncached": total - cached if total is not None and cached is not None else None,
        "output": num("output_tokens"),
        "reasoning": None,
        "duration_s": wall,
        "effort_applied": summary.get("effort_applied"),
    }


def normalize_runner(summary, wall):
    usage = summary.get("usage") or {}

    def num(key):
        value = usage.get(key)
        return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None

    total = num("total_input")
    uncached, cache_read, cache_write = num("input_uncached"), num("cache_read"), num("cache_write")
    if total is None and uncached is not None:
        total = uncached + (cache_read or 0) + (cache_write or 0)
    return {
        "status": summary.get("status", "failed"),
        "error": summary.get("error"),
        "requests": num("requests"),
        "total_input": total,
        "cache_read": cache_read,
        "cache_write": cache_write,
        "input_uncached": uncached,
        "output": num("output"),
        "reasoning": num("reasoning"),
        "duration_s": wall,
        "effort_applied": summary.get("effort_applied"),
    }


def last_json(stdout):
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None


def invoke(cfg, prompt_file, ws, work_dir, run_id, timeout):
    work_dir.mkdir(parents=True, exist_ok=True)
    override = os.environ.get("BENCH_RUNNER_OVERRIDE")
    if override:
        start = time.monotonic()
        try:
            proc = run_group([sys.executable, override, str(prompt_file), str(ws)], ws, timeout)
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "duration_s": time.monotonic() - start}, None
        summary = last_json(proc.stdout)
        return normalize_runner(summary or {"status": "failed"}, time.monotonic() - start), summary
    if cfg["harness"] == "codex":
        runner = CODEX_RUNNER
        cmd = [sys.executable, str(runner), "--prompt-file", str(prompt_file), "--cwd", str(ws),
               "--model", cfg["model"], "--effort", cfg["effort"], "--work-dir", str(work_dir), "--run-id", run_id]
    else:
        runner = RUNNER
        cmd = [sys.executable, str(runner), "--harness", cfg["harness"], "--model", cfg["model"],
               "--effort", cfg["effort"], "--prompt-file", str(prompt_file), "--cwd", str(ws),
               "--work-dir", str(work_dir), "--run-id", run_id, "--timeout", str(timeout)]
        for flag in cfg["flags"]:
            if flag == "minimal":
                cmd.append("--minimal-context")
            elif flag.startswith("dsh-patch="):
                cmd += ["--dsh-patch", str(Path(flag.split("=", 1)[1]).resolve())]
    if not runner.exists():
        return {"status": "runner_missing", "error": f"{runner} not found"}, None
    start = time.monotonic()
    try:
        proc = run_group(cmd, ws, timeout + 180)
    except subprocess.TimeoutExpired:
        if cfg["harness"] == "codex":
            stop_codex(work_dir, run_id)
        return {"status": "timeout", "error": "bench outer timeout", "duration_s": time.monotonic() - start}, None
    wall = time.monotonic() - start
    summary = last_json(proc.stdout)
    if summary is None:
        return {"status": "failed", "error": f"no summary JSON (exit {proc.returncode}): {proc.stderr[-300:]}",
                "duration_s": wall}, None
    norm = normalize_codex(summary, wall) if cfg["harness"] == "codex" else normalize_runner(summary, wall)
    return norm, summary


def counts(cases, total=None):
    failed = sum(c.find('failure') is not None for c in cases)
    errors = sum(c.find('error') is not None for c in cases)
    skipped = sum(c.find('skipped') is not None for c in cases)
    passed = sum(all(c.find(tag) is None for tag in ('failure', 'error', 'skipped')) for c in cases)
    total = len(cases) if total is None else total
    return dict(passed=min(passed, total), total=total, failed=failed, errors=errors, skipped=skipped)


def run_tests(ws, tdir, task, expected=None):
    """expected is the reference's {area: case count}; collection errors score zero."""
    tdir.mkdir(parents=True, exist_ok=True)
    spec = load_tasks()[task]
    result = {'areas': {}, 'infra_errors': []}
    cmd = TEST_CMD + [arg for pkg in spec.get('uv_with', []) for arg in ('--with', pkg)]
    cmd += ['python', '-m', 'pytest', '-q']
    for kind, targets in [('public', spec['public_tests']), ('hidden', ['tests_hidden'])]:
        xml = (tdir / f'{kind}.xml').resolve()
        xml.unlink(missing_ok=True)
        try:
            proc = subprocess.run(cmd + targets + [f'--junitxml={xml}'], cwd=ws,
                                  capture_output=True, text=True, timeout=spec.get('grading_timeout_s', 300))
            stdout, stderr = proc.stdout, proc.stderr
        except (OSError, subprocess.TimeoutExpired) as exc:
            proc = None
            stdout, stderr = '', str(exc)
            result['infra_errors'].append(f'{kind}: {exc}')
        (tdir / f'{kind}.stdout').write_text(stdout)
        (tdir / f'{kind}.stderr').write_text(stderr)
        cases = []
        if proc is not None:
            try:
                cases = list(ET.parse(xml).getroot().iter('testcase'))
            except (OSError, ET.ParseError) as exc:
                result['infra_errors'].append(f'{kind}: invalid JUnit: {exc}')
            if proc.returncode not in (0, 1, 2, 5):
                result['infra_errors'].append(f'{kind}: pytest exit {proc.returncode}')
        if kind == 'public':
            result[kind] = counts(cases)
        else:
            grouped = {f.stem[5:]: [] for f in (FIXTURES / task / 'private/tests').glob('test_*.py')}
            for case in cases:
                identity = case.get('classname', '') + '/' + case.get('name', '')
                for area in grouped:
                    if re.search(r'(?:^|[./])test_' + re.escape(area) + r'(?:[./]|$)', identity):
                        grouped[area].append(case)
                        break
            result['areas'] = {area: counts(cs, expected[area] if expected is not None else None)
                               for area, cs in grouped.items()}
            for area, cs in grouped.items():
                result['areas'][area]['perf_timeout'] = sum(
                    any('TimeoutExpired' in failure.get('message', '') or
                        'timed out' in failure.get('message', '')
                        for failure in case.findall('failure')) for case in cs)
            result[kind] = {k: sum(v[k] for v in result['areas'].values())
                            for k in ('passed', 'total', 'failed', 'errors', 'skipped')}
    logger.info('graded task=%s path=%s public=%s hidden=%s infra_errors=%d',
                task, tdir, result['public'], result['hidden'], len(result['infra_errors']))
    return result


def prepare_grading_workspace(task, source, changed, dest):
    shutil.copytree(FIXTURES / task / 'workspace', dest,
                    ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache', '.git'))
    spec = load_tasks()[task]
    for rel in changed:
        if (any(matches(rel, x) for x in spec['allowed'])
                and not any(matches(rel, x) for x in spec['public_tests'])):
            src, dst = source / rel, dest / rel
            if src.is_file():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            elif dst.exists():
                shutil.rmtree(dst) if dst.is_dir() else dst.unlink()
    shutil.copytree(FIXTURES / task / 'private/tests', dest / 'tests_hidden')
    return dest


def grade_ref(task, tdir):
    tdir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='bench-reference-') as tmp:
        ws = Path(tmp) / 'ws'
        shutil.copytree(FIXTURES / task / 'workspace', ws)
        shutil.copytree(FIXTURES / task / 'private/reference', ws, dirs_exist_ok=True)
        shutil.copytree(FIXTURES / task / 'private/tests', ws / 'tests_hidden')
        result = run_tests(ws, tdir, task)
    if (result['infra_errors'] or not result['hidden']['total'] or
            any(v['passed'] != v['total'] or v['errors'] for v in [result['public'], result['hidden']])
            or any(v['total'] == 0 for v in result['areas'].values())):
        raise RuntimeError(f'reference grading failed: {task}; result={result}; logs={tdir}')
    return result


def run_trial(cfg, idx, task, n, out, timeout, expected, budget_s=None):
    axes = load_tasks()[task]['axes']
    tdir = out / 'trials' / f'{task}-c{idx}-{n}'
    tdir.mkdir(parents=True)
    ws = tdir / 'ws'
    base = prepare_workspace(task, ws)
    prompt = tdir / 'task.md'
    shutil.copyfile(FIXTURES / task / 'task.md', prompt)
    logger.info('trial_start id=%s config=%s timeout_s=%s budget_s=%s', tdir.name, cfg['spec'], timeout, budget_s)
    norm, usage_summary = invoke(cfg, prompt, ws, tdir / 'work', slug(tdir.name), timeout)
    # This must precede any private test entering the agent or grading workspace.
    changed, tampered, outside = check_diff(task, ws, base)
    invalid = bool(tampered or outside)
    start = time.monotonic()
    try:
        grading = prepare_grading_workspace(task, ws, changed, tdir / 'grading')
        tests = run_tests(grading, tdir, task, expected)
    except (OSError, shutil.Error) as exc:
        logger.exception('grading_failed id=%s', tdir.name)
        tests = {'areas': {}, 'infra_errors': [str(exc)]}
    infra = bool(tests['infra_errors'])
    raw = None if infra else tests['hidden']['passed'] / sum(expected.values())
    eligible = None if infra else (0 if invalid else raw)
    public = tests.get('public', {})
    public_ok = bool(public) and public['passed'] == public['total'] and public['errors'] == 0
    areas = {}
    for area, total in expected.items():
        values = tests['areas'].get(area, {'total': total})
        areas[area] = {**values, 'score': None if infra else values['passed'] / total}
    result = dict(config=cfg['spec'], task=task, axes=axes, trial=n, trial_dir=str(tdir), **norm,
                  budget_s=budget_s,
                  within_budget=None if budget_s is None else bool(
                      norm['status'] == 'completed' and eligible == 1.0 and
                      norm.get('duration_s') is not None and norm['duration_s'] <= budget_s),
                  changed=changed, tampered=tampered, outside=outside, valid=not invalid,
                  raw_score=raw, eligible_score=eligible, areas=areas, tests=tests,
                  usage=(usage_summary or {}).get('usage'), grading_infra_failure=infra,
                  grading_duration_s=time.monotonic() - start,
                  success=bool(norm['status'] == 'completed' and public_ok and raw == 1 and not invalid),
                  skipped=norm['status'] in SKIP_STATUSES)
    (tdir / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    logger.info('trial_done id=%s status=%s valid=%s raw_score=%s eligible_score=%s agent_s=%s grading_s=%.3f within_budget=%s',
                tdir.name, norm['status'], not invalid, raw, eligible, norm.get('duration_s'), result['grading_duration_s'], result['within_budget'])
    return result


def median(values):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None


def mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def total_tokens(r):
    return r['total_input'] + r['output'] if r.get('total_input') is not None and r.get('output') is not None else None


def summary_row(config, task, rs, score):
    tokens = [total_tokens(r) for r in rs]
    missing = sum(t is None for t in tokens)
    # An incomplete denominator cannot produce a measured efficiency.
    efficiency = (sum(r['eligible_score'] for r in rs) / sum(tokens) * 100000
                  if rs and not missing and sum(tokens) > 0 and
                  all(r.get('eligible_score') is not None for r in rs) else None)
    vals = [config, task, score, f"{sum(r['success'] for r in rs)}/{len(rs)}",
            (f"{sum(r.get('within_budget') is True for r in rs)}/{len(rs)}"
             if rs and all(r.get('within_budget') is not None for r in rs) else None),
            sum(not r['valid'] for r in rs), sum(r['status'] == 'timeout' for r in rs),
            sum(r['grading_infra_failure'] for r in rs), median([r.get('duration_s') for r in rs]),
            median([r.get('requests') for r in rs]), sum(r.get('requests') is None for r in rs),
            median(tokens), missing, efficiency]
    return '| ' + ' | '.join('-' if v is None else f'{v:.4f}' if isinstance(v, float) else str(v) for v in vals) + ' |'


def axis_summaries(records, tasks, planned_trials=None, saved_axes=None):
    manifests = load_tasks() if saved_axes is None else {}
    by_task = {task: [r for r in records if r['task'] == task] for task in tasks}
    # Saved classifications take precedence over manifests when summarizing results.
    axes = {task: {axis for r in rs for axis in r['axes']} if rs else
            set(saved_axes.get(task, []) if saved_axes is not None else
                manifests.get(task, {}).get('axes', [])) for task, rs in by_task.items()}
    rows = []
    for axis in sorted({a for values in axes.values() for a in values}):
        members = [task for task in tasks if axis in axes[task]]
        groups = [by_task[task] for task in members]
        rs = [r for group in groups for r in group]
        scored = sum(r['eligible_score'] is not None for r in rs)
        planned = sum(planned_trials if planned_trials is not None else len(group) for group in groups)
        tokens = [total_tokens(r) for r in rs]
        areas = [area.get('score') for r in rs for area in r['areas'].values()]
        rows.append(dict(
            axis=axis, fixtures=members,
            score=mean([mean([r['eligible_score'] for r in group]) for group in groups]),
            full_pass=mean([mean([int(r['success']) for r in group
                                 if r['eligible_score'] is not None]) for group in groups]),
            scored=scored, planned=planned, score_missing=len(rs) - scored,
            trial_missing=max(0, planned - len(rs)),
            invalid=sum(not r['valid'] for r in rs),
            timeout=sum(r['status'] == 'timeout' for r in rs),
            infra=sum(r['grading_infra_failure'] for r in rs),
            wall=median([r.get('duration_s') for r in rs]),
            wall_missing=sum(r.get('duration_s') is None for r in rs),
            tokens=median(tokens), tokens_missing=sum(t is None for t in tokens),
            areas_full=sum(score == 1 for score in areas) if axis == 'volume' else None,
            areas_total=len(areas) if axis == 'volume' else None,
            areas_missing=sum(score is None for score in areas) if axis == 'volume' else None))
    return rows


def build_matrix(records):
    grouped = {}
    for r in records:
        cfg = parse_config(r['config'])
        model = ':'.join([cfg['harness'], cfg['model']] +
                         ([','.join(sorted(cfg['flags']))] if cfg['flags'] else []))
        effort = r.get('effort_applied') or cfg['effort']
        grouped.setdefault((model, effort), []).append((r, cfg['effort']))
    present = {effort for _, effort in grouped}
    order = ['low', 'medium', 'high', 'xhigh', 'max']
    efforts = [e for e in order if e in present] + sorted(present - set(order))
    models = sorted({model for model, _ in grouped})
    tasks = sorted({r['task'] for r in records})

    def table(kind, name):
        rows = []
        for model in models:
            cells = {}
            for effort in efforts:
                pairs = [(r, requested) for r, requested in grouped.get((model, effort), [])
                         if (kind == 'axis' and name == 'overall') or
                         (kind == 'axis' and name in r['axes']) or
                         (kind == 'fixture' and name == r['task'])]
                if not pairs:
                    cells[effort] = None
                    continue
                rs = [r for r, _ in pairs]
                groups = [[r for r in rs if r['task'] == task]
                          for task in sorted({r['task'] for r in rs})]
                cells[effort] = dict(
                    score=mean([mean([r['eligible_score'] for r in group]) for group in groups]),
                    full_pass=mean([mean([int(r['success']) for r in group
                                         if r['eligible_score'] is not None]) for group in groups]),
                    trials=len(rs), scored=sum(r['eligible_score'] is not None for r in rs),
                    score_missing=sum(r['eligible_score'] is None for r in rs),
                    total_tokens=median([total_tokens(r) for r in rs]),
                    tokens_missing=sum(total_tokens(r) is None for r in rs),
                    wall_s=median([r.get('duration_s') for r in rs]),
                    wall_missing=sum(r.get('duration_s') is None for r in rs),
                    effort_mappings=sorted({f'{requested}→{effort}' for _, requested in pairs
                                            if requested != effort}))
            rows.append(dict(model=model, cells=cells))
        return dict(name=name, rows=rows)

    return dict(efforts=efforts,
                axes=[table('axis', axis) for axis in ('difficulty', 'complexity', 'volume', 'overall')],
                fixtures=[table('fixture', task) for task in tasks])


def render_matrix(matrix):
    lines = ['', '## マトリックス', '',
             '列は適用effort。得点・full-pass率はfixture平均、tokens・wallはtrial中央値です。',
             '未実行は空欄、計測欠測は `-`、effort変換は `要求→適用` で示します。']
    for kind in ('axes', 'fixtures'):
        for table in matrix[kind]:
            lines += ['', f"### {'fixture: ' if kind == 'fixtures' else ''}{table['name']}", '',
                      '| ' + ' | '.join(['harness:model[:flags]', *matrix['efforts']]) + ' |',
                      '|---|' + '---:|' * len(matrix['efforts'])]
            for row in table['rows']:
                values = []
                for cell in row['cells'].values():
                    if cell is None:
                        values.append('')
                        continue
                    value = '-' if cell['score'] is None else f"{cell['score']:.2f}"
                    if kind == 'axes':
                        rate = '-' if cell['full_pass'] is None else f"{cell['full_pass']:.0%}"
                        tokens = cell['total_tokens']
                        tok = '-' if tokens is None else (f'{tokens / 1000:.0f}k' if tokens >= 1000 else f'{tokens:g}')
                        wall = '-' if cell['wall_s'] is None else f"{cell['wall_s']:.0f}"
                        value += f' ({rate}) · {tok} tok · {wall}s'
                    if cell['effort_mappings']:
                        value += ' [' + ', '.join(cell['effort_mappings']) + ']'
                    values.append(value)
                label = row['model'].replace('|', '\\|')
                lines.append('| ' + label + ' | ' + ' | '.join(values) + ' |')
    return lines


def write_summary(records, configs, tasks, out, planned_trials=None):
    lines = ['# bench summary', '',
             '| 構成 | 課題 | 平均eligible | full-pass率 | 予算内完遂 | invalid | timeout | grading infra | wall中央値(s) | requests中央値 | requests欠測 | total_tokens中央値 | tokens欠測 | 効率 |',
             '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    saved_axes = {task: {axis for r in records if r['task'] == task for axis in r['axes']}
                  for task in tasks}
    for cfg in configs:
        selected = [r for r in records if r['config'] == cfg['spec']]
        means = []
        for task in tasks:
            rs = [r for r in selected if r['task'] == task]
            score = mean([r['eligible_score'] for r in rs])
            means.append(score)
            lines.append(summary_row(cfg['spec'], task, rs, score))
        lines.append(summary_row(cfg['spec'], 'overall', selected, mean(means)))
    lines += ['', '## 軸別集計', '',
              '| 構成 | 軸 | fixture一覧 | 平均eligible | full-pass率 | 採点済み/予定trial | 得点欠測 | 未取得trial | invalid | timeout | grading infra | wall中央値(s) | wall欠測 | total_tokens中央値 | tokens欠測 | 満点area/全area | area欠測 |',
              '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for cfg in configs:
        selected = [r for r in records if r['config'] == cfg['spec']]
        for row in axis_summaries(selected, tasks, planned_trials, saved_axes):
            vals = [cfg['spec'], row['axis'], ', '.join(row['fixtures']), row['score'], row['full_pass'],
                    f"{row['scored']}/{row['planned']}", row['score_missing'], row['trial_missing'],
                    row['invalid'], row['timeout'], row['infra'], row['wall'], row['wall_missing'],
                    row['tokens'], row['tokens_missing'],
                    f"{row['areas_full']}/{row['areas_total']}" if row['axis'] == 'volume' else None,
                    row['areas_missing']]
            lines.append('| ' + ' | '.join('-' if v is None else f'{v:.4f}' if isinstance(v, float)
                                          else str(v) for v in vals) + ' |')
    lines += ['', '## 分野別得点', '', '| 構成 | 課題 | area | 平均raw score | perf_timeout |', '|---|---|---|---:|---:|']
    for cfg in configs:
        for task in tasks:
            rs = [r for r in records if r['config'] == cfg['spec'] and r['task'] == task]
            for area in sorted({a for r in rs for a in r['areas']}):
                value = mean([r['areas'].get(area, {}).get('score') for r in rs])
                perf_timeout = sum(r['areas'].get(area, {}).get('perf_timeout', 0) for r in rs)
                lines.append(f"| {cfg['spec']} | {task} | {area} | {value if value is not None else '-'} | {perf_timeout} |")
    matrix = build_matrix(records)
    lines += render_matrix(matrix)
    (out / 'matrix.json').write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + '\n')
    (out / 'summary.md').write_text('\n'.join(lines) + '\n')


def report_only(dirs, out):
    records = []
    task_fixtures = None
    sources = list(dict.fromkeys(path.resolve() for path in dirs))
    for directory in sources:
        path = directory / 'results.jsonl'
        with path.open() as source:
            loaded = [json.loads(line) for line in source if line.strip()]
        for record in loaded:
            if 'axes' not in record:
                task = record['task']
                if task_fixtures is None:
                    task_fixtures = load_tasks()
                if task in task_fixtures:
                    record['axes'] = task_fixtures[task].get('axes', [])
                else:
                    record['axes'] = []
                    logger.warning('report_missing_axes_unknown_task task=%s path=%s', task, path)
        records.extend(loaded)
        logger.info('report_loaded path=%s records=%d', path, len(loaded))
    configs = [parse_config(spec) for spec in sorted({r['config'] for r in records})]
    tasks = sorted({r['task'] for r in records})
    write_summary(records, configs, tasks, out)
    logger.info('report_done sources=%d records=%d out=%s', len(sources), len(records), out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', action='append', default=[])
    p.add_argument('--tasks')
    p.add_argument('--suite', choices=('capability', 'efficiency', 'archived'), default='capability')
    p.add_argument('--repeat', type=int, default=1)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--timeout', type=int, default=900)
    p.add_argument('--budget-s', type=float)
    p.add_argument('--seed', type=int)
    p.add_argument('--self-check', action='store_true')
    p.add_argument('--report-only', nargs='+', type=Path, metavar='RESULTS_DIR')
    a = p.parse_args()
    if a.budget_s is not None and not (0 < a.budget_s < float('inf')):
        p.error('--budget-s must be a finite positive number')
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z',
                        handlers=[logging.StreamHandler(), logging.FileHandler(out / 'bench.log')])
    if a.report_only:
        report_only(a.report_only, out)
        print(out / 'summary.md')
        return
    alltasks = load_tasks()
    tasks = (a.tasks.split(',') if a.tasks is not None else
             sorted(task for task, spec in alltasks.items() if spec['suite'] == a.suite))
    for task in tasks:
        if task not in alltasks:
            p.error(f'unknown task {task}')
    if not a.self_check and not a.config:
        p.error('--config required unless --self-check')
    configs = [parse_config(x) for x in a.config]
    logger.info('bench_start suite=%s tasks=%s configs=%d repeat=%d seed=%s out=%s',
                a.suite if a.tasks is None else 'explicit', tasks, len(configs), a.repeat, a.seed, out)
    expected = {}
    table = ['| fixture | reference public | reference hidden | baseline hidden |', '|---|---:|---:|---:|']
    for task in tasks:
        ref = grade_ref(task, out / 'reference' / task)
        expected[task] = {area: v['total'] for area, v in ref['areas'].items()}
        if a.self_check:
            with tempfile.TemporaryDirectory(prefix='bench-baseline-') as tmp:
                source = Path(tmp) / 'source'
                base = prepare_workspace(task, source)
                changed, _, _ = check_diff(task, source, base)
                ws = prepare_grading_workspace(task, source, changed, Path(tmp) / 'grading')
                br = run_tests(ws, out / 'baseline' / task, task, expected[task])
            if br['infra_errors']:
                raise RuntimeError(f'baseline grading infra failure: {task}: {br["infra_errors"]}')
            table.append(f"| {task} | {ref['public']['passed']}/{ref['public']['total']} | {ref['hidden']['passed']}/{ref['hidden']['total']} | {br['hidden']['passed']}/{br['hidden']['total']} |")
    if a.self_check:
        report = '\n'.join(table) + '\n'
        (out / 'self-check.md').write_text(report)
        print(report, end='')
        return
    records = []
    rng = random.Random(a.seed)
    for n in range(1, a.repeat + 1):
        order = list(enumerate(configs))
        if a.seed is not None:
            rng.shuffle(order)
        for task in tasks:
            for idx, cfg in order:
                r = run_trial(cfg, idx, task, n, out, a.timeout, expected[task], a.budget_s)
                records.append(r)
                with (out / 'results.jsonl').open('a') as f:
                    f.write(json.dumps(r) + '\n')
    write_summary(records, configs, tasks, out, planned_trials=a.repeat)
    print(out / 'summary.md')


if __name__ == '__main__':
    main()
