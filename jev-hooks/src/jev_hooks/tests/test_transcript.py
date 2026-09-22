"""Transcript reader tests against the observed Codex rollout format."""

from __future__ import annotations

import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from jev_hooks import transcript as tr  # noqa: E402
from jev_hooks.tests import rollout_fixture as fx  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class TranscriptResolutionTests(unittest.TestCase):
    def test_browser_context_only_sends_the_request_text(self) -> None:
        self.assertEqual(
            tr.classify_user_text(
                "<in-app-browser-context>private-url-and-page</in-app-browser-context>\n"
                "## My request:\n続けて"
            ),
            ("user", "続けて"),
        )

    def test_missing_path_resolves_only_one_matching_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "sessions/2026/09/21"
            directory.mkdir(parents=True)
            path = directory / "rollout-2026-09-21-session-one.jsonl"
            path.write_text(
                '{"type":"session_meta","payload":{"id":"session-one"}}\n',
                encoding="utf-8",
            )
            env = {"CODEX_HOME": tmp}
            self.assertEqual(tr.resolve_codex_transcript(None, "session-one", env), str(path))
            with self.assertRaises(tr.TranscriptError):
                tr.resolve_codex_transcript(None, "other", env)

            duplicate = directory / "rollout-2026-09-22-session-one.jsonl"
            duplicate.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            with self.assertRaisesRegex(tr.TranscriptError, "matching sessions=2"):
                tr.resolve_codex_transcript(None, "session-one", env)

    def test_windows_transcript_path_is_converted_in_wsl(self) -> None:
        with patch.object(tr.subprocess, "check_output", return_value="/mnt/c/session.jsonl") as convert:
            result = tr.resolve_codex_transcript(
                "C:\\Users\\user\\session.jsonl",
                "session-one",
                {"WSL_DISTRO_NAME": "Ubuntu"},
            )
        self.assertEqual(result, "/mnt/c/session.jsonl")
        convert.assert_called_once_with(
            ["wslpath", "-u", "C:\\Users\\user\\session.jsonl"],
            text=True,
            timeout=1,
        )


class StaticFixtureTests(unittest.TestCase):
    def test_explain_only_fixture(self) -> None:
        ctx = tr.load_turn_context(
            str(FIXTURES / "codex_0153_rollout_explain_only_stop.jsonl"),
            "01a0b284-5a2a-7be3-af56-561ebadda2dd",
            max_bytes=1_000_000,
        )
        self.assertTrue(ctx.found_turn_start)
        self.assertFalse(ctx.window_truncated)
        self.assertEqual(ctx.parse_errors, 0)
        # AGENTS.md / environment_context wrappers and the user_message event echo are dropped;
        # the IDE wrapper is stripped to the request text.
        self.assertEqual([m.text for m in ctx.user_messages], ["player.ts の再生キューがどう動いているか説明して。コードは変えないで。"])
        self.assertTrue(ctx.user_messages[0].in_current_turn)
        self.assertEqual(len(ctx.tool_records), 1)
        self.assertEqual(ctx.tool_records[0].kind, "shell")
        self.assertEqual(ctx.tool_records[0].summary, "cat src/audio/player.ts")
        self.assertIs(ctx.tool_records[0].ok, True)
        self.assertEqual(ctx.files_changed, [])
        self.assertEqual(ctx.assistant_messages_in_turn, 1)
        self.assertFalse(ctx.user_message_after_last_assistant)

    def test_correction_fixture_scopes_records_to_current_turn(self) -> None:
        ctx = tr.load_turn_context(
            str(FIXTURES / "codex_0153_rollout_correction_continue.jsonl"),
            "01a0b290-bbbb-7000-8000-000000000020",
            max_bytes=1_000_000,
        )
        self.assertTrue(ctx.found_turn_start)
        texts = [m.text for m in ctx.user_messages]
        self.assertEqual(
            texts,
            ["通知音の再生を実装して。再生中は他の効果音と重ならないようにして。", "なぜホーム画面でしか動かないように制限しているの？"],
        )
        self.assertEqual([m.in_current_turn for m in ctx.user_messages], [False, True])
        # Previous turn's tool calls and patch are not current-turn records.
        self.assertEqual(ctx.tool_records, [])
        self.assertEqual(ctx.files_changed, [])
        self.assertEqual(ctx.assistant_messages_in_turn, 1)

    def test_correction_fixture_previous_turn_has_patch(self) -> None:
        ctx = tr.load_turn_context(
            str(FIXTURES / "codex_0153_rollout_correction_continue.jsonl"),
            "01a0b290-aaaa-7000-8000-000000000010",
            max_bytes=1_000_000,
        )
        kinds = [(r.kind, r.ok) for r in ctx.tool_records]
        self.assertEqual(kinds, [("shell", True), ("patch", True)])
        self.assertEqual(ctx.files_changed, ["src/audio/SoundPlayer.ts"])


