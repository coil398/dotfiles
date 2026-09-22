"""Bounded reader for Codex rollout transcripts (``transcript_path`` of Stop).

The normal path reads only the tail of the file (``max_bytes``). If that window
is truncated before the current turn marker or the latest user-history boundary,
a reverse chunk scan recovers the marker, recent user messages, and a bounded
set of current-turn records. Oversized lines are skipped. The reader reports
what it could and could not find so policy can distinguish "not done" from
"not recorded".

Observed shapes (Codex 0.153.x / 0.154 alpha, one JSON object per line):

* ``{"type":"event_msg","payload":{"type":"task_started","turn_id":...}}``
* ``{"type":"turn_context","payload":{"turn_id":...}}``
* ``{"type":"response_item","payload":{"type":"message","role":"user"|"assistant"|"developer","content":[{"type":"input_text"|"output_text","text":...}]}}``
* ``{"type":"response_item","payload":{"type":"function_call","name":...,"arguments":"...","call_id":...}}`` /
  ``function_call_output`` (``output`` string)
* ``{"type":"response_item","payload":{"type":"custom_tool_call","name":"exec","input":"<js>","call_id":...}}`` /
  ``custom_tool_call_output`` (``output`` list of ``input_text``)
* ``{"type":"response_item","payload":{"type":"local_shell_call","action":{"command":[...]},"call_id":...}}``
* ``{"type":"event_msg","payload":{"type":"patch_apply_end","call_id":...,"success":bool,"changes":{path:{...}}}}``
* ``{"type":"event_msg","payload":{"type":"turn_aborted","turn_id":...}}``
* ``{"type":"compacted","payload":{"replacement_history":[...response items...]}}``

Stop-hook continuation prompts are recorded as ``role: user`` messages whose
text is ``<hook_prompt hook_run_id="...">...</hook_prompt>``.
"""

from __future__ import annotations

import json
import os
import subprocess
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HOOK_PROMPT_PREFIX = "<hook_prompt"
IDE_REQUEST_MARKER = "## My request:"
_SYSTEM_PREFIXES = ("# AGENTS.md instructions",)
_WRAPPER_TAG = re.compile(r"\A\s*<([A-Za-z_][^<>/]*?)\s*>")
_EXEC_CMD = re.compile(r'\bcmd\s*:\s*"((?:[^"\\]|\\.)*)"')
_EXIT_CODE = re.compile(r'"exit_code"\s*:\s*(-?\d+)')
_SHELL_TOOL_NAMES = {"exec_command", "shell", "shell_command", "local_shell", "container.exec", "exec"}
_RECOVERY_CHUNK_BYTES = 64_000
_RECOVERY_MAX_LINE_BYTES = 32_000
_RECOVERY_MAX_CURRENT_RECORDS = 64


@dataclass
class UserMessage:
    text: str
    in_current_turn: bool
    from_compaction: bool = False


@dataclass
class ToolRecord:
    kind: str  # shell | patch | tool
    summary: str
    ok: Optional[bool] = None
    failure_head: str = ""
    call_id: Optional[str] = None
    after_last_continuation: bool = False
    files: List[str] = field(default_factory=list)


@dataclass
class TurnContext:
    turn_id: str
    found_turn_start: bool = False
    window_truncated: bool = False
    user_messages: List[UserMessage] = field(default_factory=list)
    assistant_messages_in_turn: int = 0
    last_assistant_text: Optional[str] = None
    tool_records: List[ToolRecord] = field(default_factory=list)
    files_changed: List[str] = field(default_factory=list)
    hook_prompts_in_turn: int = 0
    turn_aborted: bool = False
    user_message_after_last_assistant: bool = False
    parse_errors: int = 0
    total_lines: int = 0
    compaction_seen: bool = False

    @property
    def records_since_last_continuation(self) -> int:
        if self.hook_prompts_in_turn == 0:
            return len(self.tool_records)
        return sum(1 for r in self.tool_records if r.after_last_continuation)

    @property
    def failed_tool_records(self) -> int:
        return sum(1 for r in self.tool_records if r.ok is False)


class TranscriptError(Exception):
    pass


