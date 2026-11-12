# /// script
# dependencies = []
# ///
"""Reproduce manual bench grading in disposable copies; no model invocations."""
from pathlib import Path
from tempfile import TemporaryDirectory
from collections import defaultdict
import json
import logging
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
LOG = logging.getLogger("calibrate")
MUTATIONS = {
    "interval": ("index.py", "stop = self.boundary(rows, upper, upper=True)", "stop = self.boundary(rows, upper, upper=False)"),
    "duplicates": ("index.py", "        insort(self.buckets.setdefault(event.key, []), (event.timestamp, ordinal, event))", "        if any(row[2] == event for row in self.buckets.get(event.key, ())):\n            return\n        insort(self.buckets.setdefault(event.key, []), (event.timestamp, ordinal, event))"),
    "ordering": ("engine.py", "for peer in peers:", "for peer in reversed(peers):"),
    "watermarks": ("index.py", "self.expiry[0][0] < frontier", "self.expiry[0][0] <= frontier"),
    "late_events": ("engine.py", "item.timestamp < own - self.lateness", "item.timestamp <= own - self.lateness"),
    "flush": ("stream.py", "        if isinstance(item, Flush):\n            break\n", ""),
    "validation": ("validation.py", "isinstance(value, bool) or not isinstance(value, int)", "not isinstance(value, int)"),
    "performance": ("index.py", '''        start = self.boundary(rows, lower)
        stop = self.boundary(rows, upper, upper=True)
        for _, _, event in rows[start:stop]:
            self.metrics.add("candidate_visits")
            yield event''', '''        for timestamp, _, event in rows:
            self.metrics.add("range_probes", 2)
            self.metrics.add("candidate_visits")
            if lower <= timestamp <= upper:
                yield event'''),
}


