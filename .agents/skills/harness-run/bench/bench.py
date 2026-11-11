#!/usr/bin/env python3
"""harness-run と codex-run の実装委譲ベンチ。標準ライブラリのみ。

構成 (--config) は harness:model:effort[:flag,flag] 形式。
  harness: codex (codex-run.py ベースライン) | pi | omp | opencode | dsh
  flag:    minimal (--minimal-context) / dsh-patch=PATH (--dsh-patch PATH)
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import statistics
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parent.parent
RUNNER = SKILLS / "harness-run" / "scripts" / "harness-run.py"
CODEX_RUNNER = SKILLS / "codex" / "scripts" / "codex-run.py"
FIXTURES = HERE / "fixtures"
TEST_CMD = ["uv", "run", "-q", "--no-project", "--with", "pytest", "python", "-m", "pytest", "-q"]
HARNESSES = ("codex", "pi", "omp", "opencode", "dsh")
IGNORE_LINES = "__pycache__/\n.pytest_cache/\n*.pyc\n"
SKIP_STATUSES = ("auth_not_ready", "runner_missing")

# task名 -> 変更を許す path prefix。テストは変更禁止として別途検査する。
TASKS = {
    "inventory": {"allowed": ("inventory.py",), "tests": ("test_inventory.py",)},
    "ledger": {"allowed": ("ledger/",), "tests": ("tests/",)},
}


def slug(text):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-")


def parse_config(spec):
    parts = spec.split(":")
    if len(parts) < 3 or len(parts) > 4 or parts[0] not in HARNESSES:
        raise SystemExit(f"invalid --config {spec!r}: harness:model:effort[:flags], harness in {HARNESSES}")
    flags = [f for f in (parts[3].split(",") if len(parts) == 4 else []) if f]
    for flag in flags:
        if flag != "minimal" and not flag.startswith("dsh-patch="):
            raise SystemExit(f"unknown flag {flag!r} in {spec!r}")
    return {"spec": spec, "harness": parts[0], "model": parts[1], "effort": parts[2], "flags": flags}


def run(cmd, cwd, timeout, env=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)


def run_group(cmd, cwd, timeout, grace=45):
    """run() と同じだが、timeout時にprocess group全体を止める。

    runnerは子harnessを別のprocess groupで起動するため、SIGKILLでは子が残る。
    先にSIGTERMを送り、runnerに子のgroupを止めさせてから、残りをSIGKILLする。
    """
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            start_new_session=True)
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except BaseException:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            proc.communicate(timeout=grace)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.communicate()
        raise
    return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)


def stop_codex(work_dir, run_id):
    """codex-run が detach した supervisor と helper を止める(codex-run に timeout 引数が無いため)。"""
    pids = []
    prefix = work_dir / f"codex-{run_id}-"
    for name, pattern in (("run.log", r"worker_pid=(\d+)"), ("pid", r"(\d+)")):
        try:
            pids += [int(x) for x in re.findall(pattern, Path(f"{prefix}{name}").read_text(errors="replace"))]
        except OSError:
            pass
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid in set(pids):
            for kill in (os.killpg, os.kill):
                try:
                    kill(pid, sig)
                    break
                except (ProcessLookupError, PermissionError):
                    continue
        time.sleep(3)


def git(ws, *args):
    return subprocess.run(
        ["git", "-c", "user.name=bench", "-c", "user.email=bench@localhost", *args],
        cwd=ws, capture_output=True, text=True, check=True,
    ).stdout


def prepare_workspace(task, ws):
    src = FIXTURES / task
    shutil.copytree(src, ws, ignore=shutil.ignore_patterns("task.md", "__pycache__", ".pytest_cache", ".git"))
    (ws / ".gitignore").write_text(IGNORE_LINES, encoding="utf-8")
    git(ws, "init", "-q")
    git(ws, "add", ".")
    git(ws, "commit", "-q", "-m", "baseline")
    return git(ws, "rev-parse", "HEAD").strip()


def check_diff(task, ws, baseline):
    """baseline commit からの変更(担当のcommit含む)とuntrackedを検出する。"""
    spec = TASKS[task]
    changed = sorted(set(git(ws, "-c", "core.quotepath=off", "diff", "--name-only", baseline).splitlines()
                         + git(ws, "-c", "core.quotepath=off", "ls-files", "--others",
                               "--exclude-standard").splitlines()))
    tampered = [p for p in changed if any(p.startswith(t) for t in spec["tests"])]
    outside = [p for p in changed if p not in tampered and not any(p.startswith(a) for a in spec["allowed"])]
    return changed, tampered, outside


def normalize_codex(summary, wall):
    usage = summary.get("usage") or {}

    def num(key):
        value = usage.get(key)
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    total = num("input_tokens")
    cached = num("cached_input_tokens")
    requests = None
    events_path = (summary.get("events") or {}).get("path")
    if events_path and Path(events_path).exists():
        count = 0
        for line in Path(events_path).read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                if json.loads(line).get("method") == "thread/tokenUsage/updated":
                    count += 1
            except json.JSONDecodeError:
                continue
        requests = count or None
    if requests is None:
        calls = (summary.get("run") or {}).get("model_call_count")
        requests = calls if isinstance(calls, int) else None
    done = summary.get("done") or {}
    status = "completed" if summary.get("wait_status") == "completed" and done.get("exit") == 0 else None
    if status is None:
        status = {"invocation_error": "invocation_error", "timeout": "timeout", "timed_out": "timeout"}.get(summary.get("wait_status"), "failed")
    return {
        "status": status,
        "error": summary.get("error"),
        "requests": requests,
        "total_input": total,
        "cache_read": cached,
        "cache_write": None,
        "input_uncached": total - cached if total is not None and cached is not None else None,
        "output": num("output_tokens"),
        "reasoning": None,
        "duration_s": wall,
    }


def normalize_runner(summary, wall):
    usage = summary.get("usage") or {}

    def num(key):
        value = usage.get(key)
        return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None

    total = num("total_input")
    uncached, cache_read, cache_write = num("input_uncached"), num("cache_read"), num("cache_write")
    if total is None and uncached is not None:
        total = uncached + (cache_read or 0) + (cache_write or 0)
    return {
        "status": summary.get("status", "failed"),
        "error": summary.get("error"),
        "requests": num("requests"),
        "total_input": total,
        "cache_read": cache_read,
        "cache_write": cache_write,
        "input_uncached": uncached,
        "output": num("output"),
        "reasoning": num("reasoning"),
        "duration_s": wall,
    }


def last_json(stdout):
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None


def invoke(cfg, prompt_file, ws, work_dir, run_id, timeout):
    work_dir.mkdir(parents=True, exist_ok=True)
    if cfg["harness"] == "codex":
        runner = CODEX_RUNNER
        cmd = [sys.executable, str(runner), "--prompt-file", str(prompt_file), "--cwd", str(ws),
               "--model", cfg["model"], "--effort", cfg["effort"], "--work-dir", str(work_dir), "--run-id", run_id]
    else:
        runner = RUNNER
        cmd = [sys.executable, str(runner), "--harness", cfg["harness"], "--model", cfg["model"],
               "--effort", cfg["effort"], "--prompt-file", str(prompt_file), "--cwd", str(ws),
               "--work-dir", str(work_dir), "--run-id", run_id, "--timeout", str(timeout)]
        for flag in cfg["flags"]:
            if flag == "minimal":
                cmd.append("--minimal-context")
            elif flag.startswith("dsh-patch="):
                cmd += ["--dsh-patch", str(Path(flag.split("=", 1)[1]).resolve())]
    if not runner.exists():
        return {"status": "runner_missing", "error": f"{runner} not found"}, None
    start = time.monotonic()
    try:
        proc = run_group(cmd, ws, timeout + 180)
    except subprocess.TimeoutExpired:
        if cfg["harness"] == "codex":
            stop_codex(work_dir, run_id)
        return {"status": "timeout", "error": "bench outer timeout", "duration_s": time.monotonic() - start}, None
    wall = time.monotonic() - start
    summary = last_json(proc.stdout)
    if summary is None:
        return {"status": "failed", "error": f"no summary JSON (exit {proc.returncode}): {proc.stderr[-300:]}",
                "duration_s": wall}, None
    norm = normalize_codex(summary, wall) if cfg["harness"] == "codex" else normalize_runner(summary, wall)
    return norm, summary


def run_tests(ws):
    try:
        proc = run(TEST_CMD, ws, 600)
    except subprocess.TimeoutExpired:
        return False, "test timeout"
    tail = (proc.stdout + proc.stderr).strip().splitlines()
    return proc.returncode == 0, (tail[-1] if tail else "")


def run_trial(cfg, cfg_idx, task, n, out, timeout):
    trial = f"{task}-c{cfg_idx}-{n}"
    tdir = out / "trials" / trial
    ws = tdir / "ws"
    tdir.mkdir(parents=True)
    baseline = prepare_workspace(task, ws)
    prompt_file = tdir / "task.md"
    shutil.copyfile(FIXTURES / task / "task.md", prompt_file)
    run_id = slug(f"bench-{out.name}-{trial}")[:120]
    norm, summary = invoke(cfg, prompt_file, ws, tdir / "work", run_id, timeout)
    record = {"config": cfg["spec"], "task": task, "trial": n, "trial_dir": str(tdir), **norm}
    if norm["status"] in SKIP_STATUSES or norm["status"] == "invocation_error":
        record.update(skipped=norm["status"] in SKIP_STATUSES, tests_pass=None, tampered=[], outside=[], changed=[], success=False)
        return record
    changed, tampered, outside = check_diff(task, ws, baseline)
    passed, tail = run_tests(ws)
    record.update(
        skipped=False, tests_pass=passed, test_tail=tail, changed=changed, tampered=tampered, outside=outside,
        success=bool(norm["status"] == "completed" and passed and not tampered and not outside),
    )
    return record


def med(values):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None


def fmt(value, digits=0):
    if value is None:
        return "-"
    return f"{value:,.{digits}f}"


def write_summary(records, configs, tasks, out):
    lines = ["# bench summary", "",
             "入力は total_input (非cache + cache read + cache write) に正規化。Codexの input_tokens は cached 込みなのでそのまま total_input。",
             "cache率 = cache_read / total_input。reasoningは output に含まれる。中央値は skipped を除く試行で算出。", "",
             "| 構成 | 課題 | 成功 | skipped | 時間(s) | req | 入力/req | 総入力 | uncached | cache率 | 出力 |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for cfg in configs:
        for task in tasks:
            rs = [r for r in records if r["config"] == cfg["spec"] and r["task"] == task]
            if not rs:
                continue
            skipped = [r for r in rs if r["skipped"]]
            ran = [r for r in rs if not r["skipped"]]
            ok = sum(1 for r in ran if r["success"])
            per_req = [r["total_input"] / r["requests"] for r in ran if r.get("total_input") is not None and r.get("requests")]
            cache = [r["cache_read"] / r["total_input"] for r in ran if r.get("cache_read") is not None and r.get("total_input")]
            if ran:
                succ = f"{ok}/{len(ran)}"
            else:
                succ = "skipped"
            reasons = sorted({r["status"] for r in skipped})
            lines.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
                cfg["spec"], task, succ, f"{len(skipped)} ({','.join(reasons)})" if skipped else "0",
                fmt(med([r.get("duration_s") for r in ran]), 1), fmt(med([r.get("requests") for r in ran])),
                fmt(med(per_req)), fmt(med([r.get("total_input") for r in ran])),
                fmt(med([r.get("input_uncached") for r in ran])),
                f"{med(cache) * 100:.0f}%" if med(cache) is not None else "-",
                fmt(med([r.get("output") for r in ran]))))
    problems = [r for r in records if not r["skipped"] and not r["success"]]
    if problems:
        lines += ["", "## 失敗した試行", ""]
        for r in problems:
            reason = []
            if r["status"] != "completed":
                reason.append(f"status={r['status']}")
            if r.get("tests_pass") is False:
                reason.append("tests failed")
            if r.get("tampered"):
                reason.append(f"tests modified: {r['tampered']}")
            if r.get("outside"):
                reason.append(f"outside changes: {r['outside']}")
            if r.get("error"):
                reason.append(f"error: {str(r['error'])[:200]}")
            lines.append(f"- {r['config']} / {r['task']} #{r['trial']}: {'; '.join(reason)} ({r['trial_dir']})")
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", action="append", required=True, help="harness:model:effort[:flags] (複数指定可)")
    parser.add_argument("--tasks", default=",".join(TASKS), help="カンマ区切り (既定: 全課題)")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=900, help="試行ごとのrunner timeout秒")
    args = parser.parse_args()

    configs = [parse_config(c) for c in args.config]
    tasks = [t for t in args.tasks.split(",") if t]
    for task in tasks:
        if task not in TASKS:
            raise SystemExit(f"unknown task {task!r}; choose from {list(TASKS)}")
    out = args.out.resolve()
    if (out / "results.jsonl").exists():
        raise SystemExit(f"{out}/results.jsonl already exists; use a new --out")
    out.mkdir(parents=True, exist_ok=True)

    records = []
    with open(out / "results.jsonl", "w", encoding="utf-8") as results:
        for task in tasks:
            for n in range(1, args.repeat + 1):
                for idx, cfg in enumerate(configs):
                    record = run_trial(cfg, idx, task, n, out, args.timeout)
                    records.append(record)
                    results.write(json.dumps(record, ensure_ascii=False) + "\n")
                    results.flush()
                    print(f"[{cfg['spec']}] {task} #{n}: status={record['status']} success={record['success']}"
                          f" skipped={record['skipped']}", file=sys.stderr, flush=True)
    write_summary(records, configs, tasks, out)
    print(out / "summary.md")


if __name__ == "__main__":
    main()
