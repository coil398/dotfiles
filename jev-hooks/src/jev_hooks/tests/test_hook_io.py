"""Hook I/O, API failure codes, config, doctor, and log hygiene."""

from __future__ import annotations

import io
import json
import os
import socket
import stat
import sys
import tempfile
import threading
import unittest
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional
from urllib.request import ProxyHandler, Request, build_opener

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from jev_hooks import codex_hook, jev_client, logbook, policy  # noqa: E402
from jev_hooks.config import load_config, resolve_api_key  # noqa: E402
from jev_hooks.doctor import doctor  # noqa: E402
from jev_hooks.jev_client import ChoiceAnswer, JevResult  # noqa: E402
from jev_hooks.tests import rollout_fixture as fx  # noqa: E402
from jev_hooks.tests.test_state_and_limits import FakeJev, Harness, turn_lines  # noqa: E402


class _HTTPError(urllib.error.HTTPError):
    def __init__(self, code: int) -> None:
        super().__init__("https://api.typesafe.ai/v1/systemone", code, "err", hdrs=None, fp=io.BytesIO(b""))


class ConfigTests(unittest.TestCase):
    def test_file_then_env_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "cfg.json"
            cfg_path.write_text(json.dumps({"mode": "observe", "confidence_threshold": 0.8, "unknown": 1}))
            env = {
                "HOME": tmp,
                "JEV_HOOKS_CONFIG": str(cfg_path),
                "JEV_HOOKS_MODE": "off",
                "JEV_HOOKS_API_TIMEOUT_S": "2.5",
            }
            cfg = load_config(env)
            self.assertEqual(cfg.mode, "off")
            self.assertEqual(cfg.confidence_threshold, 0.8)
            self.assertEqual(cfg.api_timeout_s, 2.5)
            self.assertTrue(any("unknown" in w for w in cfg.warnings))

    def test_invalid_values_fall_back(self) -> None:
        env = {
            "HOME": "/tmp",
            "JEV_HOOKS_MODE": "maybe",
            "JEV_HOOKS_CONFIDENCE_THRESHOLD": "2",
            "JEV_HOOKS_API_TIMEOUT_S": "9",
            "JEV_HOOKS_TOTAL_TIMEOUT_S": "4",
            "JEV_HOOKS_MAX_CONTINUATIONS": "-1",
            "JEV_HOOKS_API_URL": "http://api.typesafe.ai/v1/systemone",
        }
        cfg = load_config(env)
        self.assertEqual(cfg.mode, "on")
        self.assertEqual(cfg.confidence_threshold, 0.6)
        self.assertLessEqual(cfg.api_timeout_s, cfg.total_timeout_s)
        self.assertEqual(cfg.max_continuations, 2)
        self.assertGreaterEqual(len(cfg.warnings), 3)
        self.assertEqual(cfg.api_url, "https://api.typesafe.ai/v1/systemone")
        self.assertTrue(any("api_url must use HTTPS" in warning for warning in cfg.warnings))

    def test_api_key_env_beats_secret_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".zsh_secret").write_text("export TYPESAFE_API_KEY=from-file\n")
            key, src = resolve_api_key({"HOME": tmp, "TYPESAFE_API_KEY": "from-env"})
            self.assertEqual((key, src), ("from-env", "env"))
            key, src = resolve_api_key({"HOME": tmp})
            self.assertEqual((key, src), (None, "missing"))