def grade(label, reference=True, mutation=None, public=False):
    with TemporaryDirectory(prefix="temporal-join-grade-") as tmp:
        dest = Path(tmp)
        shutil.copytree(ROOT / "workspace", dest, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        if reference:
            shutil.copytree(ROOT / "private/reference", dest, dirs_exist_ok=True)
        shutil.copytree(ROOT / "private/tests", dest / "tests_hidden",
                        ignore=shutil.ignore_patterns("__pycache__"))
        if mutation:
            name, old, new = MUTATIONS[mutation]
            target = dest / "temporal_join" / name
            source = target.read_text()
            assert source.count(old) == 1, (mutation, source.count(old))
            target.write_text(source.replace(old, new))
        results = {}
        for suite in (["tests", "tests_hidden"] if public else ["tests_hidden"]):
            xml = dest / "results.xml"
            command = ["uv", "run", "-q", "--no-project", "--with", "pytest", "python", "-m", "pytest", "-q", suite, f"--junitxml={xml}"]
            proc = subprocess.run(command, cwd=dest, text=True, capture_output=True, timeout=300)
            areas = defaultdict(lambda: {"passed": 0, "total": 0, "failures": []})
            tree = ET.parse(xml)
            signatures = []
            for case in tree.iter("testcase"):
                area = case.attrib["classname"].split(".")[-1].removeprefix("test_")
                passed = not any(case.find(tag) is not None for tag in ("failure", "error", "skipped"))
                areas[area]["total"] += 1
                areas[area]["passed"] += int(passed)
                if not passed:
                    areas[area]["failures"].append(case.attrib["name"])
                signatures.append((area, case.attrib["name"], passed))
            results[suite] = {"exit": proc.returncode, "areas": dict(areas), "signature": sorted(signatures)}
            LOG.info("graded label=%s suite=%s passed=%d total=%d exit=%d", label, suite,
                     sum(a["passed"] for a in areas.values()), sum(a["total"] for a in areas.values()), proc.returncode)
            if proc.returncode and reference and not mutation:
                print(proc.stdout[-12000:])
        return results


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    results = {"reference": grade("reference", public=True), "baseline": grade("baseline", reference=False, public=True)}
    ref = results["reference"]["tests_hidden"]
    assert results["reference"]["tests"]["exit"] == 0
    assert ref["exit"] == 0
    assert len(ref["areas"]) == 8
    assert all(v["total"] == 5 for v in ref["areas"].values())
    baseline = results["baseline"]["tests_hidden"]["areas"]
    score = sum(a["passed"] for a in baseline.values()) / 40
    assert 0.1 <= score <= 0.4, score
    results["mutations"] = {}
    for area in MUTATIONS:
        result = grade("mutation-" + area, mutation=area)
        assert result["tests_hidden"]["areas"][area]["passed"] < 5, area
        results["mutations"][area] = result
    # Initial reference run is repetition 1; each subsequent run uses a fresh copy.
    results["determinism"] = [ref["signature"]]
    for i in range(2,11):
        result = grade(f"determinism-{i}")["tests_hidden"]
        assert result["exit"] == 0
        assert result["signature"] == ref["signature"]
        results["determinism"].append(result["signature"])
    (ROOT / "private/results.json").write_text(json.dumps(results, indent=2) + "\n")
    lines = ["# Calibration", "", "All runs use disposable copies of workspace/, overlay reference only for reference/mutation runs, then copy private/tests to tests_hidden/. Commands execute from that copy's root. No benchmark/model trials were run.", "", "Commands:", "", "```sh", "uv run -q --no-project --with pytest python -m pytest -q tests --junitxml=results.xml", "uv run -q --no-project --with pytest python -m pytest -q tests_hidden --junitxml=results.xml", "```", "", "Reproduce: `uv run --no-project private/calibrate.py` from this fixture directory.", "", "## Scores and mutations", "", "| Area | Reference | Baseline | Single mutation | Mutated area | Full hidden score |", "|---|---:|---:|---|---:|---:|"]
    for area, (file, old, new) in MUTATIONS.items():
        m = results["mutations"][area]["tests_hidden"]["areas"]
        lines.append(f"| {area} | 5/5 | {baseline[area]['passed']}/5 | {file}: `{old.splitlines()[0].strip()}` → `{(new.splitlines()[0].strip() if new else 'remove stop at Flush')}` | {m[area]['passed']}/5 | {sum(a['passed'] for a in m.values())}/40 |")
    rp = results['reference']['tests']['areas']['public']
    bp = results['baseline']['tests']['areas']['public']
    lines += ["", f"Reference: public {rp['passed']}/{rp['total']}, hidden 40/40 (1.0). Baseline: public {bp['passed']}/{bp['total']}, hidden {sum(a['passed'] for a in baseline.values())}/40 ({score:.3f}); all 40 cases collected without import failures.", "", "The starting package derives from the reference with four local faults: strict interval scan instead of indexed lookup; reversed peer emission; expiration delayed until both watermarks using their minimum; and a zero-lateness inclusive rejection rule. Its iterator also continues after Flush. See workspace source for the exact implementation; public docs do not disclose these faults.", "", "## Specification mapping", "", "Every assertion, including helper/oracle equality, maps to the public SPEC.md sections below. Metric/state assertions use sections 5 and 8. Case names and full pass/fail signatures are preserved in results.json.", "", "| Area (all five cases) | SPEC.md sections and assertions |", "|---|---|"]
    mappings = {
        'interval': '2 (closed range, keys, identity, negative/large times), 3 (oracle sequence), 7 (adapter parity)',
        'duplicates': '2–3 (occurrence Cartesian product, original identities, no deferred emission), 4 (equal watermarks), 6 (Flush)',
        'ordering': '2–3 (timestamp and arrival tie order, payload opacity, batch order), 5 (expiration), 7 (adapter parity)',
        'watermarks': '1 (atomic error), 4 (monotonicity), 5 (opposite-side frontier, exact counts, match before discard), 8 (evicted)',
        'late_events': '4 (own watermark, strict threshold, lateness, unknown), 5 (no late retention), 8 (no work for dropped event)',
        'flush': '1 (closed precedence), 5–6 (clear state, independent instances), 7 (single pass, no read-ahead, stop and propagate)',
        'validation': '1 (types, errors, atomicity, frozen messages, payload identity), 5 (read-only retained), 8 (read-only counters)',
        'performance': '2–3 (known pair counts), 5 (exact retained/key counts), 8 (actual probes, visits, expiration, sparse and dense bounds)',
    }
    for area, mapping in mappings.items(): lines.append(f"| {area} | {mapping} |")
    lines += ["", "## Determinism and limits", "", "Reference hidden suite: 10/10 fresh grading copies, each 40 passed; identical sorted (area, case name, pass) signatures. Small-input oracle scans all accepted history independently of reference indexes/eviction. Random case uses fixed seed 921. Large inputs use analytically known outputs; no sleep, network, clock or timing thresholds. Package uses only stdlib; tests use pytest.", "", "Each mutation is independently applied to a fresh reference, never cumulatively. Each of the eight mutations lowers its target area's score. The mutation harness asserts the original edit occurs exactly once. It does not change public/hidden tests or use model calls.", "", "Unverified: model discrimination and predicted model score ranges require parent-run trials; reference/baseline/mutations cannot establish model ordering. Size targets are approximate; this fixture keeps a compact seven-module production implementation rather than padding unrelated files."]
    (ROOT / "private/calibration.md").write_text("\n".join(lines)+"\n")


if __name__ == "__main__":
    main()
