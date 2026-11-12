# /// script
# dependencies = []
# ///
"""Run fixture acceptance in isolated copies, retaining compact JSON evidence."""
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import subprocess
import json
import logging
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
log = logging.getLogger('calibration')
AREAS = sorted(p.stem[5:] for p in (ROOT/'private/tests').glob('test_*.py'))


def run_suite(work, target, label):
    xml = work / 'result.xml'
    cmd = ['uv','run','-q','--no-project','--with','pytest','python','-m','pytest','-q',target,'--junitxml='+str(xml)]
    result = subprocess.run(cmd, cwd=work, capture_output=True, text=True, timeout=300)
    (ROOT/'private/results'/f'{label}.log').write_text(result.stdout+result.stderr)
    shutil.copy2(xml, ROOT/'private/results'/f'{label}.xml')
    cases = ET.parse(xml).getroot().findall('.//testcase')
    scores = {}
    for case in cases:
        area = case.attrib['classname'].split('.')[-1].removeprefix('test_')
        count = scores.setdefault(area, {'passed':0,'total':0})
        count['total'] += 1
        count['passed'] += not any(case.find(t) is not None for t in ('failure','error','skipped'))
    log.info('suite label=%s exit=%d passed=%d total=%d', label, result.returncode, sum(v['passed'] for v in scores.values()),len(cases))
    return {'exit':result.returncode,'areas':scores}


MUTATIONS = {
    'boolean': ('matching.py', "return all(matches(record, child) for child in node[1])", "return any(matches(record, child) for child in node[1])"),
    'quotes': ('tokens.py', "''.join(chars)", "''.join(chars).replace(' ', '')"),
    'missing': ('matching.py', 'if left is MISSING:\n        return False', 'if left is MISSING:\n        left = None'),
    'types': ('literals.py', "return float(text) if any(c in text for c in '.eE') else int(text)", 'return text'),
    'sorting': ('sorting.py', 'for field in reversed(fields):', 'for field in fields:'),
    'pagination': ('engine.py', "'total': len(rows)", "'total': len(rows[offset:offset + limit])"),
    'validation': ('pagination.py', 'type(offset) is not int', 'not isinstance(offset, int)'),
    'integration': ('cli.py', 'result = method(args.query,', "result = method('',"),
}


def main():
    (ROOT/'private/results').mkdir(exist_ok=True)
    evidence = {}
    with TemporaryDirectory(dir=ROOT/'private',prefix='grading-') as temp:
        base = Path(temp)
        def prepare(name, reference):
            work = base/name
            shutil.copytree(ROOT/'workspace',work)
            if reference:
                shutil.copytree(ROOT/'private/reference',work,dirs_exist_ok=True)
            shutil.copytree(ROOT/'private/tests',work/'tests_hidden')
            return work
        ref = prepare('reference',True)
        evidence['reference_public'] = run_suite(ref,'tests','reference_public')
        evidence['reference_hidden'] = run_suite(ref,'tests_hidden','reference_hidden')
        baseline = prepare('baseline',False)
        evidence['baseline_public'] = run_suite(baseline,'tests','baseline_public')
        evidence['baseline_hidden'] = run_suite(baseline,'tests_hidden','baseline_hidden')
        evidence['mutations'] = {}
        for area,(file,before,after) in MUTATIONS.items():
            work=prepare('mutation_'+area,True)
            path=work/'catalog'/file
            text=path.read_text()
            assert text.count(before)==1, (area, before)
            path.write_text(text.replace(before,after))
            evidence['mutations'][area]={'file':file,'before':before,'after':after,'result':run_suite(work,'tests_hidden','mutation_'+area)}
        evidence['determinism'] = [run_suite(ref,'tests_hidden',f'determinism_{i+1:02}') for i in range(10)]
    (ROOT/'private/results/summary.json').write_text(json.dumps(evidence,indent=2)+'\n')
    assert evidence['reference_public']['exit']==0
    assert evidence['reference_hidden']['exit']==0
    assert len(evidence['reference_hidden']['areas'])==8
    assert all(v=={'passed':5,'total':5} for v in evidence['reference_hidden']['areas'].values())
    assert all(m['result']['areas'][a]['passed']<5 for a,m in evidence['mutations'].items())
    assert all(r==evidence['reference_hidden'] for r in evidence['determinism'])
    baseline_score=sum(v['passed'] for v in evidence['baseline_hidden']['areas'].values())/40
    assert 0.1<=baseline_score<=0.4, baseline_score
    log.info('acceptance_passed baseline_score=%.3f',baseline_score)

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO,format='%(levelname)s %(name)s %(message)s')
    main()
