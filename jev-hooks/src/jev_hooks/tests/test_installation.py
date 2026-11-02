"""Deployment preserves unrelated hooks; no-key launcher does not start Python."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
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
            self.assertEqual(json.loads(proc.stdout), {"key": "process-key", "source": ""})
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
            self.assertEqual(json.loads(proc.stdout), {"key": "doctor-key", "source": "launchd"})

    @unittest.skipUnless(shutil.which("zsh"), "zsh is required to exercise .zshrc")
    def test_zsh_publishes_only_exported_nonempty_key_on_macos(self):
        zshrc = (ROOT.parent / ".zshrc").read_text()
        start = zshrc.index("# Codex desktop hooks read exported keys")
        end = zshrc.index('[ -f "$HOME/.deno/env" ]', start)
        publish_block = zshrc[start:end]
        for system, assignment, expected in (
            ("Darwin", "export TYPESAFE_API_KEY=exported-key", "setenv TYPESAFE_API_KEY exported-key"),
            ("Darwin", "TYPESAFE_API_KEY=local-only-key", None),
            ("Darwin", "export TYPESAFE_API_KEY='   '", None),
            ("Linux", "export TYPESAFE_API_KEY=linux-key", None),
        ):
            with self.subTest(system=system, assignment=assignment), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                bin_dir = root / "bin"
                bin_dir.mkdir()
                calls = root / "launchctl-calls"
                launchctl = bin_dir / "launchctl"
                launchctl.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> {str(calls)!r}\n")
                launchctl.chmod(0o755)
                script = f"OS={system}\n{assignment}\n{publish_block}"
                proc = subprocess.run([shutil.which("zsh"), "-fc", script], text=True, capture_output=True,
                                      env={"PATH": f"{bin_dir}:{os.environ['PATH']}", "HOME": str(root)})
                self.assertEqual(proc.returncode, 0, proc.stderr)
                observed = calls.read_text().splitlines() if calls.exists() else []
                self.assertEqual(observed, [expected] if expected else [])

    def test_json_config_off_uses_launchd_but_skips_api_and_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            config = root / "config.json"
            config.write_text('{"mode":"off"}')
            state_dir = root / "state"
            calls = root / "launchctl-calls"
            uname = bin_dir / "uname"
            uname.write_text("#!/bin/sh\nprintf 'Darwin\\n'\n")
            uname.chmod(0o755)
            launchctl = bin_dir / "launchctl"
            launchctl.write_text(
                f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> {str(calls)!r}\nprintf 'test-key'\n"
            )
            launchctl.chmod(0o755)
            env = {
                "PATH": f"{bin_dir}:{os.environ['PATH']}",
                "HOME": str(root),
                "JEV_HOOKS_CONFIG": str(config),
                "JEV_HOOKS_STATE_DIR": str(state_dir),
                "JEV_HOOKS_API_URL": "http://127.0.0.1:1/v1/systemone",
            }
            proc = subprocess.run(["/bin/sh", str(ROOT / "hook.sh"), "codex"], input='{"event":"Stop"}',
                                  text=True, capture_output=True, env=env)
            self.assertEqual((proc.returncode, proc.stdout, proc.stderr), (0, "{}", ""))
            self.assertEqual(calls.read_text().splitlines(), ["getenv TYPESAFE_API_KEY"])
            self.assertFalse(state_dir.exists())

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
