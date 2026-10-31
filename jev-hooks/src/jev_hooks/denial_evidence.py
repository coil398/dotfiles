"""Evidence for an auto mode denial, as structured JSON plus a short summary.

Input is a Claude Code ``PermissionDenied`` hook payload (``tool_name``,
``tool_input``, ``reason``, ``cwd``, ``transcript_path``). The output lists the
denied operation, the matched rule, the user's recent requests, repository
facts, documented operating rules that mention the operation, the target
environment and impact signals. It only reads local files and runs read-only
``git`` queries; it never calls an API, retries the operation or answers the
classifier. Wiring it into a hook or a report is left to the caller.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from .config import load_config
from .redact import scrub
from .transcript import TranscriptError, claude_prompt_id, load_turn_context

OPERATION_CHARS = 400
REQUEST_CHARS = 300
RULE_LINE_CHARS = 240
MAX_REQUESTS = 3
MAX_RULE_HITS = 20
MAX_KEYWORDS = 10
GIT_TIMEOUT_S = 2.0

NO_VERDICT_PREFIX = "Auto mode could not evaluate this action"
UNAVAILABLE = "Classifier unavailable"

# Documents that state how a repository is operated, relative to its root.
RULE_DOCS = (
    "README.md", "README", "README.ja.md", "CLAUDE.md", "AGENTS.md", "CONTRIBUTING.md",
    ".claude/CLAUDE.md", ".github/CONTRIBUTING.md", "docs/CONTRIBUTING.md",
)

_STOPWORDS = {
    "the", "and", "for", "with", "from", "into", "that", "this", "bash", "sudo", "true", "false",
    "null", "echo", "printf", "cat", "head", "tail", "grep", "sed", "awk", "xargs", "env", "cd",
}

_ENVIRONMENTS = (
    ("production", re.compile(r"(?i)\b(prod|production|live|本番)\b")),
    ("staging", re.compile(r"(?i)\b(stg|staging|stage|検証環境)\b")),
    ("development", re.compile(r"(?i)\b(dev|develop|development|sandbox|test|qa|開発環境)\b")),
    ("local", re.compile(r"(?i)(localhost|127\.0\.0\.1|\[::1\]|\.localhost\b|\.test\b)")),
)

_IMPACT = (
    ("force_push", re.compile(r"\bgit\s+push\b.*(\s--force\b|\s-f\b|\s--force-with-lease\b|\s\+\S)")),
    ("push", re.compile(r"\bgit\s+push\b")),
    ("history_rewrite", re.compile(r"\bgit\s+(reset\s+--hard|rebase|filter-branch|filter-repo)\b")),
    ("branch_or_tag_delete", re.compile(r"\bgit\s+(branch\s+-D|push\s+\S+\s+(--delete|:))|\bgit\s+tag\s+-d\b")),
    ("file_delete", re.compile(r"(^|[\s;&|])(rm|rmdir|unlink|trash)\s")),
    ("network_send", re.compile(r"\b(curl|wget|scp|rsync|ssh|nc)\b")),
    ("package_publish", re.compile(r"\b(npm|pnpm|yarn)\s+publish\b|\btwine\s+upload\b|\bcargo\s+publish\b")),
    ("deploy", re.compile(r"(?i)\b(deploy|kubectl|helm|terraform\s+apply|gcloud|aws|fly|vercel|heroku)\b")),
    ("database", re.compile(r"(?i)\b(psql|mysql|mongo|redis-cli|DROP\s+TABLE|TRUNCATE|DELETE\s+FROM|migrate)\b")),
)


def _operation_text(tool_input: Mapping[str, Any]) -> str:
    command = tool_input.get("command")
    if isinstance(command, str):
        return command
    return json.dumps(dict(tool_input), ensure_ascii=False, default=str)


def _denial(reason: str) -> Dict[str, Any]:
    if reason.startswith(NO_VERDICT_PREFIX):
        kind = "no_verdict"
    elif reason.strip() == UNAVAILABLE:
        kind = "classifier_unavailable"
    else:
        kind = "classifier_verdict"
    rule = re.search(r"\[([^\]]{1,80})\]", reason)
    return {"kind": kind, "rule": rule.group(1) if rule else None, "reason": scrub(reason, OPERATION_CHARS)}


def _git(root: Path, *args: str) -> Optional[str]:
    try:
        done = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True, timeout=GIT_TIMEOUT_S, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    out = done.stdout.strip()
    return out if done.returncode == 0 and out else None


def _repository(cwd: Optional[Path]) -> Dict[str, Any]:
    if cwd is None or not cwd.is_dir():
        return {"root": None}
    root = _git(cwd, "rev-parse", "--show-toplevel")
    if root is None:
        return {"root": None}
    root_path = Path(root)
    default = _git(root_path, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    remote = _git(root_path, "remote", "get-url", "origin")
    return {
        "root": root,
        "branch": _git(root_path, "branch", "--show-current"),
        "default_branch": default.split("/", 1)[1] if default and "/" in default else default,
        "remote_url": scrub(remote, 200) if remote else None,
    }


def _keywords(operation: str, repo: Mapping[str, Any]) -> List[str]:
    # Program names (``git``, ``npm``) match nearly every document line; keep
    # their subcommands and arguments instead.
    programs = {m.group(1).lower() for m in re.finditer(r"(?:^|[;&|]\s*|\$\(\s*)([A-Za-z][A-Za-z0-9_.-]*)", operation)}
    words: List[str] = []
    for token in re.findall(r"[A-Za-z][A-Za-z0-9_.-]{2,}", operation):
        word = token.lower().strip(".-")
        if len(word) >= 3 and word not in _STOPWORDS and word not in programs and word not in words:
            words.append(word)
    for key in ("branch", "default_branch"):
        value = repo.get(key)
        if isinstance(value, str) and value.lower() not in words:
            words.append(value.lower())
    return words[:MAX_KEYWORDS]


def _documented_rules(root: Optional[str], keywords: List[str]) -> List[Dict[str, Any]]:
    if not root or not keywords:
        return []
    patterns = [(word, re.compile(r"(?<![A-Za-z0-9_])" + re.escape(word) + r"(?![A-Za-z0-9_])", re.I)) for word in keywords]
    hits: List[Dict[str, Any]] = []
    for rel in RULE_DOCS:
        path = Path(root) / rel
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for number, line in enumerate(lines, 1):
            matched = [word for word, pattern in patterns if pattern.search(line)]
            if matched:
                hits.append({"file": rel, "line": number, "matched": matched, "text": scrub(line.strip(), RULE_LINE_CHARS)})
    # Lines naming more parts of the operation come first; ties keep document order.
    hits.sort(key=lambda hit: -len(hit["matched"]))
    return hits[:MAX_RULE_HITS]


def _user_requests(transcript_path: Any) -> List[str]:
    if not isinstance(transcript_path, str) or not transcript_path:
        return []
    max_bytes = load_config().max_transcript_bytes
    try:
        ctx = load_turn_context(transcript_path, claude_prompt_id(transcript_path, max_bytes), max_bytes, MAX_REQUESTS)
    except TranscriptError:
        return []
    return [scrub(m.text, REQUEST_CHARS) for m in ctx.user_messages[-MAX_REQUESTS:]]


def _environment(operation: str, repo: Mapping[str, Any]) -> Dict[str, Any]:
    haystack = " ".join(str(v) for v in (operation, repo.get("branch"), repo.get("remote_url")) if v)
    signals = [name for name, pattern in _ENVIRONMENTS if pattern.search(haystack)]
    return {"target": signals[0] if signals else "unknown", "signals": signals}


def _impact(operation: str, repo: Mapping[str, Any]) -> List[str]:
    signals = [name for name, pattern in _IMPACT if pattern.search(operation)]
    if "push" in signals and repo.get("default_branch") and (
        repo.get("branch") == repo["default_branch"] or re.search(r"\b" + re.escape(repo["default_branch"]) + r"\b", operation)
    ):
        signals.append("push_to_default_branch")
    return signals


def _summary(evidence: Mapping[str, Any]) -> str:
    op = evidence["operation"]
    denial = evidence["denial"]
    repo = evidence["repository"]
    rule = denial["rule"] or denial["kind"]
    lines = [f"auto mode が {op['tool']} の操作を拒否しました（規則: {rule}）。", f"操作: {op['summary']}"]
    if repo.get("root"):
        lines.append(f"対象: {repo['root']}（ブランチ {repo.get('branch') or '不明'}、既定ブランチ {repo.get('default_branch') or '不明'}）")
    lines.append(f"環境: {evidence['environment']['target']}、影響: {', '.join(evidence['impact']) or '検出なし'}")
    rules = evidence["documented_rules"]
    if rules:
        lines.append("関連する運用の記述:")
        lines.extend(f"- {r['file']}:{r['line']} {r['text']}" for r in rules[:5])
    else:
        lines.append("運用文書に該当する記述は見つかりませんでした。")
    if evidence["user_requests"]:
        lines.append(f"直近の依頼: {evidence['user_requests'][-1]}")
    return "\n".join(lines)


def collect(payload: Mapping[str, Any]) -> Dict[str, Any]:
    tool_name = str(payload.get("tool_name") or "tool")
    raw_input = payload.get("tool_input")
    tool_input: Mapping[str, Any] = raw_input if isinstance(raw_input, dict) else {}
    operation = _operation_text(tool_input)
    cwd = payload.get("cwd")
    repo = _repository(Path(cwd) if isinstance(cwd, str) and cwd else None)
    raw_reason = payload.get("reason")
    reason = raw_reason if isinstance(raw_reason, str) else ""
    evidence: Dict[str, Any] = {
        "operation": {"tool": tool_name, "summary": scrub(operation, OPERATION_CHARS), "tool_use_id": payload.get("tool_use_id")},
        "denial": _denial(reason),
        "user_requests": _user_requests(payload.get("transcript_path")),
        "repository": repo,
        "documented_rules": _documented_rules(repo.get("root"), _keywords(operation, repo)),
        "environment": _environment(operation, repo),
        "impact": _impact(operation, repo),
    }
    evidence["summary_ja"] = _summary(evidence)
    return evidence
