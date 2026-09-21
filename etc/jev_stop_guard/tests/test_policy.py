"""Verdict combination, state construction bounds, redaction and response validation."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from jev_stop_guard import jev_client, policy, redact  # noqa: E402
from jev_stop_guard.jev_client import ChoiceAnswer  # noqa: E402
from jev_stop_guard.transcript import ToolRecord, TurnContext, UserMessage  # noqa: E402


def ans(choice: str, confidence: float = 0.9, qid: str = "") -> ChoiceAnswer:
    options = list(policy.QUESTIONS[qid]["criteria"]) if qid else [choice]
    probs = {o: 0.0 for o in options}
    probs[choice] = 1.0
    return ChoiceAnswer(choice=choice, probabilities=probs, confidence=confidence)


def answers(rk="execute_work", rw="work_remaining", bl="can_proceed", c_rk=0.9, c_rw=0.9, c_bl=0.9):
    return {
        "request_kind": ans(rk, c_rk, "request_kind"),
        "remaining_work": ans(rw, c_rw, "remaining_work"),
        "blocker": ans(bl, c_bl, "blocker"),
    }


class CombineTests(unittest.TestCase):
    T = 0.6

    def test_continue_work(self) -> None:
        d = policy.combine(answers(), self.T)
        self.assertEqual((d.verdict, d.reason_code), (policy.CONTINUE_WORK, "OK"))
        self.assertTrue(d.continues)

    def test_continue_verify(self) -> None:
        d = policy.combine(answers(rw="verification_remaining"), self.T)
        self.assertEqual(d.verdict, policy.CONTINUE_VERIFY)

    def test_explain_only_allows_stop_even_when_work_flagged(self) -> None:
        d = policy.combine(answers(rk="explain_or_plan_only"), self.T)
        self.assertEqual((d.verdict, d.reason_code), (policy.ALLOW_STOP, "EXPLAIN_OR_PLAN_ONLY"))

    def test_user_stop_wins_at_low_confidence(self) -> None:
        d = policy.combine(answers(rk="stop_or_narrow", c_rk=0.1), self.T)
        self.assertEqual((d.verdict, d.reason_code), (policy.ALLOW_STOP, "USER_STOPPED"))

    def test_complete_allows_stop(self) -> None:
        d = policy.combine(answers(rw="complete"), self.T)
        self.assertEqual((d.verdict, d.reason_code), (policy.ALLOW_STOP, "COMPLETE"))

    def test_needs_user(self) -> None:
        d = policy.combine(answers(bl="needs_user"), self.T)
        self.assertEqual((d.verdict, d.reason_code), (policy.NEEDS_USER, "NEEDS_USER"))
        self.assertFalse(d.continues)

    def test_unclear_options_skip_without_resume(self) -> None:
        for kw, code in (({"rk": "unclear"}, "REQUEST_UNCLEAR"), ({"rw": "unclear"}, "REMAINING_UNCLEAR"), ({"bl": "unclear"}, "BLOCKER_UNCLEAR")):
            d = policy.combine(answers(**kw), self.T)
            self.assertEqual((d.verdict, d.reason_code), (policy.SKIPPED, code))

    def test_low_confidence_on_decisive_answers_skips(self) -> None:
        for kw in ({"c_rk": 0.5}, {"c_rw": 0.59}, {"c_bl": 0.0}):
            d = policy.combine(answers(**kw), self.T)
            self.assertEqual((d.verdict, d.reason_code), (policy.SKIPPED, "LOW_CONFIDENCE"), kw)
        d = policy.combine(answers(c_rk=0.6, c_rw=0.6, c_bl=0.6), self.T)
        self.assertEqual(d.verdict, policy.CONTINUE_WORK)

    def test_blocker_says_nothing_remains_is_conservative(self) -> None:
        d = policy.combine(answers(bl="no_remaining_work"), self.T)
        self.assertEqual((d.verdict, d.reason_code), (policy.ALLOW_STOP, "COMPLETE_PER_BLOCKER"))

    def test_threshold_zero_and_one(self) -> None:
        self.assertEqual(policy.combine(answers(c_rk=0.01, c_rw=0.01, c_bl=0.01), 0.0).verdict, policy.CONTINUE_WORK)
        self.assertEqual(policy.combine(answers(c_rk=0.99, c_rw=0.99, c_bl=0.99), 1.0).verdict, policy.SKIPPED)

    def test_questions_have_unclear_and_are_choice(self) -> None:
        for qid, q in policy.QUESTIONS.items():
            self.assertEqual(q["type"], "choice", qid)
            self.assertIn("unclear", q["criteria"], qid)
            self.assertGreaterEqual(len(q["criteria"]), 3)


class BuildStateTests(unittest.TestCase):
    def make_ctx(self, n_tools=3, n_files=2, long=False) -> TurnContext:
        ctx = TurnContext(turn_id="t1", found_turn_start=True)
        ctx.user_messages = [UserMessage(text=("x" * 5000 if long else "implement A"), in_current_turn=True)]
        for i in range(n_tools):
            ctx.tool_records.append(ToolRecord(kind="shell", summary=f"cmd {i} " + ("y" * 400 if long else ""), ok=(i % 2 == 0), failure_head="boom " * 100))
        ctx.files_changed = [f"src/f{i}.py" for i in range(n_files)]
        ctx.assistant_messages_in_turn = 2
        return ctx

    def test_bounds_and_shape(self) -> None:
        ctx = self.make_ctx(n_tools=100, n_files=80, long=True)
        ctx.user_messages *= 20
        state = policy.build_state(ctx, "z" * 10000, 1)
        msgs = state["conversation"]["user_messages_oldest_first"]
        self.assertEqual(len(msgs), policy.MAX_USER_MESSAGES)
        self.assertLessEqual(len(msgs[0]["text"]), policy.USER_MESSAGE_CHARS)
        self.assertLessEqual(len(state["conversation"]["agent_final_message"]), policy.FINAL_MESSAGE_CHARS)
        rec = state["execution_records_current_turn"]
        self.assertEqual(rec["tool_counts"], {"shell_success": 50, "shell_failure": 50})
        self.assertEqual(rec["tool_calls_total"], 100)
        self.assertEqual(rec["files_changed_total"], 80)
        blob = json.dumps(state, ensure_ascii=False)
        for omitted in ("cmd 0", "boom", "src/f", "tool_calls_latest", "failure_head"):
            self.assertNotIn(omitted, blob)
        self.assertEqual(state["auto_continuation"]["count_this_turn"], 1)
        self.assertIn("_note", state)
        self.assertLess(len(json.dumps(state, ensure_ascii=False)), 3_000)

    def test_history_notes(self) -> None:
        ctx = self.make_ctx()
        ctx.window_truncated = True
        ctx.found_turn_start = False
        ctx.compaction_seen = True
        ctx.parse_errors = 2
        state = policy.build_state(ctx, "final", 0)
        self.assertEqual(len(state["history_notes"]), 4)
        self.assertEqual(policy.build_state(self.make_ctx(), "final", 0)["history_notes"], [])

    def test_final_message_falls_back_to_transcript(self) -> None:
        ctx = self.make_ctx()
        ctx.last_assistant_text = "from transcript"
        self.assertEqual(policy.build_state(ctx, None, 0)["conversation"]["agent_final_message"], "from transcript")

    def test_secrets_are_redacted_in_state(self) -> None:
        # Built at runtime so the file never contains scanner-shaped literals.
        ts_live = "ts_live_" + "abcdefghijklmnop123456"
        github = "ghp_" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123"
        openai = "sk-proj-" + "abcdefghijklmnopqrstuvwxyz1234"
        openai_old = "sk-" + "abcdefghijklmnopqrstuvwxyz"
        slack = "xoxb-" + "1234567890-abcdefghij"
        ctx = TurnContext(turn_id="t1", found_turn_start=True)
        ctx.user_messages = [UserMessage(text=f"use TYPESAFE_API_KEY={ts_live} and {github}", in_current_turn=True)]
        ctx.tool_records = [ToolRecord(kind="shell", summary=f"curl -H 'Authorization: Bearer {openai}' https://x", ok=False, failure_head='{"error":"bad key ' + openai_old + '"}')]
        state = policy.build_state(ctx, f"export SLACK_TOKEN={slack} done", 0)
        blob = json.dumps(state, ensure_ascii=False)
        for secret in (ts_live, github, openai, openai_old, slack):
            self.assertNotIn(secret, blob, secret)
        self.assertIn("TYPESAFE_API_KEY=", blob)


class RedactTests(unittest.TestCase):
    def test_patterns(self) -> None:
        aws = "AKIA" + "ABCDEFGHIJKLMNOP"
        jwt = "eyJ" + "hbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abcdefghijklmnopqrstuvwxyz"
        google = "AIza" + "SyA-abcdefghijklmnopqrstuvwxyz0123456789"
        cases = {
            f"key {aws} here": aws,
            "-----BEGIN RSA PRIVATE KEY-----\nabc\n-----END RSA PRIVATE KEY-----": "abc",
            f"token {jwt}": "eyJhbGci",
            "password: hunter2hunter2": "hunter2hunter2",
            google: "AIzaSyA",
            "sha " + "a" * 64: "a" * 64,
        }
        for text, secret in cases.items():
            out = redact.redact(text)
            self.assertNotIn(secret, out, text)
            self.assertIn(redact.REDACTED, out)

    def test_git_sha_and_paths_survive(self) -> None:
        text = "commit 0123456789abcdef0123456789abcdef01234567 in /Users/someone/ghq/github.com/org/repo-name/src/a.py"
        self.assertEqual(redact.redact(text), text)

    def test_clip_keeps_head_and_tail(self) -> None:
        out = redact.clip("A" * 100 + "B" * 100, 50)
        self.assertLessEqual(len(out), 50)
        self.assertTrue(out.startswith("A"))
        self.assertTrue(out.endswith("B"))
        self.assertEqual(redact.clip("short", 50), "short")


class ResponseValidationTests(unittest.TestCase):
    def good_body(self):
        return {
            "model": "jev-latest",
            "answers": {
                "request_kind": {"type": "choice", "choice": "execute_work", "probabilities": {"execute_work": 0.9, "explain_or_plan_only": 0.05, "stop_or_narrow": 0.03, "unclear": 0.02}, "confidence": 0.85},
                "remaining_work": {"type": "choice", "choice": "work_remaining", "probabilities": {"work_remaining": 1.0}, "confidence": 1.0},
                "blocker": {"type": "choice", "choice": "can_proceed", "probabilities": {"can_proceed": 0.7, "needs_user": 0.3}, "confidence": 0.4},
            },
            "usage": {"input_tokens": 10, "output_tokens": 2},
        }

    def test_valid(self) -> None:
        res = jev_client.validate_response(self.good_body(), policy.QUESTIONS)
        self.assertEqual(res.answers["blocker"].probabilities["no_remaining_work"], 0.0)
        self.assertEqual(res.usage["input_tokens"], 10)

    def test_invalid_shapes(self) -> None:
        bad = []
        b = self.good_body(); del b["answers"]["blocker"]; bad.append(b)
        b = self.good_body(); b["answers"]["blocker"]["choice"] = "maybe"; bad.append(b)
        b = self.good_body(); b["answers"]["blocker"]["type"] = "score"; bad.append(b)
        b = self.good_body(); b["answers"]["blocker"]["confidence"] = "high"; bad.append(b)
        b = self.good_body(); b["answers"]["blocker"]["probabilities"] = {"can_proceed": 0.2}; bad.append(b)
        b = self.good_body(); b["answers"]["blocker"]["probabilities"]["can_proceed"] = 1.7; bad.append(b)
        bad.append([]); bad.append({"answers": "x"})
        for body in bad:
            with self.assertRaises(jev_client.JevError) as cm:
                jev_client.validate_response(body, policy.QUESTIONS)
            self.assertEqual(cm.exception.code, "API_BAD_RESPONSE")


if __name__ == "__main__":
    unittest.main()
