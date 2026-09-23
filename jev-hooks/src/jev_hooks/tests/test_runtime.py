from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from jev_hooks import guards, runtime
from jev_hooks.config import load_config


class RuntimeAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = {"HOME": self.temp.name, "JEV_HOOKS_MODE": "on", "TYPESAFE_API_KEY": "test-key"}

    def tearDown(self):
        self.temp.cleanup()

    def test_codex_hook_specific_output_uses_documented_event_and_context_fields(self):
        with patch("jev_hooks.runtime.guards.advise_event", return_value="Research before asking."):
            result = runtime.evaluate_event("codex", {"hook_event_name": "PreToolUse", "tool_name": "AskUserQuestion"}, self.env)
        self.assertEqual(
            result,
            {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "Research before asking."}},
        )

    def test_codex_user_prompt_returns_only_a_skill_candidate_context(self):
        selection = {"status": "ok", "selected": [{"name": "research", "path": "/repo/.agents/skills/research/SKILL.md", "description": "Research uncertain topics."}]}
        with patch("jev_hooks.skills.select_skills", return_value=selection) as choose:
            result = runtime.evaluate_event("codex", {"hook_event_name": "UserPromptSubmit", "prompt": "research this"}, self.env)
        self.assertEqual(result["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertIn("research", result["hookSpecificOutput"]["additionalContext"])
        self.assertIn("候補", result["hookSpecificOutput"]["additionalContext"])
        choose.assert_called_once()

    def test_explicit_skill_invocation_is_not_overridden(self):
        with patch("jev_hooks.skills.select_skills") as choose:
            result = runtime.evaluate_event("codex", {"hook_event_name": "UserPromptSubmit", "prompt": "/research this"}, self.env)
        self.assertEqual(result, {})
        choose.assert_not_called()

    def test_observe_mode_always_emits_empty_object(self):
        observe = {**self.env, "JEV_HOOKS_MODE": "observe"}
        with patch("jev_hooks.runtime.guards.advise_event", return_value="A useful check remains."):
            result = runtime.evaluate_event("codex", {"hook_event_name": "PostToolUse", "tool_name": "exec_command"}, observe)
        self.assertEqual(result, {})

        selection = {"status": "ok", "selected": [{"name": "research", "path": "/repo/research/SKILL.md", "description": "Research uncertain topics."}]}
        with patch("jev_hooks.skills.select_skills", return_value=selection) as choose:
            result = runtime.evaluate_event("codex", {"hook_event_name": "UserPromptSubmit", "prompt": "find current docs"}, observe)
        self.assertEqual(result, {})
        choose.assert_called_once()

    def test_cursor_posttool_uses_documented_snake_case_context_and_permission_hook_is_absent(self):
        with patch("jev_hooks.runtime.guards.advise_event", return_value="Check the relevant tests.") as guard:
            result = runtime.evaluate_event("cursor", {"hook_event_name": "postToolUse", "tool_name": "Shell"}, self.env)
            self.assertEqual(result, {"additional_context": "Check the relevant tests."})
            guard.assert_called_once()
            guard.reset_mock()
            denied = runtime.evaluate_event("cursor", {"hook_event_name": "preToolUse", "tool_name": "Write"}, self.env)
        self.assertEqual(denied, {})
        guard.assert_not_called()

    def test_cursor_stop_and_before_prompt_do_not_emit_unsupported_context_fields(self):
        with patch("jev_hooks.runtime.guards.advise_event", return_value="Advice") as guard:
            self.assertEqual(runtime.evaluate_event("cursor", {"hook_event_name": "stop"}, self.env), {})
            self.assertEqual(runtime.evaluate_event("cursor", {"hook_event_name": "beforeSubmitPrompt", "prompt": "hello"}, self.env), {})
        guard.assert_not_called()

    def test_codex_subagent_advice_uses_user_visible_system_message_only(self):
        with patch("jev_hooks.runtime.guards.advise_event", return_value="Return the verification results."):
            result = runtime.evaluate_event("codex", {"hook_event_name": "SubagentStop", "last_assistant_message": "Done"}, self.env)
        self.assertEqual(result, {"systemMessage": "Jev助言（ユーザー向け表示）: Return the verification results."})
        self.assertNotIn("hookSpecificOutput", result)

    def test_grok_runs_advisory_evaluation_but_ignores_stdout_output(self):
        payload = {"hookEventName": "PreToolUse", "sessionId": "session", "toolName": "Edit", "toolInput": {"patch": "diff"}}
        with patch("jev_hooks.runtime.guards.advise_event", return_value="Do not apply a workaround.") as guard:
            result = runtime.evaluate_event("grok", payload, self.env)
        self.assertEqual(result, {})
        guard.assert_called_once()
        self.assertEqual(guard.call_args.args[1], "PreToolUse")

    def test_grok_posttool_failure_event_is_recognized_and_remains_passive(self):
        state_dir = Path(self.temp.name) / "grok-state"
        env = {**self.env, "JEV_HOOKS_STATE_DIR": str(state_dir)}
        payload = {
            "hookEventName": "PostToolUseFailure",
            "sessionId": "grok-session",
            "toolName": "Bash",
            "toolInput": {"command": "npm test"},
            "errorMessage": "command failed",
        }
        with patch("jev_hooks.service.record_skip"):
            result = runtime.evaluate_event("grok", payload, env)
        self.assertEqual(result, {})
        stored = guards._load_failure(load_config(env), "grok", "grok-session")
        self.assertIsNotNone(stored)

    def test_unknown_event_is_empty_and_does_not_evaluate(self):
        with patch("jev_hooks.runtime.guards.advise_event") as guard:
            result = runtime.evaluate_event("codex", {"hook_event_name": "FutureEvent"}, self.env)
        self.assertEqual(result, {})
        guard.assert_not_called()

    def test_run_hook_is_bounded_and_fail_open(self):
        out = io.StringIO()
        rc = runtime.run_hook("codex", io.StringIO("not-json"), out, self.env)
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out.getvalue()), {})

        out = io.StringIO()
        oversized = io.StringIO(json.dumps({"hook_event_name": "PreToolUse", "payload": "x" * 25_000}))
        with patch("jev_hooks.runtime.evaluate_event", side_effect=AssertionError("oversized input should be ignored")) as evaluate:
            rc = runtime.run_hook("codex", oversized, out, {**self.env, "JEV_HOOKS_MAX_TRANSCRIPT_BYTES": "10000"})
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out.getvalue()), {})
        evaluate.assert_called_once_with("codex", {}, environ={**self.env, "JEV_HOOKS_MAX_TRANSCRIPT_BYTES": "10000"})

        out = io.StringIO()
        with patch("jev_hooks.runtime.guards.advise_event", side_effect=RuntimeError("failure")):
            rc = runtime.run_hook("codex", io.StringIO(json.dumps({"hook_event_name": "PostToolUse", "tool_name": "exec_command"})), out, self.env)
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out.getvalue()), {})


if __name__ == "__main__":
    unittest.main()
