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
    def run_hook_with_stubs(self, tmp, runtime="codex", args=(), *, system="Darwin", key=None, launchd_key=None, mode=None):
        root = Path(tmp)
        bin_dir = root / "bin"
        bin_dir.mkdir(exist_ok=True)
        calls = root / "calls"
        launchctl = bin_dir / "launchctl"
        launchctl.write_text(
            "#!/bin/sh\n"
            f"printf '%s\\n' \"$*\" >> {str(calls)!r}\n"
            "if [ \"$1\" = getenv ] && [ \"$2\" = TYPESAFE_API_KEY ]; then\n"
            f"  printf '%s' {str(launchd_key or '')!r}\n"
            "fi\n"
        )
        launchctl.chmod(0o755)
        uname = bin_dir / "uname"
        uname.write_text(f"#!/bin/sh\nprintf '%s\\n' {system!r}\n")
        uname.chmod(0o755)
        python = bin_dir / "python3"
        python.write_text(
            "#!/bin/sh\n"
            f"printf '%s\\n' \"$@\" > {str(root / 'python-call')!r}\n"
            "printf '{\"key\":\"%s\",\"source\":\"%s\"}\\n' \"${TYPESAFE_API_KEY:-}\" \"${JEV_HOOKS_API_KEY_SOURCE:-}\"\n"
        )
        python.chmod(0o755)
        env = {"PATH": f"{bin_dir}:{os.environ['PATH']}", "HOME": str(root)}
        if key is not None:
            env["TYPESAFE_API_KEY"] = key
        if mode is not None:
            env["JEV_HOOKS_MODE"] = mode
        proc = subprocess.run(["/bin/sh", str(ROOT / "hook.sh"), runtime, *args], input="{}", text=True,
                              capture_output=True, env=env)
        return proc, calls, root / "python-call"

    def test_no_key_skips_python_and_state_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"PATH": "/nonexistent", "HOME": tmp}
            for runtime in ("claude", "codex", "cursor", "devin", "grok"):
                proc = subprocess.run(["/bin/sh", str(ROOT / "hook.sh"), runtime], input="{}", text=True,
                                      capture_output=True, env=env)
                self.assertEqual((proc.returncode, proc.stdout, proc.stderr), (0, "{}", ""))
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_environment_off_skips_python_even_with_key(self):
        proc = subprocess.run(["/bin/sh", str(ROOT / "hook.sh"), "codex"], input="{}", text=True,
                              capture_output=True, env={"PATH": "/nonexistent", "TYPESAFE_API_KEY": "test-key", "JEV_HOOKS_MODE": "off"})
        self.assertEqual((proc.returncode, proc.stdout, proc.stderr), (0, "{}", ""))

    def test_codex_uses_launchd_key_only_when_process_key_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc, calls, python_call = self.run_hook_with_stubs(tmp, launchd_key="launchd-key")
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(json.loads(proc.stdout), {"key": "launchd-key", "source": "launchd"})
            self.assertEqual(calls.read_text().splitlines(), ["getenv TYPESAFE_API_KEY"])
            self.assertEqual(python_call.read_text().splitlines(), [str(ROOT / "codex-hook.py")])

    def test_process_key_wins_without_launchd_lookup(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc, calls, _ = self.run_hook_with_stubs(tmp, key="process-key", launchd_key="launchd-key")
            self.assertEqual(json.loads(proc.stdout), {"key": "process-key", "source": None})
            self.assertFalse(calls.exists())

    def test_no_launchd_key_keeps_normal_hook_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc, calls, python_call = self.run_hook_with_stubs(tmp)
            self.assertEqual((proc.returncode, proc.stdout, proc.stderr), (0, "{}", ""))
            self.assertEqual(calls.read_text().splitlines(), ["getenv TYPESAFE_API_KEY"])
            self.assertFalse(python_call.exists())

    def test_off_non_mac_and_other_runtime_do_not_lookup_launchd(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc, calls, python_call = self.run_hook_with_stubs(tmp, mode="off")
            self.assertEqual((proc.returncode, proc.stdout), (0, "{}"))
            self.assertFalse(calls.exists())
            self.assertFalse(python_call.exists())
        for runtime, system in (("codex", "Linux"), ("cursor", "Darwin")):
            with self.subTest(runtime=runtime, system=system), tempfile.TemporaryDirectory() as tmp:
                proc, calls, python_call = self.run_hook_with_stubs(tmp, runtime=runtime, system=system)
                self.assertEqual((proc.returncode, proc.stdout), (0, "{}"))
                self.assertFalse(calls.exists())
                self.assertFalse(python_call.exists())

    def test_codex_launcher_doctor_forwards_diagnostic_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc, calls, python_call = self.run_hook_with_stubs(tmp, args=("--doctor",), launchd_key="doctor-key")
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(python_call.read_text().splitlines(), [str(ROOT / "jev.py"), "doctor"])
            self.assertIn('"source": "launchd"', proc.stdout)

    def test_cursor_preserves_other_hooks_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            dest = home / ".cursor/hooks.json"
            dest.parent.mkdir()
            dest.write_text(json.dumps({"version": 1, "custom": "keep", "hooks": {
                "stop": [{"command": "other-stop"},
                         {"command": "sh /old-checkout/jev-hooks/hook.sh cursor"},
                         {"command": "python3 /old-checkout/etc/jev-stop-guard-cursor-hook.py"}],
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
