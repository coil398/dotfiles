"""Claude Code runtime: transcript parser, Stop adapter, and advisory output shapes."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from jev_hooks import claude_hook, guards, runtime, transcript as tr  # noqa: E402
from jev_hooks.config import Config  # noqa: E402
from jev_hooks.tests.test_guards import evaluated  # noqa: E402
from jev_hooks.tests.test_state_and_limits import Harness  # noqa: E402


# ---- synthetic Claude Code transcript lines ------------------------------------


def user(text, prompt, uuid, **extra):
    return json.dumps({"type": "user", "message": {"role": "user", "content": text}, "promptId": prompt,
                       "uuid": uuid, "isSidechain": False, **extra})


def meta(text, prompt, uuid):
    return user(text, prompt, uuid, isMeta=True)


def assistant(items, uuid, message_id=None):
    return json.dumps({"type": "assistant", "message": {"role": "assistant", "id": message_id or uuid, "content": items},
                       "uuid": uuid, "isSidechain": False})


def text(value):
    return {"type": "text", "text": value}


def tool_use(call_id, name, tool_input):
    return {"type": "tool_use", "id": call_id, "name": name, "input": tool_input}


def tool_result(call_id, prompt, uuid, content="ok", is_error=None):
    item = {"type": "tool_result", "tool_use_id": call_id, "content": content}
    if is_error is not None:
        item["is_error"] = is_error
    return json.dumps({"type": "user", "message": {"role": "user", "content": [item]}, "promptId": prompt,
                       "uuid": uuid, "isSidechain": False})


def attachment(uuid):
    return json.dumps({"type": "attachment", "attachment": {"type": "date"}, "uuid": uuid, "isSidechain": False})


def main_transcript():
    return [
        json.dumps({"type": "queue-operation", "operation": "enqueue"}),
        user("fix the parser", "p1", "u1", origin={"kind": "human"}),
        assistant([tool_use("c0", "Read", {"file_path": "/repo/a.py"})], "a1"),
        tool_result("c0", "p1", "r1"),
        assistant([text("Fixed.")], "a2"),
        user("now add tests for the parser", "p2", "u2", origin={"kind": "human"}),
        meta("<system-reminder>context</system-reminder>", "p2", "m1"),
        attachment("at1"),
        assistant([{"type": "thinking", "thinking": ""}, tool_use("c1", "Bash", {"command": "make test"})], "a3", "msg3"),
        tool_result("c1", "p2", "r2", content="Exit code 1\nFAILED", is_error=True),
        assistant([tool_use("c2", "Edit", {"file_path": "/repo/test_a.py", "old_string": "a", "new_string": "b"})], "a4"),
        tool_result("c2", "p2", "r3"),
        assistant([text("I will stop here.")], "a5"),
        meta("Stop hook feedback:\n[hook]: [jev-stop-guard] continue", "p2", "m2"),
        json.dumps({"type": "user", "message": {"role": "user", "content": "side task text"}, "uuid": "s1", "isSidechain": True}),
        user("<task-notification>done</task-notification>", "p3", "n1", origin={"kind": "task-notification"}),
        assistant([tool_use("c3", "Bash", {"command": "make test"})], "a6"),
        tool_result("c3", "p2", "r4"),
        assistant([text("Tests pass now.")], "a7"),
    ]


def subagent_transcript():
    def side(line):
        obj = json.loads(line)
        obj.update({"isSidechain": True, "agentId": "agent1"})
        obj.pop("promptId", None)
        return json.dumps(obj)

    return [side(line) for line in (
        user("Review the diff and report findings", None, "su1"),
        meta("<system-reminder>x</system-reminder>", None, "sm1"),
        assistant([tool_use("k1", "Bash", {"command": "git diff"})], "sa1"),
        tool_result("k1", None, "sr1"),
        assistant([tool_use("k2", "SubagentHandback", {"message": "Two findings: A and B."})], "sa2"),
        tool_result("k2", None, "sr2"),
        assistant([text("Handed back.")], "sa3"),
    )]


class ClaudeTranscriptTests(unittest.TestCase):
    def test_current_turn_scoping_tools_and_hook_feedback(self) -> None:
        ctx = tr.parse_claude_lines(main_transcript(), "p2")
        self.assertTrue(ctx.found_turn_start)
        self.assertEqual([m.text for m in ctx.user_messages], ["fix the parser", "now add tests for the parser"])
        self.assertEqual([m.in_current_turn for m in ctx.user_messages], [False, True])
        self.assertEqual([(r.kind, r.ok) for r in ctx.tool_records], [("shell", False), ("patch", True), ("shell", True)])
        self.assertEqual(ctx.tool_records[0].summary, "make test")
        self.assertTrue(ctx.tool_records[0].failure_head.startswith("Exit code 1"))
        self.assertEqual(ctx.files_changed, ["/repo/test_a.py"])
        self.assertEqual(ctx.hook_prompts_in_turn, 1)
        self.assertEqual(ctx.records_since_last_continuation, 1)
        self.assertEqual(ctx.last_assistant_text, "Tests pass now.")
        self.assertEqual(ctx.assistant_messages_in_turn, 2)
        self.assertFalse(ctx.user_message_after_last_assistant)
        self.assertFalse(ctx.turn_aborted)
        self.assertEqual(ctx.parse_errors, 0)

    def test_interrupt_and_user_steer(self) -> None:
        lines = [
            user("build it", "p1", "u1"),
            assistant([tool_use("c1", "Bash", {"command": "make"})], "a1"),
            user("[Request interrupted by user for tool use]", "p1", "i1"),
        ]
        self.assertTrue(tr.parse_claude_lines(lines, "p1").turn_aborted)
        steered = tr.parse_claude_lines(lines[:2] + [user("actually use cmake", "p1", "u2")], "p1")
        self.assertTrue(steered.user_message_after_last_assistant)

    def test_unknown_turn_starts_at_latest_real_prompt(self) -> None:
        ctx = tr.parse_claude_lines(main_transcript(), "missing")
        self.assertFalse(ctx.found_turn_start)
        self.assertEqual([m.in_current_turn for m in ctx.user_messages], [False, True])
        self.assertEqual(len(ctx.tool_records), 3)

    def test_subagent_transcript_keeps_sidechain_and_handback(self) -> None:
        ctx = tr.parse_claude_lines(subagent_transcript(), "agent1")
        self.assertTrue(ctx.found_turn_start)
        self.assertEqual([m.text for m in ctx.user_messages], ["Review the diff and report findings"])
        self.assertEqual(len(ctx.tool_records), 2)
        self.assertEqual(ctx.handback_message, "Two findings: A and B.")

    def test_load_turn_context_detects_claude_and_prompt_id_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            path.write_text("\n".join(main_transcript()) + "\n")
            ctx = tr.load_turn_context(str(path), "p2", 1_000_000)
            self.assertEqual(ctx.hook_prompts_in_turn, 1)
            # The task notification and Stop hook feedback are not user prompts.
            self.assertEqual(tr.claude_prompt_id(str(path), 1_000_000), "p2")
            self.assertEqual(tr.claude_prompt_id(str(Path(tmp) / "absent.jsonl"), 1_000_000), "")


class ClaudeStopAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.h = Harness(self._tmp.name)
        self.path = self.h.transcript("claude", main_transcript())

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def payload(self, **extra):
        return {"session_id": "s", "prompt_id": "p2", "transcript_path": self.path, "cwd": "/work",
                "permission_mode": "default", "hook_event_name": "Stop", "stop_hook_active": False,
                "last_assistant_message": "Tests pass now.", "background_tasks": [], "session_crons": [], **extra}

    def run_hook(self, payload):
        out = io.StringIO()
        rc = claude_hook.run_hook(io.StringIO(json.dumps(payload)), out, environ=self.h.env, ask_fn=self.h.jev)
        self.assertEqual(rc, 0)
        return json.loads(out.getvalue())

    def test_mapping_uses_prompt_id_or_transcript_prompt(self) -> None:
        mapped = claude_hook.to_codex_payload(self.payload(), self.h.cfg)
        self.assertEqual((mapped["session_id"], mapped["turn_id"], mapped["_runtime"]), ("s", "p2", "claude"))
        without = self.payload()
        del without["prompt_id"]
        self.assertEqual(claude_hook.to_codex_payload(without, self.h.cfg)["turn_id"], "p2")

    def test_block_output_and_turn_limit(self) -> None:
        first = self.run_hook(self.payload())
        self.assertEqual(first["decision"], "block")
        self.assertTrue(first["reason"].startswith("[jev-stop-guard]"))
        second = self.run_hook(self.payload(stop_hook_active=True, last_assistant_message="Still here."))
        self.assertEqual(second["decision"], "block")
        third = self.run_hook(self.payload(stop_hook_active=True, last_assistant_message="Again."))
        self.assertEqual(third, {})
        self.assertEqual(self.h.jev.calls, 2)
        # A new prompt id with stop_hook_active=false is a new user turn.
        self.assertEqual(self.run_hook(self.payload(prompt_id="p3", last_assistant_message="New."))["decision"], "block")

    def test_background_tasks_allow_stop_without_evaluation(self) -> None:
        body = self.run_hook(self.payload(background_tasks=[{"id": "t", "type": "subagent", "status": "running"}]))
        self.assertEqual(body, {})
        self.assertEqual(self.h.jev.calls, 0)

    def test_cli_routes_claude_stop_to_adapter(self) -> None:
        from jev_hooks import cli

        with patch("jev_hooks.claude_hook.run_hook", side_effect=lambda stdin, stdout: (stdout.write("{}"), 0)[1]) as run, \
                patch("sys.stdin", io.StringIO(json.dumps(self.payload()))), patch("sys.stdout", io.StringIO()):
            self.assertEqual(cli.hook_main("claude", []), 0)
        run.assert_called_once()


class ClaudeRuntimeOutputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.env = {"HOME": self.temp.name, "JEV_HOOKS_MODE": "on", "TYPESAFE_API_KEY": "test-key"}

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_tool_events_add_context_without_permission_decision(self) -> None:
        for event in ("PreToolUse", "PostToolUse", "PostToolUseFailure"):
            with patch("jev_hooks.runtime.guards.advise_event", return_value="Check the tests.") as guard:
                result = runtime.evaluate_event("claude", {"hook_event_name": event, "tool_name": "Bash"}, self.env)
            self.assertEqual(result, {"hookSpecificOutput": {"hookEventName": event, "additionalContext": "Check the tests."}})
            self.assertEqual(guard.call_args.args[:2], ("claude", event))

    def test_subagent_stop_is_user_visible_system_message(self) -> None:
        with patch("jev_hooks.runtime.guards.advise_event", return_value="Report the checks."):
            result = runtime.evaluate_event("claude", {"hook_event_name": "SubagentStop", "agent_id": "a"}, self.env)
        self.assertEqual(result, {"systemMessage": "Jev助言（ユーザー向け表示）: Report the checks."})

    def test_user_prompt_skill_candidate_uses_claude_roots(self) -> None:
        selection = {"status": "ok", "selected": [{"name": "research", "path": "/h/.claude/skills/research/SKILL.md", "description": "Research."}]}
        with patch("jev_hooks.skills.select_skills", return_value=selection) as choose:
            result = runtime.evaluate_event("claude", {"hook_event_name": "UserPromptSubmit", "prompt": "research this", "cwd": "/w"}, self.env)
        self.assertEqual(result["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertIn("research", result["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(choose.call_args.kwargs["runtime"], "claude")

    def test_stop_and_unknown_events_are_empty(self) -> None:
        with patch("jev_hooks.runtime.guards.advise_event") as guard:
            self.assertEqual(runtime.evaluate_event("claude", {"hook_event_name": "Stop"}, self.env), {})
            self.assertEqual(runtime.evaluate_event("claude", {"hook_event_name": "SessionStart"}, self.env), {})
        guard.assert_not_called()


class ClaudeGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cfg = Config(mode="on", state_dir=str(self.root / "state"), max_transcript_bytes=200_000)
        self.env = {"HOME": str(self.root), "TYPESAFE_API_KEY": "test-key"}

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_post_tool_use_failure_error_is_stored(self) -> None:
        payload = {"hook_event_name": "PostToolUseFailure", "session_id": "s", "prompt_id": "p", "tool_name": "Bash",
                   "tool_input": {"command": "npm test"}, "error": "Exit code 1\nError: missing module"}
        with patch("jev_hooks.service.record_skip"):
            self.assertEqual(guards.advise_event("claude", "PostToolUseFailure", payload, cfg=self.cfg, environ=self.env), "")
        stored = guards._load_failure(self.cfg, "claude", "s")
        self.assertEqual(stored["tool_name"], "Bash")
        self.assertIn("Exit code 1", stored["summary"])

    def test_pretool_request_context_reads_claude_transcript_by_prompt_id(self) -> None:
        path = self.root / "main.jsonl"
        path.write_text("\n".join(main_transcript()) + "\n")
        payload = {"session_id": "s", "prompt_id": "p2", "transcript_path": str(path), "tool_name": "AskUserQuestion", "tool_input": {}}
        with patch("jev_hooks.service.evaluate", side_effect=lambda policy, state, questions, **kw: evaluated(questions, {})) as call:
            guards.advise_event("claude", "PreToolUse", payload, cfg=self.cfg, environ=self.env)
        transcript = call.call_args.args[1]["request_context"]["transcript"]
        self.assertEqual(transcript["recent_user_requests"][-1], "now add tests for the parser")

    def test_subagent_stop_uses_handback_report(self) -> None:
        path = self.root / "agent-agent1.jsonl"
        path.write_text("\n".join(subagent_transcript()) + "\n")
        payload = {"session_id": "s", "agent_id": "agent1", "agent_type": "general-purpose",
                   "agent_transcript_path": str(path), "last_assistant_message": "Handed back.", "stop_hook_active": False}
        with patch("jev_hooks.service.evaluate", side_effect=lambda policy, state, questions, **kw: evaluated(questions, {})) as call:
            guards.advise_event("claude", "SubagentStop", payload, cfg=self.cfg, environ=self.env)
        state = call.call_args.args[1]
        self.assertEqual(state["summary"], "Two findings: A and B.")
        self.assertEqual(state["task"], "Review the diff and report findings")


if __name__ == "__main__":
    unittest.main()
