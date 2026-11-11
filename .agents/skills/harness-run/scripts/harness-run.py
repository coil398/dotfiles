#!/usr/bin/env python3
"""Run one non-interactive job on Pi, Oh my Pi, OpenCode or DeepSeek Harness (dsh).

Blocking execution with a timeout. One JSON summary line goes to stdout, logs go
to stderr and to harness-<RUN_ID>-run.log. No automatic retry, model change or
permission escalation. See references/harnesses.md for the per-harness contract.
"""

import argparse
import json
import logging
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
from urllib.parse import quote

logger = logging.getLogger("harness_run")

EXIT_BY_STATUS = {"completed": 0, "failed": 1, "invocation_error": 2,
                  "auth_not_ready": 3, "timeout": 124}
RUN_ID_RE = re.compile(r"[A-Za-z0-9._-]+\Z")
MODEL_RE = re.compile(r"[A-Za-z0-9._-]+/[A-Za-z0-9._:/-]+\Z")
EFFORTS = ("low", "medium", "high", "xhigh", "max")
HARNESSES = ("pi", "omp", "opencode", "dsh")
SUMMARY_KEYS = ("harness", "model", "effort", "run_id", "cwd", "status", "exit",
                "final_text_path", "events_path", "stderr_path", "usage",
                "duration_s", "error")
PROMPT_PREFIX = """【harness-run から委譲された担当としての実行条件】
この依頼では、あなた自身が作業を完了してください。
- 別のAI CLI・サブエージェント・別の担当を起動しないでください。
- git commit / push、外部への送信、依頼範囲外の変更をしないでください。
- 完了条件に含まれるテスト・ビルドなどは実行して結果を確認し、結果を最終応答に書いてください。
- 大きな出力は全体を読まず、grep・head などで必要な行だけ確認してください。

--- 依頼 ---
"""
PI_TOOLS_RO = "read,grep,find,ls"
PI_TOOLS_RW = "read,bash,edit,write,grep,find,ls"
OMP_TOOLS_RO = "read,grep,glob,find"
OMP_TOOLS_RW = "read,bash,edit,write,grep,glob,find"
OMP_OVERLAY = ("disabledProviders: [claude, claude-plugins, codex, cursor, "
               "gemini, opencode, windsurf, github]\n")
OPENCODE_RO_PERMISSION = {
    "*": "deny",
    "read": {"*": "allow", "*.env": "deny", "*.env.*": "deny", "*.env.example": "allow"},
    "grep": "allow", "glob": "allow", "list": "allow"}
EFFORT_RANK = {"low": 0, "medium": 1, "high": 2, "xhigh": 3, "max": 4}
DSH_KEY_ENV = {"opencode-go": "OPENCODE_API_KEY"}
DSH_DEEPSEEK_EFFORT = {"low": "low", "medium": "high", "high": "high",
                       "xhigh": "max", "max": "max"}


class InvocationError(Exception):
    pass


class Plan:
    def __init__(self, argv, cwd):
        self.argv = argv
        self.cwd = cwd
        self.env_set = {}
        self.env_unset = ["OPENAI_API_KEY"]
        self.use_stdin = False
        self.files = {}
        self.dirs = []
        self.auth_argv = None
        self.auth_env_missing = None
        self.effort_applied = None


class Ctx:
    def __init__(self, args, work_dir):
        self.harness = args.harness
        self.provider, self.model_id = args.model.split("/", 1)
        self.model = args.model
        self.effort = args.effort
        self.read_only = args.read_only
        self.minimal = args.minimal_context
        self.cwd = Path(args.cwd)
        self.work_dir = work_dir
        self.run_id = args.run_id
        self.dsh_patches = [str(Path(p).resolve()) for p in args.dsh_patch]
        prefix = f"harness-{args.run_id}-"
        self.paths = {name: work_dir / f"{prefix}{name}" for name in
                      ("prompt.md", "events.jsonl", "err.txt", "last.md",
                       "summary.json", "run.log")}
        self.aux = lambda name: work_dir / f"{prefix}{name}"


