#!/usr/bin/env bash
# Contract test for .agents/skills/agy/scripts/agy-run.py using a fake `agy acp`.
# It never starts the real agy CLI or touches the network.
set -euo pipefail

DOT_DIR="$(cd -P "$(dirname "$0")/.." && pwd)"
RUNNER="${DOT_DIR}/.agents/skills/agy/scripts/agy-run.py"
TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/agy-run-test.XXXXXX")"
trap 'rm -rf "$TEST_ROOT"' EXIT

timeout 300 python3 - "$RUNNER" "$TEST_ROOT" <<'PY'
import json
import os
import subprocess
import sys
from pathlib import Path

runner = sys.argv[1]
root = Path(sys.argv[2])
bin_dir = root / "bin"
bin_dir.mkdir()
cwd = root / "repo"
cwd.mkdir()
work = root / "jobs"
record = root / "fake-record.jsonl"

fake = bin_dir / "agy"
fake.write_text(r'''#!/usr/bin/env python3
import json, os, sys
record = os.environ["FAKE_AGY_RECORD"]
scenario = os.environ.get("FAKE_AGY_SCENARIO", "ok")

def out(message):
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()

def note(**values):
    with open(record, "a") as stream:
        stream.write(json.dumps(values) + "\n")

def update(update_kind, **fields):
    out({"jsonrpc": "2.0", "method": "session/update",
         "params": {"sessionId": "s1", "update": {"sessionUpdate": update_kind, **fields}}})

assert sys.argv[1:] == ["acp"], sys.argv
note(event="start", cwd=os.getcwd(), autosync_skip=os.environ.get("DOTFILES_AUTOSYNC_SKIP"))
config = {"model": "gemini-4-carbon", "thought_level": "medium", "mode": "default"}
for line in sys.stdin:
    message = json.loads(line)
    method = message.get("method")
    params = message.get("params", {})
    if method is None:
        note(event="client_response", result=message.get("result"))
        continue
    if method == "initialize":
        result = {"protocolVersion": 1, "agentInfo": {"name": "fake", "version": "0.0.1"}}
    elif method == "session/new":
        note(event="session_new", cwd=params.get("cwd"))
        result = {"sessionId": "sess-1"}
    elif method == "session/load":
        note(event="session_load", sessionId=params.get("sessionId"))
        update("agent_message_chunk", content={"type": "text", "text": "OLD-HISTORY"})
        result = {}
    elif method == "session/set_model":
        name, _, level = params["modelId"].rpartition("-")
        config.update(model=name, thought_level=level)
        result = {}
        out({"jsonrpc": "2.0", "id": message["id"], "result": result})
        update("config_option_update",
               configOptions=[{"id": k, "currentValue": v} for k, v in config.items()])
        continue
    elif method == "session/set_mode":
        config["mode"] = params["modeId"]
        out({"jsonrpc": "2.0", "id": message["id"], "result": {}})
        update("config_option_update",
               configOptions=[{"id": k, "currentValue": v} for k, v in config.items()])
        continue
    elif method == "session/prompt":
        note(event="prompt", text=params["prompt"][0]["text"])
        update("tool_call", toolCallId="t1", name="read_file", kind="read", status="in_progress")
        update("tool_call_update", toolCallId="t1", status="completed")
        if scenario == "die":
            sys.exit(1)
        if scenario == "refusal":
            out({"jsonrpc": "2.0", "id": message["id"], "result": {"stopReason": "refusal"}})
            continue
        if scenario == "permission":
            out({"jsonrpc": "2.0", "id": 900, "method": "session/request_permission",
                 "params": {"sessionId": "s1",
                            "toolCall": {"name": "run_command", "kind": "execute"},
                            "options": [{"optionId": "allow", "kind": "allow_once"},
                                        {"optionId": "deny", "kind": "reject_once"}]}})
            reply = json.loads(sys.stdin.readline())
            note(event="permission_reply", reply=reply.get("result"))
        else:
            update("agent_message_chunk", content={"type": "text", "text": "an"})
            update("agent_message_chunk", content={"type": "text", "text": "swer"})
        result = {"stopReason": "end_turn", "usage": {"totalTokens": 7}}
    else:
        out({"jsonrpc": "2.0", "id": message["id"], "error": {"code": -32601, "message": method}})
        continue
    out({"jsonrpc": "2.0", "id": message["id"], "result": result})
''')
fake.chmod(0o700)
prompt_file = root / "prompt.md"
prompt_file.write_text("question body\n")

