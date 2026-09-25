from __future__ import annotations

import json
import io
import sqlite3
import tempfile
import unittest
from contextlib import closing, redirect_stderr
from pathlib import Path
from unittest.mock import patch

from jev_hooks.config import Config
from jev_hooks.jev_client import ChoiceAnswer, JevError, JevResult
from jev_hooks.logbook import log_path
from jev_hooks.service import evaluate, record_skip
from jev_hooks.telemetry import database_path, summarize


class ServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cfg = Config(
            mode="on",
            model="jev-1.13.0",
            api_url="https://example.invalid/eval",
            api_timeout_s=0.4,
            total_timeout_s=0.8,
            max_transcript_bytes=512,
            state_dir=str(self.root / "state"),
        )
        self.questions = {"q": {"type": "choice", "criteria": {"yes": "yes", "no": "no"}}}
        self.answer = JevResult(
            answers={"q": ChoiceAnswer("yes", {"yes": 0.9, "no": 0.1}, 0.9)},
            usage={"input_tokens": 10, "output_tokens": 2},
            model="jev-1.13.0",
            elapsed_ms=2,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_unrecorded_call_is_visible_without_failing_the_evaluation(self):
        stderr = io.StringIO()
        with patch("jev_hooks.service.record_event", return_value=False), redirect_stderr(stderr):
            result = evaluate("test", {}, self.questions, cfg=self.cfg,
                              environ={"TYPESAFE_API_KEY": "secret"}, ask_fn=lambda **kw: self.answer)
        self.assertEqual(result.status, "ok")
        self.assertIn("費用集計に含まれません", stderr.getvalue())
        self.assertNotIn("secret", stderr.getvalue())

    def test_dynamic_question_rubrics_are_scrubbed_too(self):
        secret = "sk-" + "a" * 30
        questions = {"q": {"type": "choice", "instructions": "Check token=" + secret,
                           "criteria": {"yes": "A skill with API_KEY=" + secret, "no": "not relevant"}}}
        seen = []
        def ask(**kwargs):
            seen.append(kwargs)
            return self.answer
        evaluate("skills", {}, questions, cfg=self.cfg, environ={"TYPESAFE_API_KEY": "key"}, ask_fn=ask)
        self.assertNotIn(secret, json.dumps(seen[0]["questions"]))
        self.assertEqual(set(seen[0]["questions"]["q"]["criteria"]), {"yes", "no"})

    def test_memory_low_confidence_keeps_candidates_and_one_usage_record(self):
        from jev_hooks.memory import rerank
        response = JevResult(answers={
            "memory_0_relevance": ChoiceAnswer("high", {"high": 1.0}, 0.2),
            "memory_0_applicability": ChoiceAnswer("direct", {"direct": 1.0}, 0.2),
        }, usage={"input_tokens": 100, "output_tokens": 10}, model="jev-1.13.0")
        candidates = [{"id": i, "summary": "Synthetic test note", "context": "", "tags": "test"} for i in (1, 2)]
        env = {"TYPESAFE_API_KEY": "key", "JEV_HOOKS_STATE_DIR": str(self.cfg.state_path())}
        with patch("jev_hooks.jev_client.ask", return_value=response):
            self.assertEqual(rerank("test", candidates, environ=env), candidates)
        totals = summarize(self.cfg.state_path())["totals"]
        self.assertEqual((totals["calls"], totals["api_attempted"]), (1, 1))

    def test_missing_key_skips_network_and_records_local_gate(self) -> None:
        calls = []
        result = evaluate(
            "policy-a", {"task": "safe"}, self.questions,
            cfg=self.cfg, environ={"HOME": str(self.root)}, ask_fn=lambda **kwargs: calls.append(kwargs),
            runtime="codex", event="stop",
        )
        self.assertEqual((result.status, result.reason), ("skipped", "api_key_missing"))
        self.assertEqual(calls, [])
        report = summarize(self.cfg.state_path())
        self.assertEqual(report["totals"]["calls"], 1)
        self.assertEqual(report["totals"]["api_attempted"], 0)
        self.assertEqual(report["totals"]["cost_known_calls"], 1)
        self.assertEqual(report["skip_reasons"], {"api_key_missing": 1})

    def test_mode_off_never_resolves_key_or_calls_client(self) -> None:
        calls = []
        off = Config(**{**self.cfg.__dict__, "mode": "off"})
        result = evaluate(
            "policy-a", {}, self.questions, cfg=off,
            environ={"HOME": str(self.root), "TYPESAFE_API_KEY": "test-key"},
            ask_fn=lambda **kwargs: calls.append(kwargs),
        )
        self.assertEqual((result.status, result.reason), ("skipped", "mode_off"))
        self.assertEqual(calls, [])
        record_skip("policy-a", "would_skip", cfg=off)
        self.assertFalse(off.state_path().exists())

    def test_success_scrubs_and_bounds_state_and_records_usage_once(self) -> None:
        calls = []

        def ask(**kwargs):
            calls.append(kwargs)
            return self.answer

        secret = "sk-" + "a" * 24
        source = {
            "api_key": "private-value-123",
            "message": f"Authorization: Bearer {secret}",
            "large": "x" * 4000,
        }
        result = evaluate(
            "policy-a", source, self.questions, cfg=self.cfg,
            environ={"HOME": str(self.root), "TYPESAFE_API_KEY": "key-used-for-request"},
            runtime="cursor", event="stop", session_id="private-session", turn_id="private-turn",
            timeout_s=1.0, ask_fn=ask,
        )
        self.assertEqual((result.status, result.reason), ("ok", "evaluated"))
        self.assertEqual(result.result, self.answer)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["timeout_s"], 0.4)
        sent = json.dumps(calls[0]["state"], ensure_ascii=False)
        self.assertNotIn("private-value-123", sent)
        self.assertNotIn(secret, sent)
        self.assertLessEqual(len(json.dumps(calls[0]["state"], ensure_ascii=False).encode()), 512)
        db_text = database_path(self.cfg.state_path()).read_bytes().decode("utf-8", errors="replace")
        for private in ("private-value-123", secret, "key-used-for-request", "private-session", "private-turn", "x" * 200):
            self.assertNotIn(private, db_text)
        with closing(sqlite3.connect(database_path(self.cfg.state_path()))) as conn:
            recorded_cwd = conn.execute("SELECT cwd FROM usage").fetchone()[0]
        self.assertEqual(recorded_cwd, str(Path.cwd().resolve()))
        report = summarize(self.cfg.state_path())
        self.assertEqual(report["totals"]["calls"], 1)
        self.assertEqual(report["totals"]["input_tokens"], 10)
        self.assertEqual(report["totals"]["output_tokens"], 2)

    def test_api_failure_is_fail_open_and_cost_unknown(self) -> None:
        def fail(**kwargs):
            raise JevError("API_TIMEOUT", "must not be persisted")

        result = evaluate(
            "policy-a", {}, self.questions, cfg=self.cfg,
            environ={"HOME": str(self.root), "TYPESAFE_API_KEY": "key"}, ask_fn=fail,
        )
        self.assertEqual((result.status, result.reason, result.result), ("error", "API_TIMEOUT", None))
        report = summarize(self.cfg.state_path())
        self.assertEqual(report["failure_reasons"], {"API_TIMEOUT": 1})
        self.assertEqual(report["totals"]["cost_unknown_calls"], 1)
        with closing(sqlite3.connect(database_path(self.cfg.state_path()))) as conn:
            self.assertEqual(conn.execute("SELECT reason FROM usage").fetchone()[0], "API_TIMEOUT")

    def test_cwd_is_local_metadata_and_failed_call_is_attributed(self) -> None:
        cwd = self.root / "private-project"
        request = {"api_key": "private-key-value", "message": "private request body"}
        calls = []

        def fail(**kwargs):
            calls.append(kwargs)
            raise JevError("API_TIMEOUT", "must not be persisted")

        result = evaluate(
            "policy-a", request, self.questions, cfg=self.cfg,
            environ={"HOME": str(self.root), "TYPESAFE_API_KEY": "key-used-for-request"},
            ask_fn=fail, cwd=cwd,
        )
        self.assertEqual((result.status, result.reason), ("error", "API_TIMEOUT"))
        self.assertEqual(len(calls), 1)
        self.assertNotIn("cwd", calls[0]["state"])
        self.assertNotIn(str(cwd), json.dumps(calls[0]["state"]))

        path = database_path(self.cfg.state_path())
        with closing(sqlite3.connect(path)) as conn:
            row = conn.execute("SELECT status, cwd FROM usage").fetchone()
        self.assertEqual(row, ("error", str(cwd.resolve())))
        db_text = path.read_bytes().decode("utf-8", errors="replace")
        for private in ("private-key-value", "private request body", "key-used-for-request", "must not be persisted"):
            self.assertNotIn(private, db_text)

    def test_successful_policy_log_keeps_cwd_as_local_metadata(self) -> None:
        cwd = self.root / "workspace"

        def answer(**kwargs):
            self.assertNotIn("cwd", kwargs["state"])
            return self.answer

        result = evaluate(
            "policy-a", {"task": "safe"}, self.questions, cfg=self.cfg,
            environ={"HOME": str(self.root), "TYPESAFE_API_KEY": "key"},
            ask_fn=answer, cwd=cwd,
        )
        self.assertEqual(result.status, "ok")
        entry = json.loads(log_path(self.cfg.state_path()).read_text(encoding="utf-8"))
        self.assertEqual(entry["cwd"], str(cwd.resolve()))

    def test_record_skip_is_best_effort_and_does_not_resolve_api_key(self) -> None:
        record_skip(
            "policy-a", "transcript_incomplete", cfg=self.cfg,
            environ={"HOME": str(self.root)}, runtime="devin", event="stop",
        )
        data = summarize(self.cfg.state_path())
        self.assertEqual(data["skip_reasons"], {"transcript_incomplete": 1})
        self.assertEqual(data["by_runtime"][0]["period"], "devin")

    def test_telemetry_failure_does_not_change_success_result(self) -> None:
        with patch("jev_hooks.service.record_event", side_effect=OSError("storage unavailable")):
            result = evaluate(
                "policy-a", {}, self.questions, cfg=self.cfg,
                environ={"HOME": str(self.root), "TYPESAFE_API_KEY": "key"},
                ask_fn=lambda **kwargs: self.answer,
            )
        self.assertEqual((result.status, result.reason), ("ok", "evaluated"))


if __name__ == "__main__":
    unittest.main()
