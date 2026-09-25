from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from jev_hooks.config import Config
from jev_hooks.report import main, render_html, render_text
from jev_hooks.telemetry import record_event, summarize


class ReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.state = self.root / "state"
        self.cfg = Config(state_dir=str(self.state))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_missing_database_renders_zero_data_without_fake_bars(self) -> None:
        data = summarize(self.state, days=30)
        text = render_text(data)
        page = render_html(data)
        self.assertIn("0 calls / API 0", text)
        self.assertIn("まだ記録がありません", text)
        self.assertIn("まだ記録がありません", page)
        self.assertNotIn('<div class="bar-row">', page)

    def test_standalone_html_escapes_untrusted_labels_and_has_no_cdn(self) -> None:
        self.assertTrue(
            record_event(
                self.state,
                policy_id='<script>alert("policy")</script>',
                runtime="codex",
                event="stop",
                model="unknown",
                status="error",
                reason='<img src=x onerror="alert(1)">',
                api_attempted=True,
                usage={"input_tokens": 4, "output_tokens": 2},
                elapsed_ms=20,
                recorded_at="2026-09-22T10:00:00Z",
            )
        )
        page = render_html(summarize(self.state, days=30))
        self.assertIn("&lt;script&gt;alert(&quot;policy&quot;)&lt;/script&gt;", page)
        self.assertIn("&lt;img src=x onerror=&quot;alert(1)&quot;&gt;", page)
        self.assertNotIn('<script>alert("policy")</script>', page)
        self.assertNotIn("<img src=x", page)
        self.assertNotIn("cdnjs", page)
        self.assertIn("unknown 1", page)

    def test_cli_writes_html_and_emits_json(self) -> None:
        destination = self.root / "nested" / "report.html"
        output = io.StringIO()
        with patch("jev_hooks.report.load_config", return_value=self.cfg), redirect_stdout(output):
            code = main(["--days", "5", "--json", "--html", str(destination)])
        self.assertEqual(code, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["days"], 5)
        self.assertEqual(payload["totals"]["calls"], 0)
        self.assertTrue(destination.is_file())
        self.assertIn("<!doctype html>", destination.read_text(encoding="utf-8"))

    def test_usage_cli_can_filter_by_cwd(self) -> None:
        first = self.root / "workspace" / "first"
        second = self.root / "workspace" / "second"
        common = {
            "runtime": "codex",
            "event": "stop",
            "model": "unknown",
            "status": "ok",
            "reason": "evaluated",
            "api_attempted": True,
            "usage": {"input_tokens": 3, "output_tokens": 1},
            "elapsed_ms": 10,
            "recorded_at": "2026-09-22T10:00:00Z",
        }
        self.assertTrue(record_event(self.state, policy_id="first-policy", cwd=first, **common))
        self.assertTrue(record_event(self.state, policy_id="second-policy", cwd=second, **common))

        output = io.StringIO()
        with patch("jev_hooks.report.load_config", return_value=self.cfg), redirect_stdout(output):
            code = main(["--days", "5", "--cwd", str(first), "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["cwd"], str(first.resolve()))
        self.assertEqual(payload["totals"]["calls"], 1)
        self.assertEqual(payload["by_policy"][0]["period"], "first-policy")

    def test_text_report_includes_policy_runtime_and_failure_reasons(self) -> None:
        record_event(
            self.state,
            policy_id="policy-1",
            runtime="cursor",
            event="stop",
            model="unknown",
            status="error",
            reason="API_TIMEOUT",
            api_attempted=True,
            usage=None,
            elapsed_ms=100,
            recorded_at="2026-09-22T10:00:00Z",
        )
        output = render_text(summarize(self.state, days=30))
        self.assertIn("Policy別", output)
        self.assertIn("policy-1", output)
        self.assertIn("Runtime別", output)
        self.assertIn("cursor", output)
        self.assertIn("API_TIMEOUT: 1", output)
        self.assertIn("unknown 1", output)


if __name__ == "__main__":
    unittest.main()