def build_pi(c):
    tools = PI_TOOLS_RO if c.read_only else PI_TOOLS_RW
    argv = ["pi", "--provider", c.provider, "--model", c.model_id,
            "--thinking", c.effort, "--session-dir", str(c.aux("sessions")),
            "--tools", tools, "--mode", "json"]
    if c.minimal:
        argv += ["-nc", "-ns", "--no-mcp", "-ne", "-na"]
    argv += [f"@{c.paths['prompt.md']}", "Follow the attached task file."]
    plan = Plan(argv, c.cwd)
    plan.env_set["PI_SKIP_VERSION_CHECK"] = "1"
    plan.dirs.append(c.aux("sessions"))
    plan.auth_argv = ["pi", "auth", "check", "--provider", c.provider, "--json"]
    return plan


def build_omp(c):
    tools = OMP_TOOLS_RO if c.read_only else OMP_TOOLS_RW
    argv = ["omp", "-p", "--mode", "json", "--no-session", "--model", c.model,
            "--thinking", c.effort, "--no-title", "--no-lsp", "--tools", tools,
            "--cwd", str(c.cwd)]
    plan = Plan(argv, c.cwd)
    if c.minimal:
        overlay = c.aux("omp-overlay.yml")
        argv += ["--no-skills", "--no-rules", "--no-context-files",
                 "--no-extensions", "--config", str(overlay)]
        plan.files[overlay] = OMP_OVERLAY
    argv.append(f"@{c.paths['prompt.md']}")
    plan.use_stdin = False
    plan.auth_argv = ["omp", "token", c.provider]
    return plan


def build_opencode(c):
    agent = f"harness-ro-{c.run_id}"
    if c.provider == "openai":
        _require_opencode_openai_oauth()
    argv = ["opencode", "run", "--pure", "--dir", str(c.cwd), "--title",
            f"harness-{c.run_id}", "--agent", agent if c.read_only else "build",
            "-m", c.model, "--variant", c.effort, "--format", "json"]
    plan = Plan(argv, c.cwd)
    plan.use_stdin = True
    plan.env_set.update({"OPENCODE_DISABLE_AUTOUPDATE": "1", "OPENCODE_DISABLE_SHARE": "1"})
    if c.read_only:
        plan.env_set["OPENCODE_CONFIG_CONTENT"] = json.dumps(
            {"agent": {agent: {"mode": "primary", "permission": OPENCODE_RO_PERMISSION}}})
        # project config can redefine permissions and re-enable bash/edit
        plan.env_set["OPENCODE_DISABLE_PROJECT_CONFIG"] = "1"
    if c.minimal or c.read_only:
        xdg = c.aux("xdg") / "config"
        plan.dirs.append(xdg)
        plan.env_set["XDG_CONFIG_HOME"] = str(xdg)
    if c.minimal:
        plan.env_set.update({"OPENCODE_DISABLE_PROJECT_CONFIG": "1",
                             "OPENCODE_DISABLE_CLAUDE_CODE": "1",
                             "OPENCODE_DISABLE_EXTERNAL_SKILLS": "1"})
    return plan


def _require_opencode_openai_oauth():
    """provider openai on OpenCode is billed per use unless its credential is OAuth."""
    data_home = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    try:
        entry = json.loads((Path(data_home) / "opencode" / "auth.json").read_text(
            encoding="utf-8")).get("openai")
    except (OSError, ValueError, AttributeError):
        entry = None
    kind = entry.get("type") if isinstance(entry, dict) else None
    if kind != "oauth":
        raise InvocationError("opencode provider openai needs an OAuth credential "
                              f"(found type={kind}); an API key would be billed per use")


def declared_efforts(patches, model_id):
    """Effort levels a --dsh-patch declares under reasoningEfforts for model_id."""
    found = None
    for path in patches:
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            raise InvocationError(f"cannot read dsh patch {path}: {exc}")
        entry = re.search(r"-\s*id:\s*" + re.escape(model_id) + r"\s*\n(.*?)(?=\n\s*-\s*id:|\Z)",
                          text, re.S)
        block = entry and re.search(r"reasoningEfforts:\s*\n((?:[ \t]+[A-Za-z]+:[^\n]*\n?)+)",
                                    entry.group(1))
        if block:
            found = set(re.findall(r"^\s+([A-Za-z]+):", block.group(1), re.M))
    return found


def fit_effort(requested, declared):
    ranks = {e: EFFORT_RANK[e] for e in declared if e in EFFORT_RANK}
    if not ranks:
        return requested
    below = [e for e, r in ranks.items() if r <= EFFORT_RANK[requested]]
    return max(below, key=ranks.get) if below else min(ranks, key=ranks.get)