class ClientErrorTests(unittest.TestCase):
    def _ask(self, opener) -> None:
        jev_client.ask(
            api_url="https://api.typesafe.ai/v1/systemone",
            api_key="k",
            model="jev-latest",
            state="s",
            questions=policy.QUESTIONS,
            timeout_s=1.0,
            opener=opener,
        )

    def test_http_status_codes(self) -> None:
        cases = {401: "API_AUTH", 403: "API_AUTH", 429: "API_RATE_LIMIT", 500: "API_SERVER_ERROR", 529: "API_SERVER_ERROR", 400: "API_HTTP_ERROR"}
        for status, code in cases.items():
            with self.assertRaises(jev_client.JevError) as cm:
                self._ask(lambda req, timeout=None: (_ for _ in ()).throw(_HTTPError(status)))
            self.assertEqual(cm.exception.code, code, status)

    def test_timeout_and_network(self) -> None:
        def timeout(_req, timeout=None):
            raise socket.timeout("timed out")

        with self.assertRaises(jev_client.JevError) as cm:
            self._ask(timeout)
        self.assertEqual(cm.exception.code, "API_TIMEOUT")

        def urlerr(_req, timeout=None):
            raise urllib.error.URLError(socket.timeout("timed out"))

        with self.assertRaises(jev_client.JevError) as cm:
            self._ask(urlerr)
        self.assertEqual(cm.exception.code, "API_TIMEOUT")

        def other(_req, timeout=None):
            raise urllib.error.URLError("refused")

        with self.assertRaises(jev_client.JevError) as cm:
            self._ask(other)
        self.assertEqual(cm.exception.code, "API_NETWORK")

    def test_invalid_json_body(self) -> None:
        class Resp:
            def read(self, n: int = -1) -> bytes:
                return b"not-json"

            def __enter__(self) -> "Resp":
                return self

            def __exit__(self, *a: Any) -> None:
                return None

        with self.assertRaises(jev_client.JevError) as cm:
            self._ask(lambda req, timeout=None: Resp())
        self.assertEqual(cm.exception.code, "API_BAD_RESPONSE")

    def test_remote_http_api_url_is_rejected_before_open(self) -> None:
        called = False

        def unexpected_open(_req, timeout=None):
            nonlocal called
            called = True
            raise AssertionError("unsafe URL must not be opened")

        with self.assertRaises(jev_client.JevError) as cm:
            jev_client.ask(
                api_url="http://api.typesafe.ai/v1/systemone",
                api_key="test-only-key",
                model="jev-latest",
                state={},
                questions={},
                timeout_s=1.0,
                opener=unexpected_open,
            )
        self.assertEqual(cm.exception.code, "API_URL_UNSAFE")
        self.assertFalse(called)

    def test_redirect_does_not_forward_authorization_to_other_origin(self) -> None:
        origin_authorization = []
        redirected_authorization = []

        class RedirectHandler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                origin_authorization.append(self.headers.get("Authorization"))
                self.send_response(302)
                self.send_header("Location", self.server.redirect_to)
                self.end_headers()

            def log_message(self, *_args: Any) -> None:
                return

        class SinkHandler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                redirected_authorization.append(self.headers.get("Authorization"))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"{}")

            def log_message(self, *_args: Any) -> None:
                return

        sink = ThreadingHTTPServer(("127.0.0.1", 0), SinkHandler)
        redirector = ThreadingHTTPServer(("127.0.0.1", 0), RedirectHandler)
        redirector.redirect_to = f"http://127.0.0.1:{sink.server_port}/capture"
        threads = [
            threading.Thread(target=sink.serve_forever, daemon=True),
            threading.Thread(target=redirector.serve_forever, daemon=True),
        ]
        for thread in threads:
            thread.start()
        try:
            opener = build_opener(ProxyHandler({}), jev_client._NoRedirectHandler()).open
            with self.assertRaises(jev_client.JevError) as cm:
                jev_client.ask(
                    api_url=f"http://127.0.0.1:{redirector.server_port}/v1/systemone",
                    api_key="test-only-local-key",
                    model="jev-latest",
                    state={},
                    questions={},
                    timeout_s=1.0,
                    opener=opener,
                )
            self.assertEqual(cm.exception.code, "API_HTTP_ERROR")
            self.assertEqual(origin_authorization, ["Bearer test-only-local-key"])
            self.assertEqual(redirected_authorization, [])
        finally:
            for server in (redirector, sink):
                server.shutdown()
                server.server_close()
            for thread in threads:
                thread.join(timeout=1.0)

    def test_request_shape(self) -> None:
        seen: dict = {}

        class Resp:
            def read(self, n: int = -1) -> bytes:
                body = {
                    "model": "jev-latest",
                    "answers": {
                        qid: {
                            "type": "choice",
                            "choice": next(iter(q["criteria"])),
                            "probabilities": {k: (1.0 if i == 0 else 0.0) for i, k in enumerate(q["criteria"])},
                            "confidence": 1.0,
                        }
                        for qid, q in policy.QUESTIONS.items()
                    },
                    "usage": {"input_tokens": 3, "output_tokens": 1},
                }
                return json.dumps(body).encode()

            def __enter__(self) -> "Resp":
                return self

            def __exit__(self, *a: Any) -> None:
                return None

        def opener(req: Request, timeout: Optional[float] = None) -> Resp:
            seen["url"] = req.full_url
            seen["method"] = req.get_method()
            seen["auth"] = req.get_header("Authorization")
            seen["timeout"] = timeout
            seen["body"] = json.loads(req.data.decode())
            return Resp()

        result = jev_client.ask(
            api_url="https://api.typesafe.ai/v1/systemone",
            api_key="secret-key",
            model="jev-latest",
            state={"x": 1},
            questions=policy.QUESTIONS,
            timeout_s=2.5,
            opener=opener,
        )
        self.assertEqual(seen["method"], "POST")
        self.assertEqual(seen["auth"], "Bearer secret-key")
        self.assertEqual(seen["timeout"], 2.5)
        self.assertEqual(seen["body"]["model"], "jev-latest")
        self.assertEqual(set(seen["body"]["questions"]), set(policy.QUESTIONS))
        self.assertEqual(result.usage["input_tokens"], 3)


