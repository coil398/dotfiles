"""Stops without assistant text are fingerprinted by the transcript's last reply."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from jev_hooks import cursor_hook  # noqa: E402
from jev_hooks.tests.test_state_and_limits import Harness, turn_lines  # noqa: E402


def cursor_lines(final: str) -> list:
    return [
        json.dumps({"role": "user", "message": {"content": [{"type": "text", "text": "<timestamp>Friday, Sep 25, 2026, 12:36 PM (UTC+9)</timestamp>\n<user_query>\nimplement the importer\n</user_query>"}]}}),
        json.dumps({"role": "assistant", "message": {"content": [{"type": "tool_use", "name": "Shell", "input": {"command": "rg importer"}}]}}),
        json.dumps({"role": "assistant", "message": {"content": [{"type": "text", "text": final}]}}),
    ]


class MissingTextFingerprintTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.h = Harness(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_same_turn_with_new_reply_is_not_a_duplicate(self) -> None:
        h = self.h
        h.transcript("s", turn_lines("t1", final="first reply"))
        first = h.run(h.payload("s", "t1", None, active=False))
        self.assertNotEqual(first.record.get("reason_code"), "DUPLICATE_EVENT")
        h.transcript("s", turn_lines("t1", final="second reply"))
        second = h.run(h.payload("s", "t1", None, active=False))
        self.assertNotEqual(second.record.get("reason_code"), "DUPLICATE_EVENT")
        self.assertEqual(h.jev.calls, 2)

    def test_same_turn_with_same_reply_is_still_a_duplicate(self) -> None:
        h = self.h
        h.transcript("s", turn_lines("t1", final="same reply"))
        h.run(h.payload("s", "t1", None, active=False))
        again = h.run(h.payload("s", "t1", None, active=False))
        self.assertEqual(again.record["reason_code"], "DUPLICATE_EVENT")
        self.assertEqual(h.jev.calls, 1)

    def test_cursor_stop_without_text_or_generation_id(self) -> None:
        h = self.h
        path = Path(self._tmp.name) / "cursor.jsonl"
        codes = []
        for final in ("first reply", "second reply"):
            path.write_text("\n".join(cursor_lines(final)) + "\n", encoding="utf-8")
            payload = cursor_hook.to_codex_payload(
                {"status": "completed", "conversation_id": "conv", "loop_count": 0,
                 "transcript_path": str(path), "hook_event_name": "stop"},
                2,
            )
            self.assertIsNone(payload["last_assistant_message"])
            codes.append(h.run(payload).record.get("reason_code"))
        self.assertNotIn("DUPLICATE_EVENT", codes)
        self.assertEqual(h.jev.calls, 2)


if __name__ == "__main__":
    unittest.main()
