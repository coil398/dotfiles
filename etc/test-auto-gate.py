#!/usr/bin/env python3
"""Focused fixture tests for the Antigravity PreToolUse gate."""

from __future__ import annotations

import json
from pathlib import Path
import secrets
import subprocess
import unittest
from typing import Any


SCRIPT = Path(__file__).resolve().parents[1] / ".gemini/config/scripts/auto-gate.py"
HOOKS = Path(__file__).resolve().parents[1] / ".gemini/config/hooks.json"


def run_gate(payload: Any) -> dict[str, str]:
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    result = subprocess.run(
        [str(SCRIPT)],
        input=raw,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def command_payload(command: object) -> dict[str, object]:
    return {"toolCall": {"name": "run_command", "args": {"CommandLine": command}}}


class AutoGateTests(unittest.TestCase):
    def test_exact_read_only_command_is_allowed(self) -> None:
        self.assertEqual(run_gate(command_payload("git diff --check"))["decision"], "allow")

    def test_documented_runtime_arguments_do_not_block_safe_command(self) -> None:
        payload = {
            "stepIdx": 19,
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": "pwd",
                    "Cwd": "/workspace",
                    "Blocking": True,
                    "WaitMsBeforeAsync": 0,
                    "explanation": "fixture",
                },
                "runtimeMetadata": "fixture",
            },
        }
        self.assertEqual(run_gate(payload)["decision"], "allow")

    def test_unverified_command_asks_without_echoing_command(self) -> None:
        secret = secrets.token_hex(16)
        result = run_gate(command_payload(f"echo {secret}"))
        self.assertEqual(result["decision"], "ask")
        self.assertNotIn(secret, json.dumps(result))

    def test_shell_composition_and_dangerous_variants_ask(self) -> None:
        for command in (
            "git status --short; rm -rf /",
            "rm -rf -- /",
            "git push -f origin main",
            "git reset --hard HEAD",
            "git status | tee /tmp/status",
        ):
            with self.subTest(command=command):
                self.assertEqual(run_gate(command_payload(command))["decision"], "ask")

    def test_malformed_and_unknown_payloads_ask(self) -> None:
        for payload in (
            "not-json",
            {},
            {"toolCall": {"name": "run_command"}},
            {"toolCall": {"name": "future_tool", "args": {}}},
            command_payload(["git", "status"]),
        ):
            with self.subTest(payload=payload):
                self.assertEqual(run_gate(payload)["decision"], "ask")

    def test_known_non_command_tools_are_not_auto_allowed(self) -> None:
        payload = {"toolCall": {"name": "edit_file", "args": {"path": "x"}}}
        result = run_gate(payload)
        self.assertEqual(result["decision"], "ask")
        self.assertNotIn("x", json.dumps(result))

    def test_hook_delegates_to_the_python_source(self) -> None:
        hooks = json.loads(HOOKS.read_text(encoding="utf-8"))
        handlers = hooks["auto-mode-gate"]["PreToolUse"]
        self.assertEqual(len(handlers), 1)
        self.assertEqual(handlers[0]["matcher"], "run_command")
        self.assertEqual(
            handlers[0]["hooks"][0]["command"],
            "python3 ~/.gemini/config/scripts/auto-gate.py",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
