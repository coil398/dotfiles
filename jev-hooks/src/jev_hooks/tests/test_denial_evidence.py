import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from jev_hooks.denial_evidence import collect


def _repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    (root / "README.md").write_text("# demo\n\nこのリポジトリは PR を作らず main へ直接 push する。\n無関係な行\n", encoding="utf-8")
    (root / "CLAUDE.md").write_text("- force push だけは確認する。\n", encoding="utf-8")


class DenialEvidenceTest(unittest.TestCase):
    def test_push_denial_collects_rule_docs_and_impact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            ev = collect({
                "tool_name": "Bash",
                "tool_input": {"command": "git push origin main"},
                "tool_use_id": "toolu_1",
                "reason": "[Git Push to Default Branch] direct push",
                "cwd": str(root),
            })
        self.assertEqual(ev["denial"], {"kind": "classifier_verdict", "rule": "Git Push to Default Branch", "reason": "[Git Push to Default Branch] direct push"})
        self.assertEqual(ev["repository"]["branch"], "main")
        self.assertEqual([(r["file"], r["line"]) for r in ev["documented_rules"]], [("README.md", 3), ("CLAUDE.md", 1)])
        self.assertEqual(ev["documented_rules"][0]["matched"], ["push", "main"])
        self.assertEqual(ev["impact"], ["push"])
        self.assertIn("README.md:3", ev["summary_ja"])
        json.dumps(ev, ensure_ascii=False)

    def test_denial_kinds_and_secret_redaction(self) -> None:
        no_verdict = collect({"tool_name": "Bash", "tool_input": {"command": "ls"}, "reason": "Auto mode could not evaluate this action and is blocking it for safety"})
        self.assertEqual((no_verdict["denial"]["kind"], no_verdict["denial"]["rule"]), ("no_verdict", None))
        self.assertEqual(collect({"reason": "Classifier unavailable"})["denial"]["kind"], "classifier_unavailable")
        ev = collect({"tool_name": "Bash", "tool_input": {"command": "curl -H 'API_KEY=abcdef123456' https://api.prod.example.com"}, "reason": "[Data Exfiltration]"})
        self.assertNotIn("abcdef123456", ev["operation"]["summary"])
        self.assertEqual(ev["environment"]["target"], "production")
        self.assertIn("network_send", ev["impact"])
        self.assertEqual(ev["repository"], {"root": None})
        self.assertEqual(ev["documented_rules"], [])


if __name__ == "__main__":
    unittest.main()