class HookIOTests(unittest.TestCase):
    def test_logbook_state_and_log_are_owner_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "state"
            state_dir.mkdir(mode=0o755)
            os.chmod(state_dir, 0o755)

            self.assertTrue(logbook.append(state_dir, {"verdict": "allow"}, 10_000))

            self.assertEqual(stat.S_IMODE(state_dir.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(logbook.log_path(state_dir).stat().st_mode), 0o600)

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.h = Harness(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_stdout_is_block_or_empty_object(self) -> None:
        h = self.h
        path = h.transcript("s", turn_lines("t1"))
        payload = h.payload("s", "t1", "plan only", active=False, transcript=path)
        out = io.StringIO()
        env = dict(h.env)
        env["JEV_HOOKS_STATE_DIR"] = str(h.cfg.state_path())
        env["JEV_HOOKS_MODE"] = "on"
        # evaluate path via run_hook uses real ask; inject by calling evaluate then dump.
        outcome = h.run(payload)
        self.assertEqual(outcome.output, {"decision": "block", "reason": policy.REASON_CONTINUE_WORK})
        dumped = json.dumps(outcome.output, ensure_ascii=False)
        self.assertNotIn("\n", dumped)
        self.assertTrue(dumped.startswith("{"))

    def test_invalid_stdin_is_empty_object(self) -> None:
        env = {"HOME": self._tmp.name, "JEV_HOOKS_MODE": "off", "JEV_HOOKS_STATE_DIR": str(Path(self._tmp.name) / "st")}
        out = io.StringIO()
        rc = codex_hook.run_hook(io.StringIO("not-json"), out, environ=env)
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out.getvalue()), {})

    def test_api_error_fail_open_and_logged(self) -> None:
        h = self.h
        h.transcript("s", turn_lines("t1"))

        def boom(**kw):
            raise jev_client.JevError("API_RATE_LIMIT", "http 429")

        o = codex_hook.evaluate(h.payload("s", "t1", "a", active=False), h.cfg, environ=h.env, ask_fn=boom)
        self.assertEqual(o.output, {})
        self.assertEqual(o.record["reason_code"], "API_RATE_LIMIT")

    def test_log_omits_conversation_and_secrets(self) -> None:
        h = self.h
        fake_key = "ts_live_" + "abcdefghijklmnop"
        h.transcript("s", turn_lines("t1", request=f"implement with TYPESAFE_API_KEY={fake_key}"))
        o = h.run(h.payload("s", "t1", "I will plan it", active=False))
        blob = json.dumps(o.record, ensure_ascii=False)
        self.assertNotIn("implement with", blob)
        self.assertNotIn(fake_key, blob)
        self.assertNotIn("jev_state", o.record)
        self.assertIn("verdict", o.record)
        self.assertIn("answers", o.record)

    def test_run_hook_writes_log_and_json(self) -> None:
        h = self.h
        path = h.transcript("s", turn_lines("t1"))
        payload = h.payload("s", "t1", "plan", active=False, transcript=path)
        env = {
            "HOME": str(h.tmp),
            "TYPESAFE_API_KEY": "k",
            "JEV_HOOKS_STATE_DIR": str(h.cfg.state_path()),
            "JEV_HOOKS_MODE": "observe",
        }
        # observe + missing real API would skip; stub by calling evaluate in observe.
        from dataclasses import replace

        o = codex_hook.evaluate(payload, replace(h.cfg, mode="observe"), environ=h.env, ask_fn=h.jev)
        logbook.append(h.cfg.state_path(), o.record, 10000)
        rows = logbook.tail(h.cfg.state_path(), 5)
        self.assertEqual(rows[-1]["action"], "observe")
        self.assertEqual(rows[-1]["verdict"], policy.CONTINUE_WORK)

    def test_main_help_and_doctor(self) -> None:
        out = io.StringIO()
        self.assertEqual(doctor(out), 0)
        text = out.getvalue()
        self.assertIn("jev-hooks", text)
        self.assertIn("api key", text)
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            rc = codex_hook.main(["--help"])
        finally:
            sys.stdout = old
        self.assertEqual(rc, 0)
        self.assertIn("--doctor", buf.getvalue())



