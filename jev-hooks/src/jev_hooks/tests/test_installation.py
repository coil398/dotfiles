"""Deployment preserves unrelated hooks; no-key launcher does not start Python."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("jev_install", ROOT / "install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallationTests(unittest.TestCase):
    def test_no_key_skips_python_and_state_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"PATH": "/nonexistent", "HOME": tmp}
            for runtime in ("codex", "cursor", "devin", "grok"):
                proc = subprocess.run(["/bin/sh", str(ROOT / "hook.sh"), runtime], input="{}", text=True,
                                      capture_output=True, env=env)
                self.assertEqual((proc.returncode, proc.stdout, proc.stderr), (0, "{}", ""))
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_environment_off_skips_python_even_with_key(self):
        proc = subprocess.run(["/bin/sh", str(ROOT / "hook.sh"), "codex"], input="{}", text=True,
                              capture_output=True, env={"PATH": "/nonexistent", "TYPESAFE_API_KEY": "test-key", "JEV_HOOKS_MODE": "off"})
        self.assertEqual((proc.returncode, proc.stdout, proc.stderr), (0, "{}", ""))

    def test_cursor_preserves_other_hooks_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            dest = home / ".cursor/hooks.json"
            dest.parent.mkdir()
            dest.write_text(json.dumps({"version": 1, "custom": "keep", "hooks": {
                "stop": [{"command": "other-stop"}, {"command": "python3 /repo/etc/jev-stop-guard-cursor-hook.py"}],
                "preToolUse": [{"command": "other-check"}]}}))
            self.assertTrue(installer.install("cursor", home))
            data = json.loads(dest.read_text())
            self.assertEqual(data["custom"], "keep")
            self.assertEqual(data["hooks"]["stop"][0]["command"], "other-stop")
            self.assertEqual(len(data["hooks"]["stop"]), 2)
            self.assertEqual(data["hooks"]["preToolUse"], [{"command": "other-check"}])
            self.assertFalse(installer.install("cursor", home))
            self.assertFalse(installer.install("cursor", home, check=True))

    def test_grok_has_no_unsupported_stop_continuation(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            installer.install("grok", home)
            data = json.loads((home / ".grok/hooks/jev-hooks.json").read_text())
            self.assertEqual(set(data["hooks"]), {"PreToolUse", "PostToolUse", "PostToolUseFailure"})

    def test_mixed_handler_group_keeps_other_handlers(self):
        group = {"matcher": "Bash", "hooks": [
            {"command": "other-policy"},
            {"command": "sh /repo/jev-hooks/hook.sh grok"},
        ]}
        self.assertEqual(installer.without_owned([group]), [{"matcher": "Bash", "hooks": [{"command": "other-policy"}]}])

    def test_check_missing_configuration_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            with self.assertRaises(ValueError):
                installer.install("cursor", home, check=True)
            self.assertEqual(list(home.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
