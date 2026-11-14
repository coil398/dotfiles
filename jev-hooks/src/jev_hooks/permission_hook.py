"""Shared fixed-policy evaluator for runtime permission hooks.

Order: fixed risky patterns deny without a request, a narrow routine set
allows, Jev may allow the rest only with ``allow_routine`` at or above the
confidence threshold, and everything else denies with a message that tells
the agent to skip the operation and report it. Every path, including errors,
emits a decision; no ``updatedInput`` or ``updatedPermissions`` is returned.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional

from . import guards, logbook
from .config import Config, load_config, resolve_api_key
logger = logging.getLogger(__name__)

POLICY_ID = "guard_permission"
EVENT = "PermissionRequest"
_MAX_STDIN = 2_000_000

DENY_TEMPLATE = (
    "この操作は自動判定で許可されなかったため実行しない（理由: {code}）。"
    "この操作はスキップし、残りの作業を続け、最終報告にスキップした操作（ツール・対象・理由）を列挙すること。"
    "同じ操作を別の書き方で再試行しないこと。"
)

PERMISSION_QUESTION = guards._question(
    "A coding agent is about to run the proposed tool call and the runtime would otherwise ask the user for permission. "
    "Nobody is watching, so decide now. Allow only routine work: reversible, local to the workspace or a temporary directory, "
    "within the user's evident request, and with no production, credential, outward-facing, or destructive effect. "
    "When the effect is unclear, choose deny_risky.",
    {
        "allow_routine": "Routine, reversible, local work within the user's evident request.",
        "deny_risky": "Destructive, irreversible, production, credential access, outward-facing, out of scope, or unclear.",
    },
)

_ALLOW_TOOLS = {"Read", "Grep", "Glob", "LS", "WebSearch", "WebFetch", "ToolSearch", "TodoWrite", "TaskList", "TaskGet"}
_EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
_DENY_TOOLS = {"Artifact"}

_RISKY_COMMAND = [
    (re.compile(r"(?:^|[\s;&|(])rm\s+(?:-[a-zA-Z]*[rRf]|--recursive|--force)"), "DESTRUCTIVE_DELETE"),
    (re.compile(r"(?:^|[\s;&|(])(?:rmdir|shred|truncate|mkfs[.\w]*|dd)\s"), "DESTRUCTIVE_DELETE"),
    (re.compile(r"\bfind\b.*\s-(?:delete|exec|execdir|ok|okdir)\b"), "FIND_EXEC_OR_DELETE"),
    (re.compile(r"\bfd\b.*\s(?:-x|-X|--exec|--exec-batch)\b"), "FIND_EXEC_OR_DELETE"),
    (re.compile(r"\brg\b.*\s--pre\b"), "RG_PRE"),
    (re.compile(r"\bgit\s+push\b.*(?:\s--force\S*|\s-f\b|\s\+\S)"), "FORCE_PUSH"),
    (re.compile(r"\bgit\s+(?:reset\s+--hard|restore\b|clean\b|rebase\b|filter-\w+|checkout\s+(?:\S+\s+)?--\s)"), "GIT_HISTORY_OR_DISCARD"),
    (re.compile(r"\bgit\s+branch\s+.*-D\b|\bgit\s+stash\s+(?:drop|clear)\b"), "GIT_HISTORY_OR_DISCARD"),
    (re.compile(r"(?:^|[\s;&|(])(?:sudo|su|doas)\s"), "PRIVILEGE"),
    (re.compile(r"\bchmod\s+-R\b|(?:^|[\s;&|(])chown\s"), "PRIVILEGE"),
    (re.compile(r"(?:^|[\s;&|(])(?:kill|pkill|killall)\s"), "PROCESS_KILL"),
    (re.compile(r"\blaunchctl\s+(?!print\b|list\b|getenv\b)\w"), "SYSTEM_SERVICE"),
    (re.compile(r"\b(?:curl|wget)\b[^|]*\|\s*(?:ba|z)?sh\b"), "REMOTE_SCRIPT"),
    (re.compile(r"(?i)(?:^|[^a-z0-9])(?:prod|production)(?:[^a-z0-9]|$)"), "PRODUCTION"),
    (re.compile(r"(?i)\b(?:drop|delete|truncate|alter|update|insert|grant|revoke)\s+(?:table|database|from|into|index|on|\w+\s+set)\b"), "SQL_WRITE"),
    (re.compile(r"(?i)\b(?:deploy|npm\s+publish|gh\s+release\s+create|gh\s+pr\s+merge|terraform\s+(?:apply|destroy)|kubectl\s+(?:apply|delete|scale|rollout))\b"), "DEPLOY_OR_PUBLISH"),
    (re.compile(r"(?i)(?:\.ssh/|\.aws/|\.gnupg/|\.config/gh/|zsh_secret|id_rsa|\.pem\b|\.p12\b)"), "CREDENTIALS"),
    (re.compile(r"(?:^|[\s;&|(])(?:printenv|env)\s*(?:$|[;&|])"), "CREDENTIALS"),
]
_SECRET_WORD = re.compile(r"(?i)(?:secret|credential|token|passw(?:or)?d|private[_-]?key)")
_CREDENTIAL_PATH = re.compile(r"(?i)(?:/\.ssh/|/\.aws/|/\.gnupg/|/\.config/gh/|zsh_secret|(?:^|[/\\])id_rsa(?:$|[/\\])|\.(?:pem|p12|pfx|key)(?:$|[/\\]))")
_OUTWARD_MCP = re.compile(
    r"(?i)(?:send|post|create|update|delete|remove|merge|share|upload|trash|publish|deploy|stop|archive|cancel|move|restore|write|set|add|edit|complete|schedule|run|spawn|convert|duplicate|rename|reply|react)"
)
_READ_MCP = re.compile(r"(?i)(?:read|get|list|search|fetch|query|view|resolve|whoami|status|download|export|screenshot|metadata|context|find)")


def _decision(behavior: str, code: str = "", runtime: str = "claude") -> Dict[str, Any]:
    message = DENY_TEMPLATE.format(code=code or "UNKNOWN") if behavior == "deny" else ""
    if runtime == "cursor":
        result: Dict[str, Any] = {"permission": behavior}
        if message:
            result["user_message"] = message
            result["agent_message"] = message
        return result
    if runtime == "devin":
        result = {"decision": "approve" if behavior == "allow" else "block"}
        if message:
            result["reason"] = message
        return result
    if runtime == "opencode":
        result = {"effect": behavior}
        if message:
            result["message"] = message
        return result
    if runtime == "antigravity":
        return {"decision": "auto_approve" if behavior == "allow" else "deny", **({"reason": message} if message else {})}
    if runtime == "grok":
        result = {"decision": behavior}
        if message:
            result["reason"] = message
        return result
    decision: Dict[str, Any] = {"behavior": behavior}
    if behavior == "deny":
        decision["message"] = DENY_TEMPLATE.format(code=code or "UNKNOWN")
    return {"hookSpecificOutput": {"hookEventName": EVENT, "decision": decision}}


def _command_text(tool_input: Any) -> str:
    if isinstance(tool_input, Mapping):
        value = tool_input.get("command") or tool_input.get("cmd") or tool_input.get("CommandLine")
        if isinstance(value, (list, tuple)):
            return " ".join(str(part) for part in value)
        return value if isinstance(value, str) else ""
    return tool_input if isinstance(tool_input, str) else ""


def _edit_path(tool_input: Any) -> str:
    if not isinstance(tool_input, Mapping):
        return ""
    for key in ("file_path", "filePath", "FilePath", "AbsolutePath", "TargetFile", "notebook_path", "notebookPath", "path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _path_decision(raw: str, cwd: Any) -> str:
    if not raw:
        return "NO_TARGET_PATH"
    if guards._SECRET_PATH_RE.search(" " + raw) or _CREDENTIAL_PATH.search("/" + raw.lstrip("~/")) or _SECRET_WORD.search(Path(raw).name):
        return "CREDENTIALS"
    try:
        expanded = Path(os.path.expanduser(raw))
        if not expanded.is_absolute():
            if not isinstance(cwd, str) or not cwd:
                return "NO_CWD"
            expanded = Path(cwd) / expanded
        target = expanded.resolve()
    except (OSError, RuntimeError, ValueError):
        return "UNRESOLVABLE_PATH"
    if guards._SECRET_PATH_RE.search(" " + str(target)) or _CREDENTIAL_PATH.search(str(target)) or _SECRET_WORD.search(target.name):
        return "CREDENTIALS"
    roots = []
    if isinstance(cwd, str) and cwd:
        try:
            roots.append(Path(cwd).resolve())
        except (OSError, RuntimeError, ValueError):
            pass
    for tmp in ("/tmp", "/private/tmp", os.environ.get("TMPDIR") or ""):
        if tmp:
            try:
                roots.append(Path(tmp).resolve())
            except (OSError, RuntimeError, ValueError):
                pass
    if any(_inside(target, root) for root in roots):
        return "allow"
    if not _inside(target, Path.home().resolve()):
        return "OUTSIDE_HOME"
    return "JEV"


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _edit_decision(tool_input: Any, cwd: Any) -> Optional[str]:
    """Return ``"allow"`` or a deny code for edits; ``None`` defers to Jev."""
    decision = _path_decision(_edit_path(tool_input), cwd)
    return None if decision == "JEV" else decision


def _read_path_decision(tool_input: Any, cwd: Any) -> Optional[str]:
    if not isinstance(tool_input, Mapping):
        return None
    values = []
    for key in ("file_path", "filePath", "FilePath", "AbsolutePath", "TargetFile", "DirectoryPath", "SearchDirectory", "SearchPath", "path", "target", "notebook_path", "notebookPath"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            values.append(value)
    if not values:
        return None
    decisions = [_path_decision(value, cwd) for value in values]
    for unsafe in ("CREDENTIALS", "OUTSIDE_HOME", "NO_CWD", "UNRESOLVABLE_PATH"):
        if unsafe in decisions:
            return unsafe
    return None


def _command_references_secret(tool_input: Any, cwd: Any) -> bool:
    serialized = guards._safe_json(tool_input, 2_000)
    if guards._SECRET_PATH_RE.search(" " + serialized) or _CREDENTIAL_PATH.search(serialized):
        return True
    for segment in guards._command_segments(tool_input):
        for token in segment[1:]:
            if token.startswith("-") or "=" in token:
                continue
            try:
                target = Path(os.path.expanduser(token))
                if not target.is_absolute():
                    if not isinstance(cwd, str) or not cwd:
                        continue
                    target = Path(cwd) / target
                canonical = target.resolve()
            except (OSError, RuntimeError, ValueError):
                continue
            if guards._SECRET_PATH_RE.search(" " + str(canonical)) or _CREDENTIAL_PATH.search(str(canonical)) or _SECRET_WORD.search(canonical.name):
                return True
    return False


def _risky_input(tool_input: Any) -> Optional[str]:
    text = guards._safe_json(tool_input, 2_000)
    for pattern, code in _RISKY_COMMAND:
        if pattern.search(text):
            return code
    return None


def _patch_decision(tool_input: Any, cwd: Any) -> str:
    command = _command_text(tool_input)
    if not command or "*** Begin Patch" not in command or "*** End Patch" not in command:
        return "INVALID_PATCH"
    paths = []
    for line in command.splitlines():
        match = re.match(r"\*\*\* (?:Update|Add|Delete) File: (.+?)\s*$", line)
        if match:
            if line.startswith("*** Delete File:"):
                return "DESTRUCTIVE_DELETE"
            paths.append(match.group(1))
        move = re.match(r"\*\*\* Move to: (.+?)\s*$", line)
        if move:
            paths.append(move.group(1))
    if not paths:
        return "NO_TARGET_PATH"
    decisions = [_path_decision(path, cwd) for path in paths]
    if any(result != "allow" for result in decisions):
        if "CREDENTIALS" in decisions:
            return "CREDENTIALS"
        if "OUTSIDE_HOME" in decisions:
            return "OUTSIDE_HOME"
        if "NO_CWD" in decisions:
            return "NO_CWD"
        if "UNRESOLVABLE_PATH" in decisions:
            return "UNRESOLVABLE_PATH"
        return "JEV"
    return "allow"


def _fixed_decision(tool_name: str, tool_input: Any, payload: Mapping[str, Any], runtime: str = "claude") -> Optional[str]:
    """Return ``"allow"``, a deny code, or ``None`` when Jev should decide."""
    if tool_name in _DENY_TOOLS:
        return "ARTIFACT"
    if tool_name in _ALLOW_TOOLS:
        if tool_name in {"Read", "Grep", "Glob", "LS"}:
            if _command_references_secret(tool_input, payload.get("cwd")):
                return "CREDENTIALS"
            path_decision = _read_path_decision(tool_input, payload.get("cwd"))
            if path_decision:
                return path_decision
        return "allow"
    if tool_name in _EDIT_TOOLS:
        return _edit_decision(tool_input, payload.get("cwd"))
    if tool_name == "apply_patch":
        decision = _patch_decision(tool_input, payload.get("cwd"))
        return None if decision == "JEV" else decision
    if tool_name == "Bash" or tool_name == "Monitor":
        command = _command_text(tool_input)
        if not command.strip():
            return "EMPTY_COMMAND"
        for pattern, code in _RISKY_COMMAND:
            if pattern.search(command):
                return code
        if _command_references_secret(tool_input, payload.get("cwd")):
            return "CREDENTIALS"
        if guards._is_read_only_command(tool_input):
            return "allow"
        segments = guards._command_segments(tool_input)
        has_redirection = any(token and all(char in "<>" for char in token) for segment in segments for token in segment)
        if segments and all(guards._is_test_invocation(tokens) for tokens in segments) and not any(marker in command for marker in ("$(", "`")) and not has_redirection:
            return "allow"
        return None
    if tool_name.startswith("mcp__"):
        action = tool_name.rsplit("__", 1)[-1]
        risky = _risky_input(tool_input)
        if risky:
            return risky
        if _OUTWARD_MCP.search(action):
            return "OUTWARD_FACING"
        if action.casefold() == "query":
            return None
        if _READ_MCP.search(action):
            if _command_references_secret(tool_input, payload.get("cwd")):
                return "CREDENTIALS"
            path_decision = _read_path_decision(tool_input, payload.get("cwd"))
            if path_decision:
                return path_decision
            return "allow"
        return None
    return None


def _ask_jev(tool_name: str, tool_input: Any, payload: Mapping[str, Any], cfg: Config, environ: Optional[Dict[str, str]], evaluate: Callable[..., Any], runtime: str) -> str:
    if cfg.mode != "on":
        return "JEV_MODE_" + cfg.mode.upper()
    if not resolve_api_key(environ)[0]:
        return "NO_API_KEY"
    state = {
        "_note": guards._DATA_NOTE,
        "runtime": runtime,
        "proposed_tool": tool_name,
        "mcp_server": guards._safe_text(payload.get("mcp_server") or "", 100),
        "proposed_input": guards._safe_json(tool_input, 2_000),
        "cwd": guards._safe_text(payload.get("cwd") or "", 300),
        "permission_mode": guards._safe_text(payload.get("permission_mode") or "", 40),
        "request_context": guards._request_context(payload, cfg, runtime),
    }
    questions = {"permission": PERMISSION_QUESTION}
    evaluation = evaluate(POLICY_ID, state, questions, cfg=cfg, environ=environ, runtime=runtime, event=EVENT, payload=payload, key_prechecked=True)
    if evaluation is None:
        return "JEV_UNAVAILABLE"
    choice = guards._answer_choice(evaluation, "permission", cfg)
    if choice == "allow_routine":
        return "allow"
    if choice == "deny_risky":
        return "JEV_DENY_RISKY"
    return "JEV_LOW_CONFIDENCE"


def _normalize(payload: Mapping[str, Any], runtime: str) -> tuple[str, Any]:
    name = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    if runtime == "cursor":
        if name == "Shell":
            name = "Bash"
        elif name == "MCP" or (isinstance(name, str) and name.startswith("MCP:")):
            native_tool_name = name
            action = name.split(":", 1)[1] if isinstance(name, str) and ":" in name else "unknown"
            server = payload.get("mcp_server_name")
            if isinstance(tool_input, str):
                try:
                    parsed = json.loads(tool_input)
                    tool_input = parsed
                except (TypeError, ValueError):
                    pass
            if isinstance(tool_input, Mapping):
                server = server or tool_input.get("server_name") or tool_input.get("server")
                if native_tool_name == "MCP":
                    action = tool_input.get("tool_name") or tool_input.get("name") or action
            server = server or "unknown"
            name = f"mcp__{server}__{action}"
    elif runtime == "devin":
        name = {
            "exec": "Bash", "shell": "Bash", "run_command": "Bash",
            "edit": "Edit", "write": "Write", "apply_patch": "apply_patch",
            "read": "Read", "grep": "Grep", "glob": "Glob",
            "notebook_read": "Read", "notebook_edit": "NotebookEdit",
            "ask_user_question": "AskUserQuestion", "run_subagent": "Task",
            "read_subagent": "Task", "todo_write": "TodoWrite",
        }.get(name, name)
    elif runtime == "opencode":
        name = {
            "shell": "Bash", "edit": "Edit", "write": "Write", "apply_patch": "apply_patch",
            "read": "Read", "grep": "Grep", "glob": "Glob", "webfetch": "WebFetch",
            "websearch": "WebSearch", "question": "AskUserQuestion", "task": "Task",
            "subagent": "Task", "external_directory": "ExternalDirectory",
        }.get(name, name)
    elif runtime == "grok":
        name = payload.get("toolName", name)
        tool_input = payload.get("toolInput", tool_input)
        if name in {"shell", "run_command", "exec", "run_terminal_command"}:
            name = "Bash"
        elif name in {"read_file", "read_text_file"}:
            name = "Read"
        elif name in {"write_file", "edit_file"}:
            name = "Write"
    elif runtime == "antigravity":
        call = payload.get("toolCall")
        if isinstance(call, Mapping):
            name = call.get("name")
            tool_input = call.get("args")
        if name in {"run_command", "shell", "exec"}:
            name = "Bash"
        elif name in {"view_file", "read_file", "read_text_file"}:
            name = "Read"
        elif name in {"write_to_file", "replace_file_content", "multi_replace_file_content", "write_file", "edit_file"}:
            name = "Write"
        elif name == "list_dir":
            name = "LS"
        elif name == "find_by_name":
            name = "Glob"
        elif name == "grep_search":
            name = "Grep"
        elif name == "search_web":
            name = "WebSearch"
        elif name == "read_url_content":
            name = "WebFetch"
        if isinstance(tool_input, Mapping):
            normalized_input = dict(tool_input)
            if "CommandLine" in normalized_input and "command" not in normalized_input:
                normalized_input["command"] = normalized_input["CommandLine"]
            for native_key in ("Path", "FilePath", "AbsolutePath", "TargetFile", "DirectoryPath", "SearchDirectory", "SearchPath"):
                if native_key in normalized_input:
                    normalized_input.setdefault("file_path", normalized_input[native_key])
            tool_input = normalized_input
    return (name if isinstance(name, str) else ""), tool_input


def decide(payload: Any, environ: Optional[Dict[str, str]] = None, evaluate: Optional[Callable[..., Any]] = None, runtime: str = "claude") -> Dict[str, Any]:
    """Return a documented PermissionRequest decision for any payload."""
    cfg: Optional[Config] = None
    tool_name = ""
    tool_input: Any = None
    try:
        if not isinstance(payload, Mapping) or not payload:
            return _finish(_decision("deny", "INVALID_INPUT", runtime), "INVALID_INPUT", "", None, {}, None, runtime)
        cfg = load_config(environ)
        tool_name, tool_input = _normalize(payload, runtime)
        if runtime == "antigravity" and not payload.get("cwd") and isinstance(tool_input, Mapping):
            cwd = tool_input.get("Cwd") or tool_input.get("cwd")
            if isinstance(cwd, str) and cwd:
                payload = dict(payload, cwd=cwd)
        if runtime == "antigravity" and not payload.get("cwd") and isinstance(payload.get("workspacePaths"), list):
            roots = [root for root in payload["workspacePaths"] if isinstance(root, str) and root]
            if len(roots) == 1:
                payload = dict(payload, cwd=roots[0])
        if not tool_name:
            return _finish(_decision("deny", "NO_TOOL_NAME", runtime), "NO_TOOL_NAME", "", None, payload, cfg, runtime)
        verdict = _fixed_decision(tool_name, tool_input, payload, runtime)
        source = "fixed"
        if verdict is None:
            source = "jev"
            verdict = _ask_jev(tool_name, tool_input, payload, cfg, environ, evaluate or guards._evaluate_questions, runtime)
        if verdict == "allow":
            return _finish(_decision("allow", runtime=runtime), f"{source}:allow", tool_name, tool_input, payload, cfg, runtime)
        return _finish(_decision("deny", verdict, runtime), f"{source}:{verdict}", tool_name, tool_input, payload, cfg, runtime)
    except Exception as exc:  # every failure still answers the prompt
        return _finish(_decision("deny", "HOOK_ERROR", runtime), f"error:{type(exc).__name__}", tool_name, tool_input, payload if isinstance(payload, Mapping) else {}, cfg, runtime)


def _finish(output: Dict[str, Any], reason: str, tool_name: str, tool_input: Any, payload: Mapping[str, Any], cfg: Optional[Config], runtime: str) -> Dict[str, Any]:
    try:
        config = cfg or load_config()
        if runtime in {"claude", "codex"}:
            action = output["hookSpecificOutput"]["decision"]["behavior"]
        elif runtime == "cursor":
            action = output.get("permission", "deny")
        elif runtime == "devin":
            action = "allow" if output.get("decision") == "approve" else "deny"
        elif runtime == "opencode":
            action = output.get("effect", "deny")
        elif runtime == "antigravity":
            action = "allow" if output.get("decision") == "auto_approve" else "deny"
        elif runtime == "grok":
            action = output.get("decision", "deny")
        else:
            action = "deny"
        record = {
            "ts": logbook.now_iso(),
            "policy": POLICY_ID,
            "event": EVENT,
            "runtime": runtime,
            "action": action,
            "reason_code": reason,
            "tool": tool_name[:120],
            "session_id": str(payload.get("session_id") or "")[:80],
        }
        cwd = payload.get("cwd") if isinstance(payload.get("cwd"), str) else None
        if not logbook.append(config.state_path(), record, config.log_max_bytes, cwd=cwd):
            logger.warning("permission_decision_log_failed runtime=%s error=write_failed", runtime)
    except Exception as exc:
        logger.warning("permission_decision_log_failed runtime=%s error=%s", runtime, type(exc).__name__)
    return output


def run_hook(stdin: Any, stdout: Any, environ: Optional[Dict[str, str]] = None, evaluate: Optional[Callable[..., Any]] = None, runtime: str = "claude") -> int:
    try:
        raw = stdin.read(_MAX_STDIN + 1)
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        payload = json.loads(raw) if len(raw) <= _MAX_STDIN and raw.strip() else {}
    except Exception:
        payload = {}
    output = decide(payload, environ=environ, evaluate=evaluate, runtime=runtime)
    try:
        stdout.write(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
        stdout.flush()
    except Exception:
        pass
    return 0


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s %(message)s", stream=sys.stderr)
    return run_hook(sys.stdin, sys.stdout)
