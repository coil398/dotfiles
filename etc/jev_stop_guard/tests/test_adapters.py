"""Cursor / Devin adapters and Codex trust-hash helpers."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from jev_stop_guard import cursor_hook, devin_hook, policy, transcript as tr  # noqa: E402
from jev_stop_guard.trust import apply_stop_trust, hook_hash, parse_stop_command  # noqa: E402


class CursorAdapterTests(unittest.TestCase):
    def test_aborted_and_ask_do_not_map(self) -> None:
        self.assertIsNone(cursor_hook.to_codex_payload({"status": "aborted", "conversation_id": "c"}, 2))
        self.assertIsNone(cursor_hook.to_codex_payload({"status": "completed", "composer_mode": "ask", "conversation_id": "c"}, 2))

    def test_loop_count_becomes_active_and_limit(self) -> None:
        mapped = cursor_hook.to_codex_payload(
            {"status": "completed", "conversation_id": "conv", "loop_count": 1, "transcript_path": "/t.jsonl"},
            2,
        )
        self.assertEqual(mapped["session_id"], "conv")
        self.assertEqual(mapped["turn_id"], "conv")
        self.assertTrue(mapped["stop_hook_active"])
        limited = cursor_hook.to_codex_payload(
            {"status": "completed", "conversation_id": "conv", "loop_count": 2},
            2,
        )
        self.assertEqual(limited["_skip"], "LIMIT_REACHED")

    def test_followup_output_shape(self) -> None:
        from jev_stop_guard.tests.test_state_and_limits import FakeJev, Harness, turn_lines

        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(tmp)
            path = h.transcript("s", turn_lines("t1"))
            payload = {
                "status": "completed",
                "conversation_id": "s",
                "loop_count": 0,
                "transcript_path": path,
                "hook_event_name": "stop",
            }
            out = io.StringIO()
            rc = cursor_hook.run_hook(io.StringIO(json.dumps(payload)), out, environ=h.env, ask_fn=h.jev)
            self.assertEqual(rc, 0)
            body = json.loads(out.getvalue())
            self.assertIn("followup_message", body)
            self.assertTrue(body["followup_message"].startswith("[jev-stop-guard]"))

    def test_cursor_transcript_extracts_user_and_followup(self) -> None:
        lines = [
            json.dumps({"role": "user", "message": {"content": [{"type": "text", "text": "implement the importer"}]}}),
            json.dumps({"role": "assistant", "message": {"content": [{"type": "text", "text": "I would plan it."}]}}),
            json.dumps({"role": "user", "message": {"content": [{"type": "text", "text": policy.REASON_CONTINUE_WORK}]}}),
        ]
        ctx = tr.parse_cursor_lines(lines, "conv")
        self.assertEqual([m.text for m in ctx.user_messages], ["implement the importer"])
        self.assertEqual(ctx.hook_prompts_in_turn, 1)
        self.assertEqual(ctx.last_assistant_text, "I would plan it.")


class DevinAdapterTests(unittest.TestCase):
    def test_maps_ids_and_fail_open_without_transcript(self) -> None:
        mapped = devin_hook.to_codex_payload(
            {"session_id": "s1", "prompt_id": "p1", "stop_hook_active": True, "hook_event_name": "Stop"}
        )
        self.assertEqual(mapped["session_id"], "s1")
        self.assertEqual(mapped["turn_id"], "p1")
        self.assertTrue(mapped["stop_hook_active"])
        out = io.StringIO()
        rc = devin_hook.run_hook(
            io.StringIO(json.dumps({"session_id": "s1", "prompt_id": "p1", "hook_event_name": "Stop"})),
            out,
            environ={"HOME": "/tmp", "JEV_STOP_GUARD_MODE": "on", "JEV_STOP_GUARD_STATE_DIR": "/tmp/jev-stop-guard-test-state"},
        )
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out.getvalue()), {})


class TrustTests(unittest.TestCase):
    def test_hash_is_stable_and_field_sensitive(self) -> None:
        a = hook_hash("stop", "python3 /tmp/x.py", timeout=10, status_message="Checking")
        b = hook_hash("stop", "python3 /tmp/x.py", timeout=10, status_message="Checking")
        c = hook_hash("stop", "python3 /tmp/y.py", timeout=10, status_message="Checking")
        self.assertTrue(a.startswith("sha256:"))
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    def test_apply_writes_state_for_stop_hook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text(
                '[[hooks.Stop]]\n'
                '[[hooks.Stop.hooks]]\n'
                'type = "command"\n'
                'command = "python3 /tmp/jev-stop-guard-codex-hook.py"\n'
                "timeout = 10\n"
                'statusMessage = "Checking for abandoned requested work"\n'
                "[hooks.state]\n"
            )
            changed, digest = apply_stop_trust(path)
            self.assertTrue(changed)
            self.assertTrue(digest.startswith("sha256:"))
            text = path.read_text()
            self.assertIn("trusted_hash", text)
            self.assertIn(digest, text)
            fields = parse_stop_command(text)
            self.assertEqual(fields["timeout"], 10)
            changed2, digest2 = apply_stop_trust(path)
            self.assertFalse(changed2)
            self.assertEqual(digest, digest2)


if __name__ == "__main__":
    unittest.main()
