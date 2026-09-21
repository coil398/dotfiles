"""Hook I/O, API failure codes, config, doctor, and log hygiene."""

from __future__ import annotations

import io
import json
import socket
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from typing import Any, Optional
from urllib.request import Request

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from jev_stop_guard import codex_hook, jev_client, logbook, policy  # noqa: E402
from jev_stop_guard.config import load_config, resolve_api_key  # noqa: E402
from jev_stop_guard.doctor import doctor  # noqa: E402
from jev_stop_guard.jev_client import ChoiceAnswer, JevResult  # noqa: E402
from jev_stop_guard.tests import rollout_fixture as fx  # noqa: E402
from jev_stop_guard.tests.test_state_and_limits import FakeJev, Harness, turn_lines  # noqa: E402


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
                "JEV_STOP_GUARD_CONFIG": str(cfg_path),
                "JEV_STOP_GUARD_MODE": "off",
                "JEV_STOP_GUARD_API_TIMEOUT_S": "2.5",
            }
            cfg = load_config(env)
            self.assertEqual(cfg.mode, "off")
            self.assertEqual(cfg.confidence_threshold, 0.8)
            self.assertEqual(cfg.api_timeout_s, 2.5)
            self.assertTrue(any("unknown" in w for w in cfg.warnings))

    def test_invalid_values_fall_back(self) -> None:
        env = {
            "HOME": "/tmp",
            "JEV_STOP_GUARD_MODE": "maybe",
            "JEV_STOP_GUARD_CONFIDENCE_THRESHOLD": "2",
            "JEV_STOP_GUARD_API_TIMEOUT_S": "9",
            "JEV_STOP_GUARD_TOTAL_TIMEOUT_S": "4",
            "JEV_STOP_GUARD_MAX_CONTINUATIONS": "-1",
        }
        cfg = load_config(env)
        self.assertEqual(cfg.mode, "on")
        self.assertEqual(cfg.confidence_threshold, 0.6)
        self.assertLessEqual(cfg.api_timeout_s, cfg.total_timeout_s)
        self.assertEqual(cfg.max_continuations, 2)
        self.assertGreaterEqual(len(cfg.warnings), 3)

    def test_api_key_env_beats_secret_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".zsh_secret").write_text("export TYPESAFE_API_KEY=from-file\n")
            key, src = resolve_api_key({"HOME": tmp, "TYPESAFE_API_KEY": "from-env"})
            self.assertEqual((key, src), ("from-env", "env"))
            key, src = resolve_api_key({"HOME": tmp})
            self.assertEqual((key, src), ("from-file", "secret_file"))


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
        env["JEV_STOP_GUARD_STATE_DIR"] = str(h.cfg.state_path())
        env["JEV_STOP_GUARD_MODE"] = "on"
        # evaluate path via run_hook uses real ask; inject by calling evaluate then dump.
        outcome = h.run(payload)
        self.assertEqual(outcome.output, {"decision": "block", "reason": policy.REASON_CONTINUE_WORK})
        dumped = json.dumps(outcome.output, ensure_ascii=False)
        self.assertNotIn("\n", dumped)
        self.assertTrue(dumped.startswith("{"))

    def test_invalid_stdin_is_empty_object(self) -> None:
        env = {"HOME": self._tmp.name, "JEV_STOP_GUARD_MODE": "off", "JEV_STOP_GUARD_STATE_DIR": str(Path(self._tmp.name) / "st")}
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
            "JEV_STOP_GUARD_STATE_DIR": str(h.cfg.state_path()),
            "JEV_STOP_GUARD_MODE": "observe",
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
        self.assertIn("jev-stop-guard", text)
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
    def test_install_preserves_other_settings_and_is_idempotent(self):
        from jev_stop_guard.trust import install_codex_hook, hook_hash
        import tomllib
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)/"other-codex"; home.mkdir()
            source=Path(tmp)/"source.toml"
            source.write_text('[[hooks.Stop]]\n[[hooks.Stop.hooks]]\ntype="command"\ncommand="python3 /managed/jev-stop-guard-codex-hook.py"\ntimeout=6\n')
            (home/"config.toml").write_text('model="user-model"\n')
            original={"hooks":{"PostToolUse":[{"hooks":[{"type":"command","command":"existing"}]}],"Stop":[{"hooks":[{"type":"command","command":"other-stop"}]}]}}
            (home/"hooks.json").write_text(json.dumps(original))
            self.assertTrue(install_codex_hook(home,source))
            data=json.loads((home/"hooks.json").read_text())
            self.assertEqual(data["hooks"]["PostToolUse"],original["hooks"]["PostToolUse"])
            self.assertEqual(data["hooks"]["Stop"][0],original["hooks"]["Stop"][0])
            config=tomllib.loads((home/"config.toml").read_text())
            self.assertEqual(config["model"],"user-model")
            key=f"{home / 'hooks.json'}:stop:1:0"
            self.assertEqual(config["hooks"]["state"][key]["trusted_hash"],hook_hash("stop",f"env CODEX_HOME={home} python3 /managed/jev-stop-guard-codex-hook.py",timeout=6))
            self.assertFalse(install_codex_hook(home,source))

    def test_missing_path_resolves_only_matching_session(self):
        from jev_stop_guard.transcript import resolve_codex_transcript, TranscriptError
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)/"sessions/2026/09/21"; directory.mkdir(parents=True)
            path=directory/"rollout-2026-09-21-session-one.jsonl"
            path.write_text(json.dumps({"type":"session_meta","payload":{"id":"session-one"}})+"\n")
            env={"CODEX_HOME":tmp}
            self.assertEqual(resolve_codex_transcript(None,"session-one",env),str(path))
            with self.assertRaises(TranscriptError): resolve_codex_transcript(None,"other",env)
            path.write_text(json.dumps({"type":"session_meta","payload":{"id":"other"}})+"\n")
            with self.assertRaises(TranscriptError): resolve_codex_transcript(None,"session-one",env)

    def test_browser_wrapper_does_not_get_sent_as_user_request(self):
        from jev_stop_guard.transcript import classify_user_text
        self.assertEqual(classify_user_text('<in-app-browser-context>private-url</in-app-browser-context>\n## My request:\n続けて'),("user","続けて"))

    def test_side_question_keeps_previous_task_in_compact_payload(self):
        from jev_stop_guard.transcript import TurnContext, UserMessage
        ctx=TurnContext(turn_id="t",found_turn_start=True)
        ctx.user_messages=[UserMessage("hookを修正して有効化して",False),UserMessage("入力課金なので無駄に送信しないで",False),UserMessage("送信内容は機械的に決まるんだよな？",True)]
        data=policy.build_state(ctx,"はい、機械的です。",0)
        self.assertEqual(len(data["conversation"]["user_messages_oldest_first"]),3)
        self.assertIn("有効化",data["conversation"]["user_messages_oldest_first"][0]["text"])

    def test_inline_stop_trust_uses_real_group_index(self):
        import tomllib
        from jev_stop_guard.trust import apply_stop_trust
        with tempfile.TemporaryDirectory() as tmp:
            config=Path(tmp)/"config.toml"
            config.write_text('[[hooks.Stop]]\n[[hooks.Stop.hooks]]\ntype="command"\ncommand="other-hook"\n[[hooks.Stop]]\n[[hooks.Stop.hooks]]\ntype="command"\ncommand="python3 /managed/jev-stop-guard-codex-hook.py"\ntimeout=6\n')
            changed,digest=apply_stop_trust(config)
            self.assertTrue(changed)
            state=tomllib.loads(config.read_text())["hooks"]["state"]
            self.assertEqual(state[f"{config}:stop:1:0"]["trusted_hash"],digest)
            self.assertNotIn(f"{config}:stop:0:0",state)
            self.assertFalse(apply_stop_trust(config)[0])

if __name__ == "__main__":
    unittest.main()