def read_tail_lines(path: Path, max_bytes: int) -> Tuple[List[str], bool]:
    size = path.stat().st_size
    truncated = size > max_bytes
    with path.open("rb") as fh:
        if truncated:
            fh.seek(size - max_bytes)
        data = fh.read()
    text = data.decode("utf-8", errors="replace")
    lines = text.split("\n")
    if truncated and lines:
        lines = lines[1:]  # drop the partial first line
    return [ln for ln in lines if ln.strip()], truncated


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: List[str] = []
    for item in content:
        if isinstance(item, dict):
            txt = item.get("text")
            if isinstance(txt, str):
                parts.append(txt)
    return "\n".join(parts)


def classify_user_text(text: str) -> Tuple[str, Optional[str]]:
    """Return ``(kind, cleaned_text)``; kind is ``user``, ``hook_prompt`` or ``system``."""
    stripped = text.strip()
    if not stripped:
        return "system", None
    if stripped.startswith(HOOK_PROMPT_PREFIX) or stripped.startswith("[jev-stop-guard]"):
        return "hook_prompt", None
    if stripped.startswith(_SYSTEM_PREFIXES):
        return "system", None
    if IDE_REQUEST_MARKER in stripped and stripped.startswith(("# Context from my IDE setup", "<in-app-browser-context")):
        stripped = stripped.split(IDE_REQUEST_MARKER, 1)[1].strip()
        if not stripped:
            return "system", None
        return "user", stripped
    match = _WRAPPER_TAG.match(stripped)
    if match:
        tag = match.group(1).strip()
        if stripped.endswith(f"</{tag}>") or stripped.endswith(f"</{tag.split()[0]}>"):
            return "system", None
    return "user", stripped


def _shell_summary_from_args(arguments: Any) -> Optional[str]:
    data = arguments
    if isinstance(arguments, str):
        try:
            data = json.loads(arguments)
        except ValueError:
            return None
    if not isinstance(data, dict):
        return None
    for key in ("cmd", "command"):
        val = data.get(key)
        if isinstance(val, list):
            return " ".join(str(v) for v in val)
        if isinstance(val, str):
            return val
    return None


