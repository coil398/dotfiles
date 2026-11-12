# /// script
# dependencies = []
# ///
"""Generate expected transcripts in a separate process using only vendored upstream."""
import json
import logging
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
program = '''import importlib.util, json, sys
sys.path.insert(0, sys.argv[1])
spec = importlib.util.spec_from_file_location("graphs", sys.argv[2])
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
assert sys.argv[1] in __import__("referencing").__file__
result = {area: [[m.transcript(m.graph(area, seed, variant)) for variant in range(12)] for seed in range(6)] for area in ("pointer", "base_uri", "dynamic", "recursive", "sequential")}
print(json.dumps(result, sort_keys=True))
'''
logging.info('oracle_start upstream=%s seeds=6 variants=12 areas=5', ROOT/'upstream')
proc = subprocess.run([sys.executable, '-c', program, str(ROOT/'upstream'), str(ROOT/'tests/_graphs.py')], capture_output=True, text=True, check=True)
(ROOT/'tests/_expected.json').write_text(proc.stdout)
logging.info('oracle_done bytes=%s', len(proc.stdout))
