import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "schema" / "fields.json"
GENERATED = ROOT / "shopkit" / "generated" / "fields.py"


def _render():
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import gen_fields
    finally:
        sys.path.pop(0)
    return gen_fields.render(json.loads(SPEC.read_text()))


def test_generated_matches_render():
    assert GENERATED.read_text() == _render()
    assert "discount_pct" in GENERATED.read_text()


def test_spec_declares_discount_pct():
    rule = json.loads(SPEC.read_text())["product"]["discount_pct"]
    assert rule["type"] == "int" and rule.get("min") == 0 and rule.get("max") == 100


def test_generator_cli_reproduces_committed_file(tmp_path):
    out = tmp_path / "fields.py"
    subprocess.run([sys.executable, str(ROOT / "tools" / "gen_fields.py"), "--out", str(out)],
                   check=True, cwd=ROOT)
    assert out.read_text() == GENERATED.read_text()
    assert "discount_pct" in out.read_text()
