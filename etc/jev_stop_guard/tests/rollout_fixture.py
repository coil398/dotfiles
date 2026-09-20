"""Builders for Codex rollout transcript lines in the observed 0.153.x format."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional

TS = "2026-09-18T06:00:00.000Z"


def _line(typ: str, payload: Dict[str, Any]) -> str:
    return json.dumps({"timestamp": TS, "type": typ, "payload": payload}, ensure_ascii=False)


def session_meta(session_id: str = "01a0b284-32dc-7680-9d07-48d771ae3ad0", cli_version: str = "0.153.4") -> str:
    return _line(
        "session_meta",
        {
            "session_id": session_id,
            "id": session_id,
            "timestamp": TS,
            "cwd": "/work/project",
            "originator": "codex-tui",
            "cli_version": cli_version,
            "source": "cli",
            "thread_source": "user",
        },
    )


def task_started(turn_id: str) -> str:
    return _line("event_msg", {"type": "task_started", "turn_id": turn_id, "started_at": 1789700000, "model_context_window": 380000})


def task_complete(turn_id: str, last: str = "") -> str:
    return _line("event_msg", {"type": "task_complete", "turn_id": turn_id, "last_agent_message": last})


def turn_context(turn_id: str) -> str:
    return _line("turn_context", {"turn_id": turn_id, "cwd": "/work/project", "model": "gpt-6-astra", "approval_policy": "on-request"})


def turn_aborted(turn_id: str) -> str:
    return _line("event_msg", {"type": "turn_aborted", "turn_id": turn_id, "reason": "interrupted"})


def user_message(text: str, ide_wrapper: bool = False) -> str:
    if ide_wrapper:
        text = "# Context from my IDE setup:\n\n## Active file: /work/project/src/a.py\n\n## My request:\n" + text + "\n"
    return _line(
        "response_item",
        {"type": "message", "id": "msg_user", "role": "user", "content": [{"type": "input_text", "text": text}]},
    )


def user_message_event(text: str) -> str:
    return _line("event_msg", {"type": "user_message", "message": text, "images": []})


def agents_md_instructions() -> str:
    return user_message("# AGENTS.md instructions for /work/project\n\n<INSTRUCTIONS>\n- rules\n</INSTRUCTIONS>")


def environment_context() -> str:
    return user_message("<environment_context>\n  <cwd>/work/project</cwd>\n  <shell>zsh</shell>\n</environment_context>")


def developer_message(text: str) -> str:
    return _line(
        "response_item",
        {"type": "message", "id": "msg_dev", "role": "developer", "content": [{"type": "input_text", "text": text}]},
    )


def hook_prompt(text: str, run_id: str = "hr_1") -> str:
    return user_message(f'<hook_prompt hook_run_id="{run_id}">{text}</hook_prompt>')


def assistant_message(text: str, turn_id: str = "t") -> str:
    return _line(
        "response_item",
        {
            "type": "message",
            "id": "msg_asst",
            "role": "assistant",
            "content": [{"type": "output_text", "text": text}],
            "phase": "final_answer",
            "internal_chat_message_metadata_passthrough": {"turn_id": turn_id},
        },
    )


def exec_custom_call(call_id: str, cmds: Iterable[str]) -> str:
    script = "".join(
        'text(await tools.exec_command({cmd:"%s","max_output_tokens":20000}));\n' % c.replace("\\", "\\\\").replace('"', '\\"')
        for c in cmds
    )
    return _line(
        "response_item",
        {"type": "custom_tool_call", "id": "ctc_x", "status": "completed", "call_id": call_id, "name": "exec", "input": script},
    )


def exec_custom_output(call_id: str, exit_code: int = 0, body: str = "ok") -> str:
    chunk = json.dumps({"chunk_id": "abc123", "wall_time_seconds": 0.01, "exit_code": exit_code, "output": body})
    return _line(
        "response_item",
        {
            "type": "custom_tool_call_output",
            "id": "ctco_x",
            "call_id": call_id,
            "output": [{"type": "input_text", "text": "Script completed\nWall time 0.3 seconds\nOutput:\n"}, {"type": "input_text", "text": chunk}],
        },
    )


def function_call(call_id: str, name: str, arguments: Dict[str, Any]) -> str:
    return _line(
        "response_item",
        {"type": "function_call", "id": "fc_x", "name": name, "arguments": json.dumps(arguments), "call_id": call_id},
    )


def function_call_output(call_id: str, output: Any) -> str:
    return _line(
        "response_item",
        {"type": "function_call_output", "id": "fco_x", "call_id": call_id, "output": output if isinstance(output, str) else json.dumps(output)},
    )


def patch_apply_end(call_id: str, files: Dict[str, str], success: bool = True, turn_id: str = "t") -> str:
    changes = {path: {"type": kind, "unified_diff": "@@ -1 +1 @@\n-a\n+b\n"} for path, kind in files.items()}
    return _line(
        "event_msg",
        {
            "type": "patch_apply_end",
            "call_id": call_id,
            "turn_id": turn_id,
            "stdout": "Success. Updated the following files:\n" + "\n".join("M " + p for p in files),
            "stderr": "",
            "success": success,
            "changes": changes,
        },
    )


def compacted(user_texts: List[str]) -> str:
    history = [
        {"type": "message", "id": "msg_c", "role": "user", "content": [{"type": "input_text", "text": t}]} for t in user_texts
    ]
    return _line("compacted", {"message": "", "replacement_history": history})


def token_count() -> str:
    return _line("event_msg", {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 1}}})


def implementation_turn(
    turn_id: str,
    request: str,
    final: str,
    *,
    tools: Optional[List[str]] = None,
    earlier: Optional[List[str]] = None,
    ide_wrapper: bool = False,
) -> List[str]:
    """A whole turn: preamble + user request + tool activity + final message."""
    lines = [session_meta()]
    lines.extend(earlier or [])
    lines.append(task_started(turn_id))
    lines.append(agents_md_instructions())
    lines.append(environment_context())
    lines.append(user_message(request, ide_wrapper=ide_wrapper))
    lines.append(turn_context(turn_id))
    lines.extend(tools or [])
    lines.append(token_count())
    lines.append(assistant_message(final, turn_id))
    return lines


def write(path: Any, lines: Iterable[str]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for ln in lines:
            fh.write(ln + "\n")
