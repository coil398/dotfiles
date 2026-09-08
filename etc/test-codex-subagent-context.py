#!/usr/bin/env python3
"""Test the actual PreToolUse command stored in config.base.toml.

Run: python3 etc/test-codex-subagent-context.py
Requires Python 3.11+ for tomllib. No inference, network, or home writes.
This verifies the configured command, not live Codex hook trust/delivery.
"""
import json
from pathlib import Path
import re
import subprocess
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parent.parent


class SubagentContextPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = tomllib.loads((ROOT / ".codex/config.base.toml").read_text())
        groups = [g for g in cls.config["hooks"]["PreToolUse"]
                  if re.search(g["matcher"], "spawn_agent")]
        if len(groups) != 1 or len(groups[0]["hooks"]) != 1:
            raise AssertionError("Expected one dedicated spawn hook")
        cls.group = groups[0]
        cls.command = cls.group["hooks"][0]["command"]

    def invoke(self, args=None, raw=None, tool="spawn_agent", event_name="PreToolUse"):
        payload = raw if raw is not None else json.dumps({
            "hook_event_name": event_name, "tool_name": tool,
            "tool_input": args,
        })
        with tempfile.TemporaryDirectory() as cwd:
            result = subprocess.run(["bash", "-c", self.command], input=payload,
                                    capture_output=True, text=True, cwd=cwd, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            self.assertEqual(list(Path(cwd).iterdir()), [])
        return json.loads(result.stdout)["hookSpecificOutput"] if result.stdout else None

    def task(self, **extra):
        return dict(task_name="review", message="仕様と差分を評価する。Skillは/path/to/SKILL.md。", **extra)

    def assert_none(self, args):
        result = self.invoke(args)
        self.assertEqual(result["hookEventName"], "PreToolUse")
        self.assertEqual(result["permissionDecision"], "allow")
        expected = dict(args)
        expected.pop("fork_context", None)
        expected["fork_turns"] = "none"
        self.assertEqual(result["updatedInput"], expected)
        self.assertNotIn("additionalContext", result)
        return result["updatedInput"]

    def test_omitted_history_is_none(self):
        self.assert_none(self.task())

    def test_all_is_none(self):
        self.assert_none(self.task(fork_turns="all"))

    def test_partial_history_is_none(self):
        for value in ("1", "2", "999"):
            with self.subTest(value=value):
                self.assert_none(self.task(fork_turns=value))

    def test_none_is_preserved(self):
        self.assert_none(self.task(fork_turns="none"))

    def test_blank_null_and_invalid_history_are_none(self):
        for value in ("", " ALL ", None, 2, False, [], {}):
            with self.subTest(value=value):
                self.assert_none(self.task(fork_turns=value))

    def test_v2_legacy_field_is_removed(self):
        for value in (True, False, None):
            with self.subTest(value=value):
                self.assert_none(self.task(fork_context=value, fork_turns="all"))

    def test_model_effort_role_and_prompt_are_preserved(self):
        self.assert_none(self.task(model="gpt-5.6-sol", reasoning_effort="max",
                                   agent_type="default", fork_turns="all"))

    def test_nested_task_name_is_not_changed(self):
        args = self.task(fork_turns="all")
        args["task_name"] = "nested_worker"
        self.assert_none(args)

    def test_prompt_is_data_not_shell(self):
        args = self.task()
        args["message"] = "$(touch SHOULD_NOT_EXIST); `touch ALSO_NOT`; \" ' \n日本語"
        self.assert_none(args)

    def test_rewrite_is_idempotent(self):
        first = self.assert_none(self.task(fork_turns="all"))
        self.assertEqual(self.assert_none(first), first)

    def test_unrelated_tools_are_untouched(self):
        for tool in ("wait_agent", "followup_task", "Bash", "mcp__other__spawn_agent"):
            with self.subTest(tool=tool):
                self.assertIsNone(self.invoke(self.task(fork_turns="all"), tool=tool))
                self.assertIsNone(re.search(self.group["matcher"], tool))

    def test_other_event_is_untouched(self):
        self.assertIsNone(self.invoke(self.task(), event_name="PostToolUse"))

    def test_malformed_input_is_denied_without_echo(self):
        for raw in ("not-json", "[]", "null", "42"):
            with self.subTest(raw=raw):
                result = self.invoke(raw=raw)
                self.assertEqual(result["permissionDecision"], "deny")
                self.assertNotIn("updatedInput", result)

    def test_invalid_or_legacy_shape_is_denied(self):
        for args in (None, [], {}, {"message": "legacy"},
                     {"task_name": "x", "message": ""},
                     {"task_name": 4, "message": "task"}):
            with self.subTest(args=args):
                self.assertEqual(self.invoke(args)["permissionDecision"], "deny")

    def test_v2_and_wait_timeouts_remain_configured(self):
        self.assertTrue(self.config["features"]["hooks"])
        v2 = self.config["features"]["multi_agent_v2"]
        self.assertTrue(v2["enabled"])
        self.assertEqual((v2["min_wait_timeout_ms"], v2["default_wait_timeout_ms"],
                          v2["max_wait_timeout_ms"]), (600000, 1200000, 3600000))
        self.assertEqual(self.group["hooks"][0]["timeout"], 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