def _git_common_dir(cwd):
    try:
        out = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--path-format=absolute",
                              "--git-common-dir"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    path = out.stdout.strip()
    if out.returncode != 0 or not path or Path(path) == cwd / ".git":
        return None
    return path


def build_dsh(c):
    if c.provider == "openai-codex":
        raise InvocationError("dsh cannot sign in to openai-codex (no CLI sign-in path); "
                              "use pi, omp or opencode for Codex subscription models")
    effort = c.effort
    if "deepseek" in c.model_id:
        effort = DSH_DEEPSEEK_EFFORT[c.effort]
    declared = declared_efforts(c.dsh_patches, c.model_id)
    if declared:
        effort = fit_effort(effort, declared)
    patches = list(c.dsh_patches)
    plan = Plan([], c.cwd)
    if not patches:
        if c.provider not in DSH_KEY_ENV:
            raise InvocationError(f"provider {c.provider} is not in the pi-ai catalog route "
                                  "list; pass --dsh-patch with a providers overlay")
        routes = c.aux("dsh-routes.yml")
        plan.files[routes] = ("- id: llm-pi-ai\n  config:\n    providers:\n"
                              f"      {c.provider}:\n        apiKeyEnv: {DSH_KEY_ENV[c.provider]}\n")
        patches.append(str(routes))
    selection = c.aux("dsh-model.yml")
    plan.files[selection] = (
        "- id: agent-default-model\n  config:\n"
        f"    provider: {json.dumps(c.provider)}\n    model: {json.dumps(c.model_id)}\n"
        f"    reasoningEffort: {effort}\n"
        "- id: session-telemetry-otel\n  config:\n    mode: DISABLED\n")
    patches.append(str(selection))
    argv = ["npx", "-y", "@deepseek-ai/dsh", "--profile", "headless"]
    for p in patches:
        argv += ["--patch", p]
    argv += ["--permission-mode", "read-only" if c.read_only else "workspace-write",
             "--approval-policy", "never"]
    if not c.read_only:
        common = _git_common_dir(c.cwd)
        if common:
            argv += ["--add-dir", common]
    argv += ["--json", "-"]
    plan.argv = argv
    plan.use_stdin = True
    home = c.aux("dsh") / "home"
    plan.dirs.append(home)
    plan.env_set.update({"DSH_HOME": str(home), "DSH_TELEMETRY_MODE": "DISABLED"})
    if c.minimal:
        agents = c.aux("dsh") / "agents"
        plan.dirs.append(agents)
        plan.env_set["DSH_AGENTS_HOME"] = str(agents)
    key_env = DSH_KEY_ENV.get(c.provider)
    if len(c.dsh_patches) > 0:
        found = set()
        for p in c.dsh_patches:
            try:
                found.update(re.findall(r"apiKeyEnv:\s*([A-Za-z_][A-Za-z0-9_]*)",
                                        Path(p).read_text(encoding="utf-8")))
            except OSError as exc:
                raise InvocationError(f"cannot read dsh patch {p}: {exc}")
        key_env = next(iter(found)) if len(found) == 1 else key_env
    plan.auth_env_missing = key_env
    plan.effort_applied = effort
    return plan


BUILDERS = {"pi": build_pi, "omp": build_omp, "opencode": build_opencode, "dsh": build_dsh}


def read_events(path):
    events = []
    try:
        data = Path(path).read_bytes()
    except OSError:
        return events
    for raw in data.split(b"\n"):
        if not raw.strip():
            continue
        try:
            obj = json.loads(raw.decode("utf-8", errors="replace"))
        except ValueError:
            continue
        if isinstance(obj, dict):
            events.append(obj)
    return events


def _new_usage():
    return {"requests": 0, "input_uncached": 0, "cache_read": 0, "cache_write": 0,
            "output": 0, "reasoning": 0, "total_input": 0}


