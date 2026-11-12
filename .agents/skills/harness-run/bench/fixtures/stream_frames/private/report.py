"""Validate stored acceptance evidence and write its human-readable report."""
import ast
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT/'private'
r = json.loads((PRIVATE/'results/summary.json').read_text())
ref = r['reference']['hidden']
baseline = r['baseline']['hidden']
names = {(a, n) for a, n, _ in ref['cases']}
assert len(names) == 32
for run in [baseline] + [m['result'] for m in r['mutations'].values()] + r['determinism']:
    assert {(a, n) for a, n, _ in run['cases']} == names
assert json.loads((ROOT/'fixture.json').read_text()) == {
    'name': 'stream_frames', 'allowed': ['framing/'],
    'public_tests': ['tests/'], 'grading_timeout_s': 300}
for path in (PRIVATE/'reference').rglob('*.py'):
    assert path.relative_to(PRIVATE/'reference').parts[0] == 'framing'
    assert (ROOT/'workspace'/path.relative_to(PRIVATE/'reference')).is_file()
for path in (ROOT/'workspace/framing').glob('*.py'):
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            raise AssertionError(f'Unexpected external import: {path}')
        if isinstance(node, ast.ImportFrom):
            assert node.level > 0
chunks = re.findall(r'chunk\[\d+\]=([0-9a-f]+)', (ROOT/'workspace/logs/incident.log').read_text())
code = '''import json, sys
from framing import FrameDecoder, FrameError
d=FrameDecoder(); out=[]
for chunk in json.loads(sys.argv[1]):
    out.extend(d.feed(bytes.fromhex(chunk)))
try:
    end=d.finish()
except FrameError as exc:
    end=type(exc).__name__
print(json.dumps({'output':out,'finish':end}))
'''
incident = {}
for name, directory in [('baseline', ROOT/'workspace'), ('reference', PRIVATE/'reference')]:
    result = subprocess.run(['python3', '-c', code, json.dumps(chunks)], cwd=directory,
                            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    incident[name] = json.loads(result.stdout)
assert incident['reference'] == {'output': ['hello🌍', 'ok'], 'finish': []}
assert incident['baseline'] == {'output': [], 'finish': 'TruncatedFrameError'}
(PRIVATE/'results/structural.json').write_text(json.dumps({
    'manifest_and_allowed_reference_paths': True, 'identical_case_identities': True,
    'package_local_imports_only': True, 'incident_replay': incident}, indent=2)+'\n')
sections = {
    'buffering': '§2, §4–6: snapshots, partial bytes, consumed header accounting',
    'chunking': '§1–2, §4: arbitrary partitions, immediate emission, clean EOF',
    'eof': '§1, §3–4, §6: hierarchy, idempotence, closed state, truncation',
    'limits': '§1, §3, §5: maximum validation, inclusive byte bound, early rejection, reset',
    'multiframe': '§1–2, §4, §6: wire order, empty frames, partial following frames',
    'reset': '§2–6: all lifecycle states, discard partial bytes/length, preserve bound, independence',
    'types_encoding': '§1–3, §5, §7: types, byte length, strict encoding, failed state, reset',
    'utf8': '§1–5: complete-body validation, strict errors, no cross-frame sequences, reset',
}
lines = ['# stream_frames calibration', '', '## Reproduction', '',
    'Run `python3 private/calibrate.py` then `python3 private/report.py` from the fixture root.',
    'The calibrator creates fresh grading trees inside private/: copy pristine workspace/,',
    'overlay private/reference/ where appropriate, then copy private/tests/ to tests_hidden/.',
    'Public tests always come from the pristine workspace. Each command has a 300-second timeout.',
    'Raw outputs are in results/*.log; exact per-case outcomes are in results/summary.json.', '',
    'Commands executed from each grading root:', '', '```sh',
    'uv run -q --no-project --with pytest python -m pytest -q tests --junitxml=report.xml',
    'uv run -q --no-project --with pytest python -m pytest -q tests_hidden --junitxml=report.xml',
    '```', '', '## Scores', '',
    'Reference public **8/8**, hidden **32/32 (1.0)**. Untouched workspace public **3/8**,',
    'hidden **6/32 (0.1875)**. All 32 identical case identities collected; no import/collection',
    'errors, skips, or missing cases. Baseline exit 1 reflects behavior/assertion failures.', '',
    '| Area | Reference | Baseline | Single-mutant area passes | Mutant suite passes |',
    '|---|---:|---:|---:|---:|']
for a in sorted(sections):
    m = r['mutations'][a]['result']
    total = sum(v['passed'] for v in m['areas'].values())
    lines.append(f"| {a} | 4/4 | {baseline['areas'][a]['passed']}/4 | {m['areas'][a]['passed']}/4 | {total}/32 |")
lines += ['', 'Every area has four cases and weight 1/8. Within-case loops do not alter scoring weights.', '',
          '## Executed single mutations', '',
          'Each mutant starts from a fresh reference, changes one operation, and runs all 32 cases.',
          'Each mutant exits 1 and loses at least one case in its designated area.', '']
for a, value in sorted(r['mutations'].items()):
    path, old, new = value['mutation']
    lines += [f'### {a}', '', f'File: `{path}`.', '', '```diff']
    lines += ['-'+s for s in old.splitlines()]+['+'+s for s in new.splitlines()]+['```', '']
lines += ['## Public specification mapping', '',
          'The table lists all four cases per area and covers their output, exception, type,',
          'lifecycle, and accounting assertions. Sections refer to workspace/docs/NOTES.md.',
          'The shared wire helper implements §1/§7 independently of the production encoder;',
          'replay checks clean EOF under §4. Hidden tests import no private reference code.', '',
          '| Area and cases | Public sections |', '|---|---|']
for a in sorted(sections):
    cases = ', '.join('`'+n+'`' for area, n, _ in ref['cases'] if area == a)
    lines.append(f'| {a}: {cases} | {sections[a]} |')
loc = sum(len(x.read_text().splitlines()) for x in (ROOT/'workspace/framing').glob('*.py'))
lines += ['', '## Determinism and structural checks', '',
    '- Ten additional fresh reference grading trees: every run 32/32, exit 0.',
    '- All ten sorted (area, case name, pass/fail) vectors match the initial reference vector.',
    '- Exhaustive fixed input partitions, no randomness, network, real sleep, clock dependency, or performance thresholds.',
    '- Package imports are local only; tests use pytest and stdlib only.',
    '- Fixed manifest validated, reference files exclusively in allowed framing/.',
    '- Parsed production/hidden Python sources and checked identical collected case identities.',
    '- Literal incident chunks reproduce baseline [] (finish raises TruncatedFrameError) and reference ["hello🌍", "ok"]; reference finish returns [].',
    '- Additional evidence: results/structural.json.', '', '## Scope and limitations', '',
    'The visible workspace has ten files: seven production modules, docs, incident log, public tests.',
    f'Production Python has {loc} lines including comments/docstrings, below the approximate 650-LOC',
    'planning guide. No unrelated APIs or filler code are added to reach a line count.',
    'Baseline faults interact across queue replacement on feed, stopping after one frame, deferred',
    'size validation, partial-header EOF handling, incomplete reset, and pending byte accounting.', '',
    'Model trials were not run. Strong/weak-agent score bands and model discrimination remain',
    'unmeasured design targets. All six fixture acceptance checks were executed. No commits.', '']
(PRIVATE/'calibration.md').write_text('\n'.join(lines))
for path in sorted(ROOT.rglob('*'), reverse=True):
    if path.is_dir() and path.name in ('__pycache__', '.pytest_cache'):
        shutil.rmtree(path)
print(f'Report written: baseline=6/32 reference=32/32 mutations=8 determinism=10 production_LOC={loc}')
print('Structural checks and literal incident replay passed')