def run(run_id, *extra, scenario="ok", path=None, mode="plan", model="gemini-4-carbon-high"):
    env = dict(os.environ)
    env.update(FAKE_AGY_RECORD=str(record), FAKE_AGY_SCENARIO=scenario,
               PATH=path if path is not None else f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
               XDG_STATE_HOME=str(root / "state"))
    proc = subprocess.run(
        [sys.executable, runner, "--prompt-file", str(prompt_file), "--cwd", str(cwd),
         "--model", model, "--mode", mode, "--work-dir", str(work), "--run-id", run_id, *extra],
        env=env, text=True, capture_output=True, timeout=60, cwd=str(cwd))
    lines = proc.stdout.strip().splitlines()
    assert len(lines) == 1, (proc.stdout, proc.stderr)
    return proc.returncode, json.loads(lines[0])

def records():
    return [json.loads(line) for line in record.read_text().splitlines()]

def check(name, condition, detail=""):
    if not condition:
        print(f"FAIL {name}: {detail}")
        sys.exit(1)
    print(f"PASS {name}")

# 1. new session completes with observed values and the agy process cwd.
code, s = run("one")
check("new session completes", code == 0 and s["wait_status"] == "completed"
      and s["done"] == {"path": s["done"]["path"], "created": True, "exit": 0}, s)
check("final response", s["final_response"]["body"] == "answer", s["final_response"])
check("observed config", s["OBSERVED_MODEL"] == "gemini-4-carbon"
      and s["OBSERVED_THOUGHT_LEVEL"] == "high" and s["OBSERVED_MODE"] == "plan"
      and s["MODEL_MATCH_STATUS"] == "match" and s["MODE_MATCH_STATUS"] == "match", s)
check("tool calls counted", s["run"]["tool_call_count"] == 1 and s["warnings"] == [], s)
start = [r for r in records() if r["event"] == "start"][-1]
check("process cwd and env", start["cwd"] == str(cwd) and start["autosync_skip"] == "1", start)
prompt_text = [r for r in records() if r["event"] == "prompt"][-1]["text"]
check("delegation prefix", prompt_text.startswith("【runner から委譲された実行者")
      and prompt_text.endswith("question body\n"), prompt_text[:80])
artifacts = [p.name for p in work.iterdir() if p.name.startswith("agy-one-")]
check("artifacts", len(artifacts) == 9, sorted(artifacts))

# 2. the same RUN_ID is refused before start.
code, s = run("one")
check("run id collision", code == 2 and s["wait_status"] == "invocation_error"
      and s["done"]["created"] is False, s)

# 3. permission requests are rejected and surfaced.
code, s = run("perm", scenario="permission", mode="auto", model="gemini-4-hydrogen-xhigh")
reply = [r for r in records() if r["event"] == "permission_reply"][-1]["reply"]
check("permission rejected", reply == {"outcome": {"outcome": "selected", "optionId": "deny"}}, reply)
check("permission surfaced", code == 0 and "permission_rejected" in s["warnings"]
      and "empty_final_response" in s["warnings"]
      and s["run"]["permission_rejected"] == [{"tool": "run_command", "kind": "execute"}], s)

# 4. session continuation loads the saved session and ignores replayed history.
session = root / "sessions" / "nested" / "thread"
code, s = run("s1", "--session-file", str(session))
check("session saved", code == 0 and oct(session.parent.stat().st_mode & 0o777) == "0o700" and session.read_text() == "sess-1\n"
      and Path(str(session) + ".meta").read_text() == f"CWD={cwd}\nMODE=plan\n", s)
code, s = run("s2", "--session-file", str(session))
loads = [r for r in records() if r["event"] == "session_load"]
check("session loaded", code == 0 and loads and loads[-1]["sessionId"] == "sess-1", s)
check("history excluded", s["final_response"]["body"] == "answer", s["final_response"])

# 5. a session recorded for another mode is refused.
code, s = run("s3", "--session-file", str(session), mode="auto")
check("session meta mismatch", code == 2 and s["wait_status"] == "invocation_error", s)

# 6. a missing agy CLI is an invocation error without DONE.
empty = root / "empty-bin"
empty.mkdir()
code, s = run("missing", path=str(empty))
check("agy missing", code == 5 and s["wait_status"] == "invocation_error"
      and s["done"]["created"] is False, s)
# 7. invalid arguments still return one JSON line.
proc = subprocess.run([sys.executable, runner, "--mode", "read-only"], text=True,
                      capture_output=True, timeout=60, cwd=str(cwd))
s = json.loads(proc.stdout.strip())
check("invalid arguments", proc.returncode == 2 and s["wait_status"] == "invocation_error"
      and s["done"]["created"] is False, proc.stdout)

# 8. agy dying mid-turn and a non end_turn stop reason are failures with DONE.
code, s = run("die", scenario="die")
check("agy exit is EXIT 4", code == 4 and s["wait_status"] == "completed"
      and s["done"]["exit"] == 4 and s["run"]["failure"], s)
code, s = run("refusal", scenario="refusal")
check("non end_turn is EXIT 3", code == 3 and s["stop_reason"] == "refusal"
      and s["done"]["exit"] == 3, s)
print("ALL PASS")
PY