def _num(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else 0


def _finish_usage(u):
    u["total_input"] = u["input_uncached"] + u["cache_read"] + u["cache_write"]
    return u


def parse_pi_like(events):
    usage, last = _new_usage(), None
    for ev in events:
        if ev.get("type") != "message_end":
            continue
        msg = ev.get("message")
        if not isinstance(msg, dict) or msg.get("role") != "assistant":
            continue
        last = msg
        u = msg.get("usage")
        if isinstance(u, dict):
            usage["requests"] += 1
            usage["input_uncached"] += _num(u.get("input"))
            usage["cache_read"] += _num(u.get("cacheRead"))
            usage["cache_write"] += _num(u.get("cacheWrite"))
            usage["output"] += _num(u.get("output"))
            usage["reasoning"] += _num(u.get("reasoningTokens"))
    res = {"usage": _finish_usage(usage), "text": "", "ok": False, "error": None,
           "auth_error": False}
    if last is None:
        res["error"] = "no assistant message in events"
        return res
    parts = last.get("content") if isinstance(last.get("content"), list) else []
    res["text"] = "".join(p.get("text", "") for p in parts
                          if isinstance(p, dict) and p.get("type") == "text")
    if last.get("stopReason") == "stop":
        res["ok"] = True
    else:
        res["error"] = last.get("errorMessage") or f"stopReason={last.get('stopReason')}"
    return res


def parse_opencode(events):
    usage = _new_usage()
    res = {"usage": usage, "text": "", "ok": False, "error": None, "auth_error": False}
    stopped, last_msg, texts = False, None, []
    for ev in events:
        part = ev.get("part") if isinstance(ev.get("part"), dict) else {}
        if ev.get("type") == "step_finish":
            tokens = part.get("tokens") if isinstance(part.get("tokens"), dict) else {}
            cache = tokens.get("cache") if isinstance(tokens.get("cache"), dict) else {}
            usage["requests"] += 1
            usage["input_uncached"] += _num(tokens.get("input"))
            usage["cache_read"] += _num(cache.get("read"))
            usage["cache_write"] += _num(cache.get("write"))
            usage["output"] += _num(tokens.get("output")) + _num(tokens.get("reasoning"))
            usage["reasoning"] += _num(tokens.get("reasoning"))
            stopped = part.get("reason") == "stop"
        elif ev.get("type") == "text":
            texts.append((part.get("messageID"), part.get("text", "")))
        elif ev.get("type") == "error":
            err = ev.get("error") if isinstance(ev.get("error"), dict) else {}
            data = err.get("data") if isinstance(err.get("data"), dict) else {}
            res["error"] = f"{err.get('name')}: {data.get('message')}"
            body = str(data.get("responseBody"))
            if "Token refresh failed" in str(data.get("message")) or data.get("statusCode") == 401 \
                    or "authentication_error" in body or "api_key_expired" in body:
                res["auth_error"] = True
    if texts:
        last_msg = texts[-1][0]
        res["text"] = "".join(t for m, t in texts if m == last_msg)
    _finish_usage(usage)
    if res["error"] is None and stopped:
        res["ok"] = True
    elif res["error"] is None:
        res["error"] = "no step_finish with reason=stop"
    return res


def parse_dsh(events):
    usage = _new_usage()
    res = {"usage": usage, "text": "", "ok": False, "error": None, "auth_error": False}
    final = None
    for ev in events:
        if ev.get("type") == "status" and ev.get("phase") == "step_end" \
                and isinstance(ev.get("usage"), dict):
            u = ev["usage"]
            usage["requests"] += 1
            usage["input_uncached"] += _num(u.get("inputTokens"))
            usage["cache_read"] += _num(u.get("cacheReadTokens"))
            usage["cache_write"] += _num(u.get("cacheWriteTokens"))
            usage["output"] += _num(u.get("outputTokens"))
            usage["reasoning"] += _num(u.get("reasoningTokens"))
        elif ev.get("type") == "final":
            final = ev
        elif ev.get("type") == "error" and res["error"] is None:
            res["error"] = str(ev.get("message"))
    _finish_usage(usage)
    if final is None:
        res["error"] = res["error"] or "no final event"
        return res
    res["text"] = final.get("text") or ""
    reason = final.get("reason") if isinstance(final.get("reason"), dict) else {}
    if reason.get("kind") == "completed":
        res["ok"] = True
    else:
        err = reason.get("error") if isinstance(reason.get("error"), dict) else {}
        res["error"] = f"{err.get('code') or reason.get('kind')}: {err.get('message') or ''}".strip()
        res["auth_error"] = err.get("code") in ("MISSING_CREDENTIAL", "AUTH")
    return res


PARSERS = {"pi": parse_pi_like, "omp": parse_pi_like, "opencode": parse_opencode,
           "dsh": parse_dsh}
STDERR_AUTH_MARKERS = ("No API key found", "No active credential")


def base_env(plan):
    env = dict(os.environ)
    for key in plan.env_unset:
        env.pop(key, None)
    env.update(plan.env_set)
    return env


def preflight_auth(plan, harness):
    """Return None when ready, otherwise a reason string (no secrets)."""
    if plan.auth_env_missing and not os.environ.get(plan.auth_env_missing):
        return f"environment variable {plan.auth_env_missing} is not set"
    if plan.auth_argv is None:
        return None
    if shutil.which(plan.auth_argv[0]) is None:
        return f"{plan.auth_argv[0]} not found in PATH"
    try:
        # omp token prints the credential: never capture it
        out = subprocess.run(plan.auth_argv, env=base_env(plan), stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE if harness == "pi" else subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        return f"auth check could not run: {type(exc).__name__}"
    logger.info("auth_check harness=%s exit=%s", harness, out.returncode)
    if out.returncode == 0:
        return None
    if harness == "pi":
        try:
            info = json.loads(out.stdout.strip().splitlines()[-1])
            return f"{info.get('status')}: {info.get('reason')}"
        except (ValueError, IndexError):
            pass
    return f"auth check exit={out.returncode}"


def write_exclusive(path, content, mode=0o600):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
        stream.write(content)


def summarize(ctx_info, status, exit_code, usage, started, error, paths, plan_effort=None):
    summary = dict(ctx_info)
    summary.update({
        "status": status, "exit": exit_code,
        "final_text_path": str(paths["last.md"]) if paths and paths["last.md"].exists() else None,
        "events_path": str(paths["events.jsonl"]) if paths and paths["events.jsonl"].exists() else None,
        "stderr_path": str(paths["err.txt"]) if paths and paths["err.txt"].exists() else None,
        "usage": usage, "duration_s": round(time.monotonic() - started, 1), "error": error})
    if plan_effort and plan_effort != ctx_info["effort"]:
        summary["effort_applied"] = plan_effort
    return summary


def finish(summary, paths):
    if paths is not None:
        try:
            write_exclusive(paths["summary.json"], json.dumps(summary, ensure_ascii=False) + "\n")
        except OSError:
            pass
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return EXIT_BY_STATUS.get(summary["status"], 1)


def kill_group(proc, grace=10):
    """Stop the whole process group, including descendants that ignore SIGTERM."""
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        pass
    time.sleep(1)
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        pass


def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--harness", required=True, choices=HARNESSES)
    p.add_argument("--model", required=True, help="provider/model, e.g. openai-codex/gpt-6-luna")
    p.add_argument("--effort", required=True, choices=EFFORTS)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--prompt-file")
    src.add_argument("--prompt")
    p.add_argument("--cwd", required=True)
    p.add_argument("--work-dir", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--read-only", action="store_true")
    p.add_argument("--minimal-context", action="store_true")
    p.add_argument("--dsh-patch", action="append", default=[])
    p.add_argument("--timeout", type=int, default=3600)
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args(argv)


def validate(args):
    if not RUN_ID_RE.match(args.run_id):
        raise InvocationError("run-id must match [A-Za-z0-9._-]+")
    if not MODEL_RE.match(args.model):
        raise InvocationError("model must be provider/model")
    provider = args.model.split("/", 1)[0]
    if provider == "openai" and args.harness != "opencode":
        raise InvocationError("provider openai is pay-per-use API; use openai-codex for the "
                              "Codex subscription")
    for label, value in (("cwd", args.cwd), ("work-dir", args.work_dir)):
        if not os.path.isabs(value):
            raise InvocationError(f"{label} must be an absolute path")
    if not os.path.isdir(args.cwd):
        raise InvocationError("cwd must be an existing directory")
    if args.timeout <= 0:
        raise InvocationError("timeout must be positive")
    if args.dsh_patch and args.harness != "dsh":
        raise InvocationError("--dsh-patch applies only to --harness dsh")
    for patch in args.dsh_patch:
        if not os.path.isfile(patch):
            raise InvocationError(f"dsh patch not found: {patch}")
    if args.prompt_file is not None and not os.path.isfile(args.prompt_file):
        raise InvocationError("prompt-file must be an existing file")
    if shutil.which({"dsh": "npx"}.get(args.harness, args.harness)) is None:
        raise InvocationError(f"{args.harness} command not found in PATH")


def main(argv=None):
    started = time.monotonic()
    args = parse_args(argv)
    info = {"harness": args.harness, "model": args.model, "effort": args.effort,
            "run_id": args.run_id, "cwd": args.cwd}
    paths = None
    work_dir = Path(os.path.abspath(args.work_dir))
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    try:
        validate(args)
        ctx = Ctx(args, work_dir)
        plan = BUILDERS[args.harness](ctx)
        if args.dry_run:
            print(json.dumps({
                **info, "argv": plan.argv, "cwd": str(plan.cwd),
                "env_set": sorted(plan.env_set), "env_unset": plan.env_unset,
                "stdin": str(ctx.paths["prompt.md"]) if plan.use_stdin else None,
                "files": [str(p) for p in plan.files], "dirs": [str(d) for d in plan.dirs],
                "auth_check": plan.auth_argv, "auth_env_required": plan.auth_env_missing,
                "effort_applied": plan.effort_applied or args.effort,
                "artifacts": {k: str(v) for k, v in ctx.paths.items()}}, ensure_ascii=False))
            return 0
        known = [*ctx.paths.values(), *plan.files, *plan.dirs]
        if any(p.exists() for p in known):
            raise InvocationError("artifacts for this run-id already exist")
        work_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        paths = ctx.paths
    except InvocationError as exc:
        return finish(summarize(info, "invocation_error", None, _new_usage(), started,
                                str(exc), None), None)
    logger.addHandler(_file_handler(paths["run.log"]))
    prompt = Path(args.prompt_file).read_text(encoding="utf-8") if args.prompt_file else args.prompt
    write_exclusive(paths["prompt.md"], PROMPT_PREFIX + prompt)
    for directory in plan.dirs:
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    for path, content in plan.files.items():
        write_exclusive(path, content)
    logger.info("start run_id=%s harness=%s model=%s effort=%s read_only=%s minimal=%s cwd=%s timeout_s=%d",
                args.run_id, args.harness, args.model, args.effort, args.read_only,
                args.minimal_context, quote(args.cwd, safe="/._-"), args.timeout)
    reason = preflight_auth(plan, args.harness)
    if reason:
        logger.warning("auth_not_ready run_id=%s reason=%s", args.run_id, reason)
        return finish(summarize(info, "auth_not_ready", None, _new_usage(), started,
                                reason, paths), paths)
    stdin = open(paths["prompt.md"], "rb") if plan.use_stdin else subprocess.DEVNULL
    status, exit_code, error = "failed", None, None
    with open(paths["events.jsonl"], "wb") as out, open(paths["err.txt"], "wb") as err:
        try:
            proc = subprocess.Popen(plan.argv, cwd=plan.cwd, env=base_env(plan), stdin=stdin,
                                    stdout=out, stderr=err, start_new_session=True)
        except OSError as exc:
            logger.error("spawn_failed run_id=%s error=%s", args.run_id, type(exc).__name__)
            return finish(summarize(info, "invocation_error", None, _new_usage(), started,
                                    f"spawn failed: {exc.strerror}", paths), paths)
        try:
            exit_code = proc.wait(timeout=args.timeout)
            try:  # descendants left behind by the agent
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        except subprocess.TimeoutExpired:
            kill_group(proc)
            status, exit_code, error = "timeout", 124, f"timeout after {args.timeout}s"
            logger.error("timeout run_id=%s timeout_s=%d", args.run_id, args.timeout)
    if stdin is not subprocess.DEVNULL:
        stdin.close()
    parsed = PARSERS[args.harness](read_events(paths["events.jsonl"]))
    if parsed["text"]:
        write_exclusive(paths["last.md"], parsed["text"])
    if status != "timeout":
        err_text = paths["err.txt"].read_text(encoding="utf-8", errors="replace")
        if parsed["ok"] and exit_code == 0:
            status = "completed"
        else:
            error = parsed["error"] or f"exit={exit_code}"
            if parsed["auth_error"] or any(m in err_text for m in STDERR_AUTH_MARKERS):
                status = "auth_not_ready"
    u = parsed["usage"]
    logger.info("done run_id=%s status=%s exit=%s requests=%d input_uncached=%d cache_read=%d "
                "output=%d elapsed_s=%.1f", args.run_id, status, exit_code, u["requests"],
                u["input_uncached"], u["cache_read"], u["output"], time.monotonic() - started)
    return finish(summarize(info, status, exit_code, u, started, error, paths,
                            plan.effort_applied), paths)


def _file_handler(path):
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    return handler


if __name__ == "__main__":
    sys.exit(main())