def _exec_js_summary(script: str) -> Optional[str]:
    cmds = [m.group(1) for m in _EXEC_CMD.finditer(script or "")]
    if not cmds:
        return None
    # The command is a JS string literal; undo the common escapes for readability.
    cleaned = [c.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\") for c in cmds]
    return " ; ".join(cleaned)


def _ok_from_output_text(text: str) -> Optional[bool]:
    codes = [int(m.group(1)) for m in _EXIT_CODE.finditer(text)]
    if codes:
        return all(c == 0 for c in codes)
    head = text.lstrip()[:200].lower()
    if head.startswith("script failed") or head.startswith("error") or head.startswith('{"error"'):
        return False
    if head.startswith("script completed"):
        return True
    return None


def _turn_marker(obj: Dict[str, Any]) -> Optional[str]:
    """Return the turn_id if ``obj`` marks the start of a turn."""
    payload = obj.get("payload")
    if not isinstance(payload, dict):
        return None
    typ = obj.get("type")
    if typ == "turn_context" or (typ == "event_msg" and payload.get("type") == "task_started"):
        tid = payload.get("turn_id")
        return tid if isinstance(tid, str) else None
    return None


def _iter_lines_reverse(path: Path, max_line_bytes: int):
    """Yield bounded, complete JSONL lines newest-first without retaining a large tail."""
    with path.open("rb") as fh:
        position = path.stat().st_size
        carry = b""
        skipping_oversized_line = False
        while position > 0:
            next_position = max(0, position - _RECOVERY_CHUNK_BYTES)
            fh.seek(next_position)
            block = fh.read(position - next_position)
            position = next_position
            if skipping_oversized_line:
                boundary = block.rfind(b"\n")
                if boundary < 0:
                    continue
                block = block[: boundary + 1]
                skipping_oversized_line = False
            parts = (block + carry).split(b"\n")
            carry = parts[0]
            for raw in reversed(parts[1:]):
                if raw and len(raw) <= max_line_bytes:
                    yield raw.decode("utf-8", errors="replace")
            if len(carry) > max_line_bytes:
                carry = b""
                skipping_oversized_line = True
        if carry and len(carry) <= max_line_bytes:
            yield carry.decode("utf-8", errors="replace")


def _user_texts(obj: Dict[str, Any]) -> List[str]:
    payload = obj.get("payload")
    if not isinstance(payload, dict):
        return []
    messages = []
    if obj.get("type") == "response_item" and payload.get("type") == "message":
        if payload.get("role") == "user":
            messages.append(payload)
    elif obj.get("type") == "compacted":
        history = payload.get("replacement_history")
        if isinstance(history, list):
            messages.extend(
                item for item in reversed(history)
                if isinstance(item, dict) and item.get("type") == "message" and item.get("role") == "user"
            )
    texts = []
    for message in messages:
        kind, cleaned = classify_user_text(_content_text(message.get("content")))
        if kind == "user" and cleaned:
            texts.append(cleaned)
    return texts


def _recovery_record(obj: Dict[str, Any]) -> bool:
    typ = obj.get("type")
    payload = obj.get("payload")
    if typ == "response_item" and isinstance(payload, dict):
        return payload.get("type") in {
            "message", "function_call", "function_call_output", "custom_tool_call",
            "custom_tool_call_output", "local_shell_call", "local_shell_call_output",
        }
    if typ == "event_msg" and isinstance(payload, dict):
        return payload.get("type") in {"turn_aborted", "patch_apply_end"}
    return typ == "compacted"


def _recover_truncated_context(path: Path, turn_id: str, max_user_messages: int) -> TurnContext:
    """Recover recent user history and bounded current-turn evidence from a long rollout."""
    latest_users: List[Tuple[int, str]] = []
    post_marker_candidates: List[Tuple[int, str]] = []
    current_records: List[Tuple[int, str]] = []
    pending_records: List[Tuple[int, str]] = []
    marker_entry: Optional[Tuple[int, str]] = None
    found_marker = False
    boundary_found = False
    current_aborted = False
    post_marker_aborted = False
    pending_aborted = False
    last_user_text: Optional[str] = None
    recovered_parse_errors = 0

    for reverse_index, line in enumerate(_iter_lines_reverse(path, _RECOVERY_MAX_LINE_BYTES)):
        try:
            obj = json.loads(line)
        except ValueError:
            recovered_parse_errors += 1
            continue
        if not isinstance(obj, dict):
            recovered_parse_errors += 1
            continue

        for text in _user_texts(obj):
            if text == last_user_text:
                continue
            last_user_text = text
            if len(latest_users) < max_user_messages:
                latest_users.append((reverse_index, line))

        marker = _turn_marker(obj)
        if not found_marker:
            if marker == turn_id:
                found_marker = True
                marker_entry = (reverse_index, line)
                current_records = post_marker_candidates
                pending_records = []
                current_aborted = post_marker_aborted
                pending_aborted = False
            elif _recovery_record(obj) and len(post_marker_candidates) < _RECOVERY_MAX_CURRENT_RECORDS:
                # These records become current-turn records if the marker is found.
                post_marker_candidates.append((reverse_index, line))
        elif not boundary_found:
            if marker == turn_id:
                marker_entry = (reverse_index, line)
                for entry in pending_records:
                    if len(current_records) < _RECOVERY_MAX_CURRENT_RECORDS:
                        current_records.append(entry)
                pending_records = []
                current_aborted = current_aborted or pending_aborted
                pending_aborted = False
            elif marker is not None:
                boundary_found = True
                pending_records = []
                pending_aborted = False
            elif _recovery_record(obj) and len(pending_records) < _RECOVERY_MAX_CURRENT_RECORDS:
                pending_records.append((reverse_index, line))

        payload = obj.get("payload")
        if isinstance(payload, dict) and obj.get("type") == "event_msg":
            if payload.get("type") == "turn_aborted" and payload.get("turn_id") == turn_id:
                if found_marker and not boundary_found:
                    pending_aborted = True
                elif not found_marker:
                    post_marker_aborted = True

        if found_marker and boundary_found and len(latest_users) >= max_user_messages:
            break

    selected = current_records + ([marker_entry] if marker_entry is not None else []) + latest_users
    unique: Dict[int, str] = {}
    for entry in selected:
        unique[entry[0]] = entry[1]
    lines = [line for _, line in sorted(unique.items(), reverse=True)]
    ctx = parse_lines(lines, turn_id, max_user_messages)
    ctx.window_truncated = True
    ctx.parse_errors += recovered_parse_errors
    ctx.turn_aborted = current_aborted if found_marker else post_marker_aborted
    if not found_marker:
        # Without the marker, tools in the tail cannot be scoped to this turn.
        ctx.tool_records = []
        ctx.files_changed = []
    return ctx


def find_turn_start(objs: List[Dict[str, Any]], turn_id: str) -> Tuple[int, bool]:
    """Index from which lines belong to ``turn_id`` and whether it was found.

    If the marker is missing, the window is either entirely inside a long turn
    (no markers at all) or the latest marked turn is the one that is stopping.
    """
    last_other = -1
    for idx, obj in enumerate(objs):
        marker = _turn_marker(obj)
        if marker is None:
            continue
        if marker == turn_id:
            return idx, True
        last_other = idx
    return (last_other + 1 if last_other >= 0 else 0), False


class _Parser:
    def __init__(self, turn_id: str, start_index: int, found_turn_start: bool) -> None:
        self.ctx = TurnContext(turn_id=turn_id, found_turn_start=found_turn_start)
        self.start_index = start_index
        self.in_turn = False
        self.saw_hook_prompt_in_turn = False
        self._by_call_id: Dict[str, ToolRecord] = {}
        self._last_assistant_index = -1
        self._last_user_index = -1
        self._index = 0
        self._all_user: List[UserMessage] = []

    # -- helpers -----------------------------------------------------
    def _add_record(self, rec: ToolRecord) -> None:
        if not self.in_turn:
            return
        rec.after_last_continuation = self.saw_hook_prompt_in_turn
        self.ctx.tool_records.append(rec)
        if rec.call_id:
            self._by_call_id[rec.call_id] = rec
        for f in rec.files:
            if f not in self.ctx.files_changed:
                self.ctx.files_changed.append(f)

    # -- entry points ------------------------------------------------
    def feed(self, obj: Dict[str, Any]) -> None:
        if self._index >= self.start_index:
            self.in_turn = True
        self._index += 1
        typ = obj.get("type")
        payload = obj.get("payload")
        if not isinstance(payload, dict):
            return
        if typ == "event_msg":
            self._event(payload)
        elif typ == "response_item":
            self._response_item(payload, from_compaction=False)
        elif typ == "compacted":
            self.ctx.compaction_seen = True
            history = payload.get("replacement_history")
            if isinstance(history, list):
                for item in history:
                    if isinstance(item, dict) and item.get("type") == "message":
                        self._response_item(item, from_compaction=True)

    def _event(self, p: Dict[str, Any]) -> None:
        et = p.get("type")
        if et == "turn_aborted":
            if p.get("turn_id") == self.ctx.turn_id:
                self.ctx.turn_aborted = True
        elif et == "patch_apply_end":
            changes = p.get("changes")
            files = sorted(changes.keys()) if isinstance(changes, dict) else []
            ok = p.get("success") if isinstance(p.get("success"), bool) else None
            call_id = p.get("call_id") if isinstance(p.get("call_id"), str) else None
            existing = self._by_call_id.get(call_id) if call_id else None
            if existing is not None:
                existing.kind = "patch"
                existing.ok = ok if ok is not None else existing.ok
                for f in files:
                    if f not in existing.files:
                        existing.files.append(f)
                    if self.in_turn and f not in self.ctx.files_changed:
                        self.ctx.files_changed.append(f)
                return
            summary = "apply_patch: " + ", ".join(files) if files else "apply_patch"
            self._add_record(ToolRecord(kind="patch", summary=summary, ok=ok, call_id=call_id, files=files))

    def _response_item(self, p: Dict[str, Any], from_compaction: bool) -> None:
        pt = p.get("type")
        if pt == "message":
            self._message(p, from_compaction)
            return
        if from_compaction:
            return
        call_id = p.get("call_id") if isinstance(p.get("call_id"), str) else None
        if pt == "function_call":
            name = str(p.get("name") or "tool")
            cmd = _shell_summary_from_args(p.get("arguments")) if name in _SHELL_TOOL_NAMES else None
            if cmd:
                self._add_record(ToolRecord(kind="shell", summary=cmd, call_id=call_id))
            else:
                args = p.get("arguments")
                args_s = args if isinstance(args, str) else json.dumps(args, ensure_ascii=False) if args is not None else ""
                self._add_record(ToolRecord(kind="tool", summary=f"{name}({args_s[:160]})", call_id=call_id))
        elif pt == "custom_tool_call":
            name = str(p.get("name") or "tool")
            script = p.get("input") if isinstance(p.get("input"), str) else ""
            cmd = _exec_js_summary(script) if name == "exec" else None
            if cmd:
                self._add_record(ToolRecord(kind="shell", summary=cmd, call_id=call_id))
            else:
                self._add_record(ToolRecord(kind="tool", summary=f"{name}({script[:160]})", call_id=call_id))
        elif pt == "local_shell_call":
            action = p.get("action") if isinstance(p.get("action"), dict) else {}
            cmd = action.get("command")
            summary = " ".join(str(c) for c in cmd) if isinstance(cmd, list) else str(cmd or "shell")
            self._add_record(ToolRecord(kind="shell", summary=summary, call_id=call_id))
        elif pt in ("function_call_output", "custom_tool_call_output", "local_shell_call_output"):
            rec = self._by_call_id.get(call_id) if call_id else None
            if rec is None:
                return
            out = p.get("output")
            text = _content_text(out) if not isinstance(out, str) else out
            ok = _ok_from_output_text(text)
            if rec.ok is None or ok is False:
                rec.ok = ok
            if rec.ok is False and not rec.failure_head:
                rec.failure_head = text.strip()[:200]

    def _message(self, p: Dict[str, Any], from_compaction: bool) -> None:
        role = p.get("role")
        text = _content_text(p.get("content"))
        if role == "assistant":
            if self.in_turn and not from_compaction:
                self.ctx.assistant_messages_in_turn += 1
                self.ctx.last_assistant_text = text
                self._last_assistant_index = self._index
            return
        if role != "user":
            return
        kind, cleaned = classify_user_text(text)
        if kind == "hook_prompt":
            if self.in_turn and not from_compaction:
                self.ctx.hook_prompts_in_turn += 1
                self.saw_hook_prompt_in_turn = True
            return
        if kind != "user" or cleaned is None:
            return
        msg = UserMessage(text=cleaned, in_current_turn=self.in_turn and not from_compaction, from_compaction=from_compaction)
        # Dedupe identical consecutive texts (event echoes / compaction replay).
        if self._all_user and self._all_user[-1].text == cleaned:
            return
        self._all_user.append(msg)
        if self.in_turn and not from_compaction:
            self._last_user_index = self._index

    def finish(self, max_user_messages: int) -> TurnContext:
        ctx = self.ctx
        ctx.user_messages = self._all_user[-max_user_messages:]
        ctx.user_message_after_last_assistant = (
            self._last_assistant_index >= 0 and self._last_user_index > self._last_assistant_index
        )
        return ctx


def _cursor_part_text(part: Any) -> str:
    if not isinstance(part, dict):
        return ""
    if part.get("type") in ("text", "input_text", "output_text") and isinstance(part.get("text"), str):
        return part["text"]
    return ""


def parse_cursor_lines(lines: List[str], turn_id: str, max_user_messages: int = 4) -> TurnContext:
    """Cursor agent-transcript JSONL: ``{"role","message":{"content":[...]}}``."""
    ctx = TurnContext(turn_id=turn_id, found_turn_start=False)
    users: List[UserMessage] = []
    last_user_i = -1
    last_asst_i = -1
    parse_errors = 0
    idx = 0
    for line in lines:
        try:
            obj = json.loads(line)
        except ValueError:
            parse_errors += 1
            continue
        if not isinstance(obj, dict):
            parse_errors += 1
            continue
        role = obj.get("role")
        msg = obj.get("message") if isinstance(obj.get("message"), dict) else {}
        parts = msg.get("content") if isinstance(msg.get("content"), list) else []
        texts: List[str] = []
        for part in parts:
            if not isinstance(part, dict):
                continue
            text = _cursor_part_text(part)
            if text:
                texts.append(text)
            ptype = part.get("type")
            if ptype in ("tool_use", "tool_call"):
                name = str(part.get("name") or part.get("toolName") or "tool")
                raw = part.get("input") or part.get("arguments") or {}
                summary = name
                if isinstance(raw, dict):
                    cmd = raw.get("command") or raw.get("cmd")
                    if cmd:
                        summary = f"{name} {cmd}"[:160]
                ctx.tool_records.append(ToolRecord(kind="tool", summary=summary, after_last_continuation=ctx.hook_prompts_in_turn > 0))
            elif ptype in ("tool_result", "tool_result"):
                ok = part.get("is_error") is not True
                if ctx.tool_records and ctx.tool_records[-1].ok is None:
                    ctx.tool_records[-1].ok = ok
                    if ok is False:
                        ctx.tool_records[-1].failure_head = _cursor_part_text(part)[:200]
        body = "\n".join(texts).strip()
        if role == "assistant":
            ctx.assistant_messages_in_turn += 1
            if body:
                ctx.last_assistant_text = body
            last_asst_i = idx
        elif role == "user" and body:
            kind, cleaned = classify_user_text(body)
            if kind == "hook_prompt":
                ctx.hook_prompts_in_turn += 1
            elif kind == "user" and cleaned:
                if not users or users[-1].text != cleaned:
                    users.append(UserMessage(text=cleaned, in_current_turn=True))
                    last_user_i = idx
        idx += 1
    ctx.user_messages = users[-max_user_messages:]
    ctx.parse_errors = parse_errors
    ctx.total_lines = len(lines)
    ctx.user_message_after_last_assistant = last_asst_i >= 0 and last_user_i > last_asst_i
    return ctx


def parse_lines(lines: List[str], turn_id: str, max_user_messages: int = 4) -> TurnContext:
    objs: List[Dict[str, Any]] = []
    parse_errors = 0
    for line in lines:
        try:
            obj = json.loads(line)
        except ValueError:
            parse_errors += 1
            continue
        if isinstance(obj, dict):
            objs.append(obj)
        else:
            parse_errors += 1
    start, found = find_turn_start(objs, turn_id)
    parser = _Parser(turn_id, start, found)
    for obj in objs:
        parser.feed(obj)
    parser.ctx.parse_errors = parse_errors
    parser.ctx.total_lines = len(lines)
    return parser.finish(max_user_messages)


def load_turn_context(path: Optional[str], turn_id: str, max_bytes: int, max_user_messages: int = 4) -> TurnContext:
    if not path:
        raise TranscriptError("transcript_path missing")
    p = Path(path)
    try:
        lines, truncated = read_tail_lines(p, max_bytes)
    except OSError as exc:
        raise TranscriptError(f"transcript unreadable: {exc.__class__.__name__}") from exc
    sniff = None
    for line in lines:
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict):
            sniff = obj
            break
    if sniff is not None and "role" in sniff and "message" in sniff and "type" not in sniff:
        ctx = parse_cursor_lines(lines, turn_id, max_user_messages)
    else:
        ctx = parse_lines(lines, turn_id, max_user_messages)
        if truncated and (not ctx.found_turn_start or len(ctx.user_messages) < max_user_messages):
            try:
                ctx = _recover_truncated_context(p, turn_id, max_user_messages)
            except OSError as exc:
                raise TranscriptError(f"transcript unreadable: {exc.__class__.__name__}") from exc
    ctx.window_truncated = truncated
    return ctx