class BuilderTests(unittest.TestCase):
    def parse(self, lines, turn_id="t1"):
        return tr.parse_lines(lines, turn_id)

    def test_function_call_exec_command_with_exit_code(self) -> None:
        lines = fx.implementation_turn(
            "t1",
            "fix the bug",
            "done",
            tools=[
                fx.function_call("c1", "exec_command", {"cmd": "pytest -q"}),
                fx.function_call_output("c1", {"exit_code": 1, "output": "FAILED tests/test_x.py::test_y"}),
                fx.function_call("c2", "exec_command", {"cmd": ["git", "status"]}),
                fx.function_call_output("c2", {"exit_code": 0, "output": "clean"}),
            ],
        )
        ctx = self.parse(lines)
        self.assertEqual([(r.summary, r.ok) for r in ctx.tool_records], [("pytest -q", False), ("git status", True)])
        self.assertIn("FAILED", ctx.tool_records[0].failure_head)
        self.assertEqual(ctx.failed_tool_records, 1)

    def test_non_shell_function_call_is_tool_record(self) -> None:
        lines = fx.implementation_turn(
            "t1", "do", "done",
            tools=[fx.function_call("c1", "spawn_agent", {"task_name": "review"}), fx.function_call_output("c1", {"task_name": "/root/review"})],
        )
        ctx = self.parse(lines)
        self.assertEqual(ctx.tool_records[0].kind, "tool")
        self.assertTrue(ctx.tool_records[0].summary.startswith("spawn_agent("))
        self.assertIsNone(ctx.tool_records[0].ok)

    def test_custom_exec_multiple_commands_and_failure(self) -> None:
        lines = fx.implementation_turn(
            "t1", "do", "done",
            tools=[fx.exec_custom_call("c1", ['rg -n "foo" src', "npm test"]), fx.exec_custom_output("c1", exit_code=2, body="Error: 3 failed")],
        )
        ctx = self.parse(lines)
        self.assertEqual(ctx.tool_records[0].summary, 'rg -n "foo" src ; npm test')
        self.assertIs(ctx.tool_records[0].ok, False)

    def test_patch_apply_end_merges_into_function_call(self) -> None:
        lines = fx.implementation_turn(
            "t1", "do", "done",
            tools=[
                fx.function_call("p1", "apply_patch", {"input": "*** Begin Patch"}),
                fx.patch_apply_end("p1", {"src/a.py": "update", "src/b.py": "add"}),
                fx.function_call_output("p1", "Success. Updated the following files:\nM src/a.py\nA src/b.py"),
                fx.patch_apply_end("p2", {"src/c.py": "update"}, success=False),
            ],
        )
        ctx = self.parse(lines)
        self.assertEqual(len(ctx.tool_records), 2)
        self.assertEqual(ctx.tool_records[0].kind, "patch")
        self.assertIs(ctx.tool_records[0].ok, True)
        self.assertEqual(ctx.tool_records[0].files, ["src/a.py", "src/b.py"])
        self.assertIs(ctx.tool_records[1].ok, False)
        self.assertEqual(ctx.files_changed, ["src/a.py", "src/b.py", "src/c.py"])

    def test_hook_prompt_counts_and_progress_marker(self) -> None:
        lines = fx.implementation_turn(
            "t1", "implement X", "I will do it.",
            tools=[fx.exec_custom_call("c1", ["ls"]), fx.exec_custom_output("c1")],
        )
        lines += [fx.hook_prompt("continue please"), fx.assistant_message("Sorry, here is the plan again.")]
        ctx = self.parse(lines)
        self.assertEqual(ctx.hook_prompts_in_turn, 1)
        self.assertEqual([m.text for m in ctx.user_messages], ["implement X"])
        self.assertEqual(ctx.records_since_last_continuation, 0)
        self.assertEqual(ctx.assistant_messages_in_turn, 2)
        lines += [fx.exec_custom_call("c2", ["make"]), fx.exec_custom_output("c2"), fx.assistant_message("done")]
        ctx = self.parse(lines)
        self.assertEqual(ctx.records_since_last_continuation, 1)
        self.assertTrue(ctx.tool_records[-1].after_last_continuation)
        self.assertFalse(ctx.tool_records[0].after_last_continuation)

    def test_turn_aborted_and_user_steer(self) -> None:
        lines = fx.implementation_turn("t1", "do", "working...")
        ctx = self.parse(lines + [fx.turn_aborted("t1")])
        self.assertTrue(ctx.turn_aborted)
        ctx = self.parse(lines + [fx.turn_aborted("other")])
        self.assertFalse(ctx.turn_aborted)
        ctx = self.parse(lines + [fx.user_message("stop, do something else")])
        self.assertTrue(ctx.user_message_after_last_assistant)
        ctx = self.parse(lines + [fx.hook_prompt("go on")])
        self.assertFalse(ctx.user_message_after_last_assistant)

    def test_ide_wrapper_and_event_echo_dedupe(self) -> None:
        lines = fx.implementation_turn("t1", "Please refactor foo()", "ok", ide_wrapper=True)
        lines.insert(4, fx.user_message_event("# Context from my IDE setup:\n## My request:\nPlease refactor foo()\n"))
        ctx = self.parse(lines)
        self.assertEqual([m.text for m in ctx.user_messages], ["Please refactor foo()"])

    def test_developer_and_system_wrappers_ignored(self) -> None:
        lines = fx.implementation_turn("t1", "hi", "hello")
        lines.insert(3, fx.developer_message("<model_switch>...</model_switch>"))
        lines.insert(3, fx.user_message("<recommended_plugins>\n- x\n</recommended_plugins>"))
        lines.insert(3, fx.user_message("<permissions instructions>\nread only\n</permissions instructions>"))
        ctx = self.parse(lines)
        self.assertEqual([m.text for m in ctx.user_messages], ["hi"])

    def test_user_xml_like_message_without_closing_tag_is_kept(self) -> None:
        lines = fx.implementation_turn("t1", "<div> is rendered twice, fix it", "ok")
        ctx = self.parse(lines)
        self.assertEqual(ctx.user_messages[0].text, "<div> is rendered twice, fix it")

    def test_compaction_recovers_user_request(self) -> None:
        lines = [fx.session_meta(), fx.compacted(["original request: build the importer", "<environment_context>x</environment_context>"]), fx.task_started("t1"), fx.user_message("continue"), fx.turn_context("t1"), fx.assistant_message("plan...")]
        ctx = self.parse(lines)
        self.assertTrue(ctx.compaction_seen)
        self.assertEqual([(m.text, m.from_compaction) for m in ctx.user_messages], [("original request: build the importer", True), ("continue", False)])

    def test_missing_turn_start_uses_latest_marked_turn(self) -> None:
        lines = fx.implementation_turn("old", "first", "done first", tools=[fx.exec_custom_call("c1", ["a"]), fx.exec_custom_output("c1")])
        lines += [fx.task_started("other"), fx.user_message("second"), fx.exec_custom_call("c2", ["b"]), fx.exec_custom_output("c2"), fx.assistant_message("plan")]
        ctx = self.parse(lines, turn_id="unknown-turn")
        self.assertFalse(ctx.found_turn_start)
        self.assertEqual([r.summary for r in ctx.tool_records], ["b"])
        self.assertEqual([m.in_current_turn for m in ctx.user_messages], [False, True])

    def test_no_markers_at_all_treats_window_as_current_turn(self) -> None:
        lines = [fx.user_message("do it"), fx.exec_custom_call("c1", ["a"]), fx.exec_custom_output("c1"), fx.assistant_message("plan")]
        ctx = self.parse(lines, turn_id="t1")
        self.assertFalse(ctx.found_turn_start)
        self.assertEqual(len(ctx.tool_records), 1)
        self.assertEqual(len(ctx.user_messages), 1)

    def test_garbage_and_partial_lines_are_counted_not_fatal(self) -> None:
        lines = fx.implementation_turn("t1", "do", "done")
        lines.insert(2, "{not json")
        lines.insert(5, '"just a string"')
        lines.append(lines[-1][: len(lines[-1]) // 2])  # simulated in-progress write
        ctx = self.parse(lines)
        self.assertEqual(ctx.parse_errors, 3)
        self.assertEqual([m.text for m in ctx.user_messages], ["do"])

    def test_user_message_limit(self) -> None:
        earlier = []
        for i in range(6):
            earlier += [fx.task_started(f"e{i}"), fx.user_message(f"request {i}"), fx.assistant_message("ok")]
        lines = fx.implementation_turn("t1", "final request", "plan", earlier=earlier)
        ctx = tr.parse_lines(lines, "t1", max_user_messages=4)
        self.assertEqual([m.text for m in ctx.user_messages], ["request 3", "request 4", "request 5", "final request"])


class TailReadTests(unittest.TestCase):
    def test_tail_read_drops_partial_first_line(self) -> None:
        lines = fx.implementation_turn("t1", "do", "done", tools=[fx.exec_custom_call(f"c{i}", ["x" * 200]) for i in range(30)])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rollout.jsonl"
            fx.write(path, lines)
            size = path.stat().st_size
            got, truncated = tr.read_tail_lines(path, size // 2)
            self.assertTrue(truncated)
            self.assertLess(len(got), len(lines))
            import json

            for ln in got:
                json.loads(ln)  # every kept line is complete
            full, truncated = tr.read_tail_lines(path, size + 10)
            self.assertFalse(truncated)
            self.assertEqual(len(full), len(lines))

    def test_load_turn_context_errors(self) -> None:
        with self.assertRaises(tr.TranscriptError):
            tr.load_turn_context(None, "t", 1000)
        with self.assertRaises(tr.TranscriptError):
            tr.load_turn_context("/nonexistent/rollout.jsonl", "t", 1000)

    def test_truncated_window_without_turn_start_is_flagged(self) -> None:
        lines = fx.implementation_turn("t1", "do", "plan", tools=[fx.exec_custom_call(f"c{i}", ["y" * 300]) for i in range(40)])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rollout.jsonl"
            fx.write(path, lines)
            ctx = tr.load_turn_context(str(path), "t1", max_bytes=2000)
            self.assertTrue(ctx.window_truncated)
            self.assertTrue(ctx.found_turn_start)
            self.assertEqual([message.text for message in ctx.user_messages], ["do"])


class LongTranscriptRecoveryTests(unittest.TestCase):
    def load(self, tmp: str, lines: list[str], turn_id: str, max_bytes: int = 32_000) -> tr.TurnContext:
        path = Path(tmp) / "rollout.jsonl"
        fx.write(path, lines)
        return tr.load_turn_context(str(path), turn_id, max_bytes=max_bytes)

    def test_long_current_turn_recovers_prior_qa_request_and_current_only_evidence(self) -> None:
        older_requests = []
        for index in range(3):
            older_requests.extend([
                fx.task_started(f"older-{index}"),
                fx.user_message(f"older request {index}"),
                fx.assistant_message("older turn ended"),
            ])
        previous = fx.implementation_turn(
            "previous", "Run the Motitan Home flow QA in DEV.", "previous turn ended",
            earlier=older_requests,
            tools=[fx.function_call("old-call", "exec_command", {"cmd": "old QA check"}),
                   fx.function_call_output("old-call", {"exit_code": 0, "output": "old result"})],
        )
        current = fx.implementation_turn(
            "current", "continue", "current turn output",
            tools=[fx.function_call("current-call", "exec_command", {"cmd": "current QA check"}),
                   fx.function_call_output("current-call", {"exit_code": 0, "output": "x" * 35_000})],
        )
        with tempfile.TemporaryDirectory() as tmp:
            ctx = self.load(tmp, previous + current + [fx.turn_aborted("current")], "current")
            complete = self.load(
                tmp, previous + current + [fx.turn_aborted("current")], "current", max_bytes=1_000_000
            )

        self.assertTrue(ctx.window_truncated)
        self.assertTrue(ctx.found_turn_start)
        self.assertEqual([message.text for message in ctx.user_messages], [
            "older request 1", "older request 2", "Run the Motitan Home flow QA in DEV.", "continue",
        ])
        self.assertEqual(
            [(message.text, message.in_current_turn) for message in ctx.user_messages],
            [(message.text, message.in_current_turn) for message in complete.user_messages],
        )
        self.assertEqual([record.summary for record in ctx.tool_records], ["current QA check"])
        self.assertTrue(ctx.turn_aborted)

    def test_previous_turn_large_output_does_not_drop_its_request(self) -> None:
        previous = fx.implementation_turn(
            "previous", "Run the Motitan Home flow QA in DEV.", "previous turn ended",
            tools=[fx.function_call("old-call", "exec_command", {"cmd": "old QA check"}),
                   fx.function_call_output("old-call", {"exit_code": 0, "output": "x" * 35_000})],
        )
        current = fx.implementation_turn(
            "current", "continue", "current turn ended",
            tools=[fx.function_call("current-call", "exec_command", {"cmd": "current QA check"}),
                   fx.function_call_output("current-call", {"exit_code": 0, "output": "current result"})],
        )
        lines = previous + [fx.turn_aborted("previous")] + current
        with tempfile.TemporaryDirectory() as tmp:
            ctx = self.load(tmp, lines, "current")
            complete = self.load(tmp, lines, "current", max_bytes=1_000_000)

        self.assertTrue(ctx.found_turn_start)
        self.assertEqual([message.text for message in ctx.user_messages], [
            "Run the Motitan Home flow QA in DEV.", "continue",
        ])
        self.assertEqual(
            [(message.text, message.in_current_turn) for message in ctx.user_messages],
            [(message.text, message.in_current_turn) for message in complete.user_messages],
        )
        self.assertEqual([record.summary for record in ctx.tool_records], ["current QA check"])
        self.assertFalse(ctx.turn_aborted)


if __name__ == "__main__":
    unittest.main()
