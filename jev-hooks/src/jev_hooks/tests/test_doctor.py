from __future__ import annotations

import io
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from jev_hooks.config import Config
from jev_hooks.doctor import doctor
from jev_hooks.logbook import append
from jev_hooks.telemetry import record_event


class DoctorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.state = self.root / "state"
        self.current = self.root / "workspace" / "current"
        self.other = self.root / "workspace" / "other"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_doctor_shows_current_cwd_records_across_rotation_and_recorded_mode(self) -> None:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        common = {
            "runtime": "codex",
            "event": "stop",
            "model": "jev-latest",
            "status": "ok",
            "reason": "evaluated",
            "api_attempted": True,
            "usage": {"input_tokens": 12, "output_tokens": 3},
            "elapsed_ms": 50,
            "recorded_at": now,
        }
        self.assertTrue(record_event(self.state, policy_id="current-policy", cwd=self.current, **common))
        self.assertTrue(record_event(self.state, policy_id="other-policy", cwd=self.other, **common))
        self.assertTrue(
            append(
                self.state,
                {
                    "ts": now,
                    "policy_id": "current-policy",
                    "runtime": "codex",
                    "event": "stop",
                    "mode": "observe",
                    "answers": {"verdict": {"choice": "continue"}},
                },
                100_000,
                cwd=self.current,
            )
        )
        self.assertTrue(
            append(
                self.state,
                {
                    "ts": now,
                    "policy_id": "other-policy",
                    "runtime": "codex",
                    "event": "stop",
                    "mode": "on",
                    "answers": {"verdict": {"choice": "stop"}},
                },
                1,
                cwd=self.other,
            )
        )
        self.assertTrue((self.state / "decisions.jsonl.1").is_file())

        output = io.StringIO()
        cfg = Config(mode="on", state_dir=str(self.state))
        with (
            patch("jev_hooks.doctor.load_config", return_value=cfg),
            patch("jev_hooks.doctor.resolve_api_key", return_value=(None, "missing")),
            patch("jev_hooks.doctor._codex_registration"),
            patch("jev_hooks.doctor._path_registration"),
            patch("jev_hooks.doctor.normalize_cwd", return_value=str(self.current.resolve())),
        ):
            self.assertEqual(doctor(output), 0)

        rendered = output.getvalue()
        self.assertIn(f"current cwd       : {self.current.resolve()}", rendered)
        self.assertIn("cwd usage (30d)   : 1 calls / API 1 / skip 0 / error 0", rendered)
        self.assertIn("policy=current-policy mode_at_record=observe: verdict=continue", rendered)
        self.assertNotIn("other-policy", rendered)
        self.assertIn("mode              : on", rendered)


if __name__ == "__main__":
    unittest.main()