def resolve_codex_transcript(path, session_id, environ=None):
    """Recover only an unambiguous rollout belonging to this session."""
    env=os.environ if environ is None else environ
    if path:
        if re.match(r"^[A-Za-z]:[\\/]",path) and env.get("WSL_DISTRO_NAME"):
            try: return subprocess.check_output(["wslpath","-u",path],text=True,timeout=1).strip()
            except (OSError,subprocess.SubprocessError) as exc: raise TranscriptError("Windows path conversion failed") from exc
        return path
    if not re.fullmatch(r"[A-Za-z0-9-]+",session_id): raise TranscriptError("transcript_path missing; invalid session id")
    home=Path(env.get("CODEX_HOME") or str(Path(env.get("HOME") or Path.home()) / ".codex"))
    matches=[]
    for candidate in (home/"sessions").glob(f"*/*/*/rollout-*-{session_id}.jsonl"):
        try:
            with candidate.open(encoding="utf-8") as stream: meta=json.loads(stream.readline(65536))
            if meta.get("type")=="session_meta" and meta.get("payload",{}).get("id")==session_id: matches.append(candidate)
        except (OSError,ValueError): continue
    if len(matches)!=1: raise TranscriptError(f"transcript_path missing; matching sessions={len(matches)}")
    return str(matches[0])
