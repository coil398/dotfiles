from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from jev_hooks import guards
from jev_hooks.config import Config
from jev_hooks.jev_client import ChoiceAnswer, JevResult
from jev_hooks.service import Evaluation
from jev_hooks.tests import rollout_fixture as fx


def evaluated(questions, choices, confidence=0.95):
    answers = {}
    for qid, question in questions.items():
        options = list(question["criteria"])
        choice = choices.get(qid, options[0])
        answers[qid] = ChoiceAnswer(
            choice=choice,
            probabilities={option: (1.0 if option == choice else 0.0) for option in options},
            confidence=confidence,
        )
    return Evaluation("ok", "evaluated", JevResult(answers=answers, model="fake", elapsed_ms=1))


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cfg = Config(mode="on", state_dir=str(self.root / "state"), max_transcript_bytes=20_000)
        self.env = {"HOME": str(self.root), "TYPESAFE_API_KEY": "test-key"}

    def tearDown(self):
        self.temp.cleanup()

    def test_question_gate_distinguishes_research_authorization_and_legitimate_question(self):
        payload = {"tool_name": "request_user_input", "user_request": "Inspect the current config and fix the issue."}
        with patch("jev_hooks.service.evaluate", side_effect=lambda policy, state, questions, **kw: evaluated(questions, {"ask_action": "research_first"})) as call:
            advice = guards.advise_event("codex", "PreToolUse", payload, cfg=self.cfg, environ=self.env)
        self.assertIn("ローカル確認やWeb調査", advice)
        self.assertIn("request_context", call.call_args.args[1])

        with patch("jev_hooks.service.evaluate", side_effect=lambda policy, state, questions, **kw: evaluated(questions, {"ask_action": "proceed_authorized"})):
            advice = guards.advise_event("codex", "PreToolUse", payload, cfg=self.cfg, environ=self.env)
        self.assertIn("追加承認を求めず", advice)

        with patch("jev_hooks.service.evaluate", side_effect=lambda policy, state, questions, **kw: evaluated(questions, {"ask_action": "ask_user"})):
            advice = guards.advise_event("codex", "PreToolUse", payload, cfg=self.cfg, environ=self.env)
        self.assertEqual(advice, "")

    def test_low_confidence_and_unknown_event_do_not_advise(self):
        with patch("jev_hooks.service.evaluate", return_value=evaluated({"ask_action": guards.ASK_ACTION}, {"ask_action": "research_first"}, confidence=0.4)):
            advice = guards.advise_event(
                "codex", "PreToolUse", {"tool_name": "AskUserQuestion"}, cfg=self.cfg, environ=self.env
            )
        self.assertEqual(advice, "")
        with patch("jev_hooks.service.evaluate") as call:
            self.assertEqual(guards.advise_event("codex", "NewFutureEvent", {}, cfg=self.cfg, environ=self.env), "")
        call.assert_not_called()

    def test_failed_call_is_bounded_and_identical_retry_is_compared(self):
        session = "session-1"
        failed_input = {"cmd": "npm test"}
        failure = {
            "session_id": session,
            "tool_name": "exec_command",
            "tool_input": failed_input,
            "failure_type": "exit_code",
            "error_message": "tool failed " + "x" * 5000,
        }
        self.assertEqual(guards.advise_event("codex", "PostToolUse", {**failure, "success": False}, cfg=self.cfg, environ=self.env), "")
        path = guards._failure_path(self.cfg, "codex", session)
        self.assertLessEqual(path.stat().st_size, guards._MAX_FAILURE_BYTES)
        stored = path.read_text(encoding="utf-8")
        self.assertNotIn("npm test", stored)
        self.assertNotIn("x" * 1_000, stored)

        proposed = {"session_id": session, "tool_name": "exec_command", "tool_input": failed_input}
        captured = {}

        def choose(_policy, state, questions, **kwargs):
            captured.update(state)
            return evaluated(questions, {"retry_action": "same_failed_condition"})

        with patch("jev_hooks.service.evaluate", side_effect=choose):
            advice = guards.advise_event("codex", "PreToolUse", proposed, cfg=self.cfg, environ=self.env)
        self.assertIn("失敗条件をそのまま", advice)
        self.assertTrue(captured["most_recent_failure"]["same_tool"])
        self.assertTrue(captured["most_recent_failure"]["identical_input"])

    def test_changed_retry_input_is_not_marked_identical(self):
        session = "session-2"
        guards.advise_event(
            "codex", "PostToolUse",
            {"session_id": session, "tool_name": "exec_command", "tool_input": {"cmd": "pytest"}, "error_message": "timeout", "success": False},
            cfg=self.cfg, environ=self.env,
        )
        captured = {}

        def choose(_policy, state, questions, **kwargs):
            captured.update(state)
            return evaluated(questions, {"retry_action": "changed_approach"})

        with patch("jev_hooks.service.evaluate", side_effect=choose):
            guards.advise_event(
                "codex", "PreToolUse",
                {"session_id": session, "tool_name": "exec_command", "tool_input": {"cmd": "pytest -q"}},
                cfg=self.cfg, environ=self.env,
            )
        self.assertFalse(captured["most_recent_failure"]["identical_input"])

    def test_failure_state_survives_read_only_calls_then_clears_on_next_success(self):
        session = "session-consume"
        path = guards._failure_path(self.cfg, "codex", session)
        guards.advise_event(
            "codex", "PostToolUse",
            {"session_id": session, "tool_name": "Bash", "tool_input": {"command": "pytest first.py"}, "tool_response": {"exit_code": 1, "output": "first failure"}},
            cfg=self.cfg, environ=self.env,
        )
        guards.advise_event(
            "codex", "PostToolUse",
            {"session_id": session, "tool_name": "Bash", "tool_input": {"command": "npm test"}, "tool_response": {"exit_code": 1, "output": "replacement failure"}},
            cfg=self.cfg, environ=self.env,
        )
        replacement = json.loads(path.read_text())
        self.assertIn("replacement failure", replacement["summary"])

        with patch("jev_hooks.service.evaluate") as call:
            guards.advise_event(
                "codex", "PostToolUse",
                {"session_id": session, "tool_name": "Bash", "tool_input": {"command": "rg -n pytest README.md"}, "tool_response": {"exit_code": 0, "output": "README.md: test"}},
                cfg=self.cfg, environ=self.env,
            )
        call.assert_not_called()
        self.assertEqual(guards._load_failure(self.cfg, "codex", session), replacement)

        guards.advise_event(
            "codex", "PostToolUse",
            {"session_id": session, "tool_name": "Bash", "tool_input": {"command": "python -c 'print(1)'"}, "tool_response": {"exit_code": 0, "output": "1"}},
            cfg=self.cfg, environ=self.env,
        )
        self.assertIsNone(guards._load_failure(self.cfg, "codex", session))

    def test_test_runner_position_and_mutating_shell_forms(self):
        for command in ("python -m pytest -q", "uv run python -m pytest -q", "uv run --project app python -m unittest", "rg pattern README.md\npytest -q"):
            self.assertTrue(guards._is_test_command({"command": command}), command)
        for command in ("rg -n pytest README.md", "rg 'a|pytest -q' README.md"):
            self.assertFalse(guards._is_test_command({"command": command}), command)
        for command in ("sed -i 's/a/b/' file", "find . -delete", "cat input > output", "git branch new", "rg --pre custom pattern ."):
            self.assertFalse(guards._is_read_only_command({"command": command}), command)
        self.assertTrue(guards._is_read_only_command({"command": "rg -n pytest README.md"}))
        self.assertTrue(guards._is_read_only_command({"command": "rg 'a > b' README.md"}))

    def test_subagent_partial_provenance_does_not_send_summary(self):
        from types import SimpleNamespace
        context = SimpleNamespace(user_messages=[object()], tool_records=[object()], window_truncated=True,
                                  found_turn_start=False, parse_errors=0)
        payload = {"agent_transcript_path": "/synthetic/transcript", "turn_id": "t", "last_assistant_message": "PRIVATE_MEMORY_SENTINEL"}
        with patch("jev_hooks.transcript.load_turn_context", return_value=context), patch("jev_hooks.service.evaluate") as call:
            self.assertEqual(guards.advise_event("codex", "SubagentStop", payload, cfg=self.cfg, environ=self.env), "")
        call.assert_not_called()

    def test_searching_for_test_name_is_not_a_test_invocation(self):
        payload = {"tool_name": "Bash", "tool_input": {"command": "rg -n pytest README.md"}}
        with patch("jev_hooks.service.evaluate") as call:
            result = guards.advise_event("codex", "PostToolUse", payload, cfg=self.cfg, environ=self.env)
        self.assertEqual(result, "")
        call.assert_not_called()

    def test_codex_posttool_nested_exit_code_and_mcp_is_error_are_cached_with_summary(self):
        shell_payload = {
            "session_id": "nested-shell",
            "tool_name": "Bash",
            "tool_input": {"command": "pytest tests/test_feature.py"},
            "tool_response": {"exit_code": 1, "output": "Script failed: assertion mismatch"},
        }
        mcp_payload = {
            "session_id": "nested-mcp",
            "tool_name": "mcp__server__run",
            "tool_input": {"operation": "check"},
            "tool_response": {"isError": True, "content": [{"type": "text", "text": "MCP call failed"}]},
        }
        with patch("jev_hooks.service.record_skip"), patch("jev_hooks.service.evaluate", side_effect=lambda policy, state, questions, **kw: evaluated(questions, {"verification": "verification_sufficient"})):
            guards.advise_event("codex", "PostToolUse", shell_payload, cfg=self.cfg, environ=self.env)
            guards.advise_event("codex", "PostToolUse", mcp_payload, cfg=self.cfg, environ=self.env)
            success_path = guards._failure_path(self.cfg, "codex", "nested-success")
            guards.advise_event(
                "codex", "PostToolUse",
                {"session_id": "nested-success", "tool_name": "Bash", "tool_input": {"command": "pytest"}, "tool_response": {"exit_code": 0, "output": "1 passed"}},
                cfg=self.cfg, environ=self.env,
            )
        shell = json.loads(guards._failure_path(self.cfg, "codex", "nested-shell").read_text())
        mcp = json.loads(guards._failure_path(self.cfg, "codex", "nested-mcp").read_text())
        self.assertEqual(shell["failure_type"], "exit_code_1")
        self.assertIn("Script failed", shell["summary"])
        self.assertEqual(mcp["failure_type"], "mcp_is_error")
        self.assertIn("MCP call failed", mcp["summary"])
        self.assertFalse(success_path.exists())

    def test_edit_root_cause_and_scope_are_independent_choices(self):
        choices = {"edit_root_cause": "symptom_only", "edit_scope": "scope_expansion"}
        with patch("jev_hooks.service.evaluate", side_effect=lambda policy, state, questions, **kw: evaluated(questions, choices)) as call:
            advice = guards.advise_event(
                "codex", "PreToolUse",
                {"tool_name": "apply_patch", "tool_input": {"patch": "- retry forever\n+ swallow all errors"}, "user_request": "Fix timeout handling."},
                cfg=self.cfg, environ=self.env,
            )
        self.assertIn("症状を抑える", advice)
        self.assertIn("依頼範囲を広げ", advice)
        self.assertEqual(set(call.call_args.args[2]), {"edit_root_cause", "edit_scope"})

    def test_agent_delegation_and_review_coverage_are_separate(self):
        choices = {"delegation_scope": "unnecessary_or_overlapping", "review_scope": "coverage_missing"}
        with patch("jev_hooks.service.evaluate", side_effect=lambda policy, state, questions, **kw: evaluated(questions, choices)) as call:
            advice = guards.advise_event(
                "codex", "PreToolUse",
                {"tool_name": "spawn_agent", "tool_input": {"task": "Review this code for correctness only."}, "user_request": "Implement secure token storage."},
                cfg=self.cfg, environ=self.env,
            )
        self.assertIn("独立性", advice)
        self.assertIn("重要な観点", advice)
        self.assertEqual(set(call.call_args.args[2]), {"delegation_scope", "review_scope"})

    def test_read_tools_do_not_call_jev(self):
        with patch("jev_hooks.service.evaluate") as call:
            result = guards.advise_event("codex", "PreToolUse", {"tool_name": "Read", "tool_input": {"file_path": "x.py"}}, cfg=self.cfg, environ=self.env)
        self.assertEqual(result, "")
        call.assert_not_called()

    def test_post_read_commands_memory_search_and_secret_file_actions_stay_local(self):
        cases = [
            ("Bash", {"command": "cat README.md"}, "PostToolUse"),
            ("Bash", {"command": "python /repo/jev.py memory-search --query recent"}, "PostToolUse"),
            ("mcp__ai_ltm__session_recall", {"query": "recent context"}, "PostToolUse"),
            ("Read", {"file_path": "/private/.zsh_secret"}, "PostToolUse"),
            ("Read", {"file_path": ".env.local"}, "PostToolUse"),
        ]
        with patch("jev_hooks.service.evaluate") as call, patch("jev_hooks.service.record_skip") as skip:
            for tool_name, tool_input, event in cases:
                runtime_name = "cursor" if tool_name == "Bash" and "memory-search" in tool_input.get("command", "") else "codex"
                event_name = "postToolUseFailure" if runtime_name == "cursor" else event
                self.assertEqual(
                    guards.advise_event(runtime_name, event_name, {"tool_name": tool_name, "tool_input": tool_input}, cfg=self.cfg, environ=self.env),
                    "",
                )
        call.assert_not_called()
        self.assertEqual(skip.call_count, len(cases) - 1)
        self.assertFalse((self.cfg.state_path() / "guard-failures").exists())

    def test_memory_word_in_an_unrelated_test_path_is_not_a_broad_skip(self):
        payload = {"tool_name": "Bash", "tool_input": {"command": "pytest tests/test_memory_router.py"}}
        with patch("jev_hooks.service.evaluate", side_effect=lambda policy, state, questions, **kw: evaluated(questions, {"verification": "verification_sufficient"})) as call:
            result = guards.advise_event("codex", "PostToolUse", payload, cfg=self.cfg, environ=self.env)
        self.assertEqual(result, "")
        call.assert_called_once()

    def test_missing_key_skips_before_transcript_read(self):
        env = {"HOME": str(self.root)}
        payload = {"tool_name": "Edit", "transcript_path": "/must/not/read", "turn_id": "turn"}
        with patch("jev_hooks.guards._transcript_context", side_effect=AssertionError("transcript read")) as transcript, patch("jev_hooks.service.record_skip") as skip, patch("jev_hooks.service.evaluate") as call:
            advice = guards.advise_event("codex", "PreToolUse", payload, cfg=self.cfg, environ=env)
        self.assertEqual(advice, "")
        transcript.assert_not_called()
        skip.assert_called_once()
        call.assert_not_called()

    def test_post_tool_success_can_advise_required_or_excessive_verification(self):
        payload = {"tool_name": "exec_command", "tool_input": {"cmd": "pytest"}, "tool_output": "1 passed"}
        with patch("jev_hooks.service.evaluate", side_effect=lambda policy, state, questions, **kw: evaluated(questions, {"verification": "required_check_missing"})):
            advice = guards.advise_event("codex", "PostToolUse", payload, cfg=self.cfg, environ=self.env)
        self.assertIn("必要な検証", advice)

        with patch("jev_hooks.service.evaluate", side_effect=lambda policy, state, questions, **kw: evaluated(questions, {"verification": "testing_redundant"})):
            advice = guards.advise_event("codex", "PostToolUse", payload, cfg=self.cfg, environ=self.env)
        self.assertIn("同じ検証", advice)

    def test_subagent_report_gap_is_advisory(self):
        transcript = self.root / "report.jsonl"
        fx.write(transcript, fx.implementation_turn("report-turn", "Implement feature", "Done", tools=[fx.exec_custom_call("c0", ["touch output.py"]), fx.exec_custom_output("c0")]))
        payload = {
            "agent_id": "agent-report",
            "turn_id": "report-turn",
            "agent_transcript_path": str(transcript),
            "last_assistant_message": "Done",
            "status": "completed",
        }
        with patch("jev_hooks.service.evaluate", side_effect=lambda policy, state, questions, **kw: evaluated(questions, {"subagent_report": "multiple_items_missing"})):
            advice = guards.advise_event("codex", "SubagentStop", payload, cfg=self.cfg, environ=self.env)
        self.assertIn("担当結果", advice)
        self.assertNotIn("block", advice.casefold())

    def test_official_codex_subagent_payload_reads_bounded_agent_transcript(self):
        transcript = self.root / "agent.jsonl"
        fx.write(
            transcript,
            fx.implementation_turn(
                "agent-turn",
                "Implement the parser and report tests.",
                "Implemented the parser; tests were not run.",
                tools=[fx.exec_custom_call("call-1", ["uv run pytest tests/parser.py"]), fx.exec_custom_output("call-1", exit_code=1, body="test failed")],
            ),
        )
        captured = {}

        def choose(_policy, state, questions, **kwargs):
            captured.update(state)
            return evaluated(questions, {"subagent_report": "verification_missing"})

        payload = {
            "agent_id": "agent-1",
            "agent_type": "generalPurpose",
            "turn_id": "agent-turn",
            "agent_transcript_path": str(transcript),
            "last_assistant_message": "Implemented the parser; tests were not run.",
        }
        with patch("jev_hooks.service.evaluate", side_effect=choose):
            advice = guards.advise_event("codex", "SubagentStop", payload, cfg=self.cfg, environ=self.env)
        self.assertIn("関連チェック", advice)
        self.assertIn("Implement the parser", captured["task"])
        self.assertIn("test failed", json.dumps(captured["transcript_evidence"], ensure_ascii=False))

    def test_subagent_stop_without_official_result_or_transcript_skips(self):
        transcript = self.root / "no-tools.jsonl"
        fx.write(transcript, fx.implementation_turn("no-tools-turn", "Implement feature", "Done"))
        with patch("jev_hooks.service.record_skip") as skip, patch("jev_hooks.service.evaluate") as call:
            summary_only = guards.advise_event(
                "codex", "SubagentStop",
                {"agent_id": "agent-2", "turn_id": "agent-turn", "last_assistant_message": "Done"},
                cfg=self.cfg, environ=self.env,
            )
            no_tool_provenance = guards.advise_event(
                "codex", "SubagentStop",
                {"agent_id": "agent-3", "turn_id": "no-tools-turn", "agent_transcript_path": str(transcript), "last_assistant_message": "Done"},
                cfg=self.cfg, environ=self.env,
            )
        self.assertEqual(summary_only, "")
        self.assertEqual(no_tool_provenance, "")
        self.assertEqual(skip.call_count, 2)
        call.assert_not_called()

    def test_subagent_memory_task_or_summary_is_not_sent(self):
        transcript = self.root / "memory-agent.jsonl"
        fx.write(
            transcript,
            fx.implementation_turn("memory-turn", "Use ai-ltm session_recall to retrieve memory context.", "Retrieved memory context.", tools=[fx.exec_custom_call("c0", ["python jev.py memory-search"]), fx.exec_custom_output("c0")]),
        )
        payload = {
            "agent_id": "memory-agent",
            "turn_id": "memory-turn",
            "agent_transcript_path": str(transcript),
            "last_assistant_message": "Retrieved memory context.",
        }
        with patch("jev_hooks.service.record_skip") as skip, patch("jev_hooks.service.evaluate") as call:
            advice = guards.advise_event("codex", "SubagentStop", payload, cfg=self.cfg, environ=self.env)
        self.assertEqual(advice, "")
        skip.assert_called_once()
        self.assertEqual(skip.call_args.args[1], "OPTIONAL_MEMORY_NOT_CONNECTED")
        call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