class ActiveRuntimeTests(unittest.TestCase):
    def test_custom_home_installs_shared_hook_and_is_idempotent(self):
        import os
        import shlex
        import stat
        import tomllib
        from jev_hooks.trust import hook_hash, install_codex_hook

        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "other codex"
            home.mkdir()
            source = Path(tmp) / "source.toml"
            source.write_text(
                '[[hooks.Stop]]\n'
                '[[hooks.Stop.hooks]]\n'
                'type = "command"\n'
                'command = "sh /managed/jev-hooks/hook.sh codex"\n'
                'timeout = 10\n'
                'statusMessage = "Checking requested deliverables"\n'
            )
            config_target = home / "private config.toml"
            config_target.write_text('model = "user-model"\n')
            os.chmod(config_target, 0o600)
            (home / "config.toml").symlink_to(config_target.name)
            hooks_target = home / "private hooks.json"
            original = {
                "hooks": {
                    "PostToolUse": [{"hooks": [{"type": "command", "command": "existing"}]}],
                    "Stop": [
                        {"hooks": [{"type": "command", "command": "other-stop"}]},
                        {"hooks": [{"type": "command", "command": "sh /old/jev-hooks/hook.sh codex"}]},
                    ],
                }
            }
            hooks_target.write_text(json.dumps(original))
            os.chmod(hooks_target, 0o600)
            (home / "hooks.json").symlink_to(hooks_target.name)

            self.assertTrue(install_codex_hook(home, source))
            self.assertTrue((home / "config.toml").is_symlink())
            self.assertTrue((home / "hooks.json").is_symlink())
            self.assertEqual(stat.S_IMODE(config_target.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(hooks_target.stat().st_mode), 0o600)
            self.assertEqual(len(list(home.glob("private config.toml.backup-*"))), 1)
            self.assertEqual(len(list(home.glob("private hooks.json.backup-*"))), 1)
            data = json.loads((home / "hooks.json").read_text())
            self.assertEqual(data["hooks"]["PostToolUse"], original["hooks"]["PostToolUse"])
            self.assertEqual(data["hooks"]["Stop"][0], original["hooks"]["Stop"][0])
            installed = data["hooks"]["Stop"][1]["hooks"][0]
            installed_command = (
                "env CODEX_HOME=" + shlex.quote(str(home)) + " sh /managed/jev-hooks/hook.sh codex"
            )
            self.assertEqual(installed["command"], installed_command)

            config = tomllib.loads((home / "config.toml").read_text())
            self.assertEqual(config["model"], "user-model")
            key = f"{home / 'hooks.json'}:stop:1:0"
            self.assertEqual(
                config["hooks"]["state"][key]["trusted_hash"],
                hook_hash("stop", installed_command, timeout=10, status_message="Checking requested deliverables"),
            )
            self.assertFalse(install_codex_hook(home, source))

    def test_inline_toml_hook_is_updated_without_hooks_json_duplicate(self):
        import tomllib
        from jev_hooks.trust import hook_hash, install_codex_hook

        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "other-codex"
            home.mkdir()
            source = Path(tmp) / "source.toml"
            source.write_text(
                '[[hooks.Stop]]\n'
                '[[hooks.Stop.hooks]]\n'
                'type = "command"\n'
                'command = "sh /managed/jev-hooks/hook.sh codex"\n'
                'timeout = 10\n'
                'statusMessage = "Checking requested deliverables"\n'
            )
            target = home / "config.toml"
            target.write_text(
                'model = "user-model"\n'
                '[[hooks.Stop]]\n'
                '[[hooks.Stop.hooks]]\n'
                'type = "command"\n'
                'command = "sh /old/jev-hooks/hook.sh codex"\n'
                'timeout = 6\n'
                '[[hooks.Stop]]\n'
                'matcher = "Bash"\n'
                '[[hooks.Stop.hooks]]\n'
                'type = "command"\n'
                'command = "python3 /user/policy.py"\n'
                '[[hooks.Stop.hooks]]\n'
                'type = "command"\n'
                'command = "sh /old/jev-hooks/hook.sh codex"\n'
                'timeout = 6\n'
            )

            self.assertTrue(install_codex_hook(home, source))
            self.assertFalse((home / "hooks.json").exists())
            config = tomllib.loads(target.read_text())
            groups = config["hooks"]["Stop"]
            managed = [
                (index, handler_index, group, handler)
                for index, group in enumerate(groups)
                for handler_index, handler in enumerate(group["hooks"])
                if "jev-hooks/hook.sh" in handler.get("command", "")
            ]
            self.assertEqual(len(managed), 1)
            group_index, handler_index, group, handler = managed[0]
            self.assertEqual((group_index, handler_index), (0, 1))
            self.assertEqual(group["matcher"], "Bash")
            self.assertEqual(group["hooks"][0]["command"], "python3 /user/policy.py")
            command = "sh /managed/jev-hooks/hook.sh codex"
            self.assertEqual(handler["command"], command)
            self.assertEqual(handler["timeout"], 10)
            self.assertEqual(handler["statusMessage"], "Checking requested deliverables")
            state_key = f"{target}:stop:0:1"
            self.assertEqual(
                config["hooks"]["state"][state_key]["trusted_hash"],
                hook_hash(
                    "stop",
                    command,
                    matcher="Bash",
                    timeout=10,
                    status_message="Checking requested deliverables",
                ),
            )
            self.assertFalse(install_codex_hook(home, source))

    def test_custom_home_cli_uses_repository_config(self):
        from contextlib import redirect_stdout
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            with patch("jev_hooks.trust.install_codex_hook", return_value=True) as installer:
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(codex_hook.main(["--install-codex-hook", tmp]), 0)
            args, _kwargs = installer.call_args
            self.assertEqual(args[0], Path(tmp))
            self.assertEqual(
                args[1],
                Path(codex_hook.__file__).resolve().parents[3] / ".codex/config.toml",
            )

    def test_side_question_keeps_previous_task_in_compact_payload(self):
        from jev_hooks.transcript import TurnContext, UserMessage

        ctx = TurnContext(turn_id="t", found_turn_start=True)
        ctx.user_messages = [
            UserMessage("hookを修正して有効化して", False),
            UserMessage("入力課金なので無駄に送信しないで", False),
            UserMessage("送信内容は機械的に決まるんだよな？", True),
        ]
        data = policy.build_state(ctx, "はい、機械的です。", 0)
        self.assertEqual(len(data["conversation"]["user_messages_oldest_first"]), 3)
        self.assertIn("有効化", data["conversation"]["user_messages_oldest_first"][0]["text"])

if __name__ == "__main__":
    unittest.main()
